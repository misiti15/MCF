"""COILGAP scorer (PLAN.md frozen 2026-11-11 09:30 ET). One rule: skip CWT12 coil longs when SPY gap <= -0.25%.
    python -I coilgap.py --selftest
    python -I coilgap.py <coil_tagged.csv.gz> <spy cache csv>     Educational only - not financial advice."""
import sys, os, json, urllib.request, urllib.parse
import numpy as np, pandas as pd
LK0, LK1, SPLIT, THR = "2024-11-01", "2025-02-28", "2025-09-30", -0.0025
RNG = np.random.default_rng(20261111); NDRAW = 5000

def spy_daily(cache):
    if not os.path.exists(cache):
        H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
        rows = []
        for a, b in (("2024-09-25", "2024-10-31"), ("2025-03-01", "2026-11-09")):   # locked block never fetched
            q = {"timeframe": "1Day", "start": a, "end": b, "adjustment": "raw", "feed": "sip", "limit": 10000}
            url = "https://data.alpaca.markets/v2/stocks/SPY/bars?" + urllib.parse.urlencode(q)
            rows += [dict(date=x["t"][:10], o=x["o"], c=x["c"]) for x in json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60))["bars"]]
        pd.DataFrame(rows).to_csv(cache, index=False)
    s = pd.read_csv(cache).sort_values("date").reset_index(drop=True)
    assert not ((s.date >= LK0) & (s.date <= LK1)).any()
    s["pc"] = s.c.shift(1); s["pd"] = s.date.shift(1)
    gapdays = (pd.to_datetime(s.date) - pd.to_datetime(s.pd)).dt.days
    s.loc[gapdays > 5, "pc"] = np.nan                       # first session after the locked block: no gap
    s["gap"] = s.o / s.pc - 1; s["oc"] = s.c / s.o - 1
    return s.set_index("date")

def switch_test(t, col, off_days, days_by_split):
    """kept-book total of col: rule vs shared-day random (same number of off days per split, all setups together)."""
    rule = t.loc[~t.date.isin(off_days), col].sum()
    per_day = t.groupby("date")[col].sum()
    tot = per_day.sum(); draws = np.zeros(NDRAW)
    pools = {k: np.array(v) for k, v in days_by_split.items()}
    nk = {k: len(set(off_days) & set(v)) for k, v in days_by_split.items()}
    for i in range(NDRAW):
        rm = np.concatenate([RNG.choice(pools[k], nk[k], replace=False) for k in pools if nk[k] > 0]) if sum(nk.values()) else []
        draws[i] = tot - per_day.reindex(rm).fillna(0).sum()
    sd = draws.std(ddof=1)
    return rule, draws.mean(), (rule - draws.mean()) / sd if sd > 0 else np.nan, float((draws >= rule).mean())

def selftest():
    t = pd.DataFrame(dict(date=list("aabbccdd"), x=[-1, -1, 1, 1, 1, 1, 1, 1.0]))
    r, m, z, p = switch_test(t, "x", ["a"], {"S": list("abcd")})
    assert r == 6 and abs(m - (4 - (-2 + 2 + 2 + 2) / 4)) < 0.15 and z > 0, (r, m, z)
    r, m, z, p = switch_test(t, "x", [], {"S": list("abcd")}); assert r == 4 and m == 4
    print("selftest ok: shared-day random switch")

def main():
    t = pd.read_csv(sys.argv[1]); t["date"] = t.date.astype(str)
    assert not ((t.date >= LK0) & (t.date <= LK1)).any()
    t = t[t.setup.str.startswith("CWT12-coil") & (t.side > 0)].copy()
    S = spy_daily(sys.argv[2]); miss = sorted(set(t.date) - set(S.index)); assert not miss, miss[:5]
    t["gap"] = t.date.map(S.gap)
    t["sm"] = t.side * t.spy_move.fillna(0)
    t["beta"] = 0.0
    for s, g in t.groupby("setup"):
        tr = g[g.date <= SPLIT]; t.loc[g.index, "beta"] = np.polyfit(tr.sm, tr.r, 1)[0]
    t["xr"] = t.r - t.beta * t.sm
    days = sorted(t.date.unique()); off = sorted(t[t.gap <= THR].date.unique())
    split = {"TRAIN": [d for d in days if d <= SPLIT], "VALID": [d for d in days if d > SPLIT]}
    print(f"coil long trades {len(t)} on {len(days)} days ({t.date.min()}..{t.date.max()}); setups {t.setup.value_counts().to_dict()}")
    print(f"beta per setup (TRAIN): {t.groupby('setup').beta.first().round(3).to_dict()}; gap NaN days {int(t.groupby('date').gap.first().isna().sum())}")
    rm = t.date.isin(off)
    print(f"gap-down days (<= -0.25%) with coil trades: {len(off)} (TRAIN {len(set(off)&set(split['TRAIN']))}, VALID {len(set(off)&set(split['VALID']))}); "
          f"removed trades {int(rm.sum())} ({rm.mean():.1%})")
    for nm, g in (("removed", t[rm]), ("kept", t[~rm])):
        print(f"  {nm}: n {len(g)}, avg net R {g.r.mean():+.4f}, gross {g.gross.mean():+.4f}, ex-mkt {g.xr.mean():+.4f}")
    gd = t[~rm].groupby("date").r.sum(); b = gd.idxmax(); k = t[~rm]
    print(f"  kept avg net R w/o best day ({b}): {k[k.date != b].r.mean():+.4f}; best-day share of kept total {gd.max() / gd.sum() if gd.sum() > 0 else float('nan'):.2f}")
    od = S.loc[[d for d in days if d in S.index]]
    print(f"  SPY open->close: gap-down days {od[od.gap <= THR].oc.mean():+.4%} (n {int((od.gap <= THR).sum())}), other days {od[~(od.gap <= THR)].oc.mean():+.4%}")
    print("\nSHARED-DAY RANDOM SWITCH (kept-book total R: rule vs null mean; z; p = share of null >= rule)")
    res = {}
    for scope, sub, sp in (("ALL", t, split), ("TRAIN", t[t.date <= SPLIT], {"TRAIN": split["TRAIN"]}),
                           ("VALID", t[t.date > SPLIT], {"VALID": split["VALID"]})):
        for col in ("gross", "r", "xr"):
            r, m, z, p = switch_test(sub, col, off, sp); res[(scope, col)] = z
            print(f"  {scope:5s} {col:5s}: rule {r:+9.1f}  null {m:+9.1f}  diff {r - m:+8.1f}  z {z:+.2f}  p {p:.3f}")
    harm = {}
    for s, g in t.groupby("setup"):
        r, m, z, p = switch_test(g, "xr", off, split); harm[s] = r - m
        print(f"  per setup {s}: ex-mkt diff {r - m:+.1f} (z {z:+.2f})")
    ok = (res[("ALL", "xr")] >= 2.74 and res[("TRAIN", "xr")] > 0 and res[("VALID", "xr")] > 0
          and all(v >= 0 for v in harm.values()) and t[~rm].gross.mean() > 0)
    print(f"\nPASS (lead, BAR90 2.74 on ex-mkt z, TRAIN&VALID > 0, no setup harmed, kept gross > 0): {ok}"
          f"{'' if ok else ' -> COILGAP closed'}; Testing bar 3.57: {res[('ALL', 'xr')] >= 3.57}")
    print("1 config; lineage REGSW 104. Educational only - not financial advice.")

if __name__ == "__main__":
    selftest() if sys.argv[1] == "--selftest" else main()
