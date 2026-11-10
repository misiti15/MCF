"""EVD1 descriptive (PLAN.md frozen 2026-11-10 07:40 ET). 0 configs.
    python evd1.py <earnings_yf.parquet> > evd1_out.txt        python evd1.py --selftest
Run only after Builder's gap-alignment table is posted. Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
LK0, LK1, SPLIT = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date(), pd.Timestamp("2025-09-30").date()
RNG = np.random.default_rng(20261110)


def reaction_session(report_date, timing, sessions):
    """BMO -> report date (or next session if not a session); AMC -> next session after the report date; dmh / other -> None."""
    t = str(timing).lower()
    if t not in ("bmo", "amc"): return None
    i = np.searchsorted(sessions, report_date, side="left" if t == "bmo" else "right")
    return sessions[i] if i < len(sessions) else None


def surprise_bucket(x):
    if x is None or not np.isfinite(x): return "unknown"
    return "beat" if x > 1 else ("miss" if x < -1 else "inline")


def dedupe(ev, days=45):
    ev = ev.sort_values(["symbol", "react"]); keep = []
    last = {}
    for r in ev.itertuples():
        p = last.get(r.symbol)
        if p is None or (pd.Timestamp(r.react) - pd.Timestamp(p)).days >= days: keep.append(r.Index); last[r.symbol] = r.react
    return ev.loc[keep]


def selftest():
    S = np.array(pd.to_datetime(["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-06"]).date)
    d = pd.Timestamp("2026-11-03").date()
    assert reaction_session(d, "bmo", S) == d and reaction_session(d, "amc", S) == S[2] and reaction_session(d, "dmh", S) is None
    sat = pd.Timestamp("2026-11-05").date()                                   # not a session: BMO maps to the next one
    assert reaction_session(sat, "bmo", S) == S[3] and reaction_session(S[3], "amc", S) is None
    assert surprise_bucket(5.0) == "beat" and surprise_bucket(-0.5) == "inline" and surprise_bucket(float("nan")) == "unknown"
    ev = pd.DataFrame(dict(symbol=["A", "A", "A"], react=pd.to_datetime(["2026-01-01", "2026-01-20", "2026-04-01"]).date))
    assert len(dedupe(ev)) == 2
    print("selftest ok: BMO/AMC/dmh mapping, non-session dates, surprise buckets, 45-day dedupe")


def main():
    import pyarrow.dataset as pds
    assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
    sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
    import lib
    er = pd.read_parquet(sys.argv[1]); er["date"] = pd.to_datetime(er["date"]).dt.date
    assert not ((er.date >= LK0) & (er.date <= LK1)).any(), "locked-block rows present"
    Dd = lib.daily().sort_values(["symbol", "date"]).reset_index(drop=True)
    assert not ((Dd.date >= LK0) & (Dd.date <= LK1)).any()
    pc = Dd.groupby("symbol").close.shift(1); gap5 = pd.to_datetime(Dd.date).groupby(Dd.symbol).diff().dt.days > 5
    tr = np.maximum(Dd.high - Dd.low, np.maximum((Dd.high - pc).abs(), (Dd.low - pc).abs())).mask(gap5)
    Dd["pc"] = pc.mask(gap5); Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
    Dd["ret"] = (Dd.close / pc - 1).mask(gap5); SPYD = Dd[Dd.symbol == "SPY"].set_index("date"); Dd["sr"] = Dd.date.map(SPYD.ret)
    def _b(g):
        x, y = g.sr.shift(1), g.ret.shift(1)
        cov = (x * y).rolling(60, min_periods=40).mean() - x.rolling(60, min_periods=40).mean() * y.rolling(60, min_periods=40).mean()
        return cov / x.rolling(60, min_periods=40).var(ddof=0)
    Dd["beta"] = Dd.groupby("symbol", group_keys=False).apply(_b)
    INFO = {(s, d): (p, a, adv, b) for s, d, p, a, adv, b in Dd[["symbol", "date", "pc", "atr", "adv20", "beta"]].itertuples(index=False)}
    S = np.array(sorted(SPYD.index))
    tcol = next(c for c in ("timing", "time", "report_time", "hour_class") if c in er.columns)
    er["react"] = [reaction_session(d, t, S) for d, t in zip(er.date, er[tcol])]
    n0 = len(er); ev = er[er.react.notna()].copy()
    print(f"events {n0}; dropped (dmh/other timing or no next session) {n0 - len(ev)}; weekend/non-session report dates mapped "
          f"{int((~pd.Series(er.date).isin(set(S))).sum())}")
    ev = dedupe(ev); ev["sb"] = [surprise_bucket(x) for x in ev.get("surprise_pct", pd.Series(np.nan, index=ev.index))]
    ev = ev[[(s, d) in INFO and INFO[(s, d)][2] >= 60e6 for s, d in zip(ev.symbol, ev.react)]]
    print(f"after dedupe + adv20 >= $60M: {len(ev)} events, {ev.react.nunique()} sessions; surprise buckets {ev.sb.value_counts().to_dict()}")
    TL0, TL1 = pd.Timestamp("2024-11-01", tz="America/New_York"), pd.Timestamp("2025-03-01", tz="America/New_York")
    def path(sym, dates):
        p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
        if not p.exists(): return {}
        ix = "__index_level_0__"
        df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
        if ix in df.columns: df = df.set_index(ix)
        assert not ((df.index >= TL0) & (df.index < TL1)).any()
        df = df[~df.index.duplicated(keep="last")].sort_index(); mm = df.index.hour * 60 + df.index.minute
        out = {}
        for d in dates:
            k = (df.index.date == d) & (mm >= 570) & (mm < 960)
            if not k.any(): continue
            x = df[k]; m_ = (x.index.hour * 60 + x.index.minute).to_numpy()
            def at(minute, col):                                  # first bar at/after minute (open) or last bar before (close)
                i = np.searchsorted(m_, minute)
                return float(x[col].iloc[i]) if col == "open" and i < len(x) else (float(x[col].iloc[i - 1]) if i > 0 else np.nan)
            out[d] = dict(o930=float(x.open.iloc[0]) if m_[0] == 570 else np.nan, c949=at(590, "close"), o950=at(590, "open"),
                          c1129=at(690, "close"), c1555=at(956, "close"))
        return out
    need = {}
    for s, d in zip(ev.symbol, ev.react): need.setdefault(s, set()).add(d)
    need.setdefault("SPY", set()).update(set(ev.react))
    # control pool: same-day non-event lab names (seeded 300-name pool), gap bucket matched
    evset = set(zip(ev.symbol, ev.react))
    lab = [s.strip() for s in open(ROOT / "research/lab_symbols.txt") if s.strip()]
    pool = sorted(RNG.choice([s for s in lab if s not in ("SPY", "QQQ", "IWM", "DIA")], 300, replace=False).tolist())
    for s in pool: need.setdefault(s, set()).update(set(ev.react))
    P = {}
    for k_, (s, ds) in enumerate(sorted(need.items())):
        for d, v in path(s, ds).items(): P[(s, d)] = v
        if k_ % 100 == 0: print(f"paths {k_}/{len(need)}", flush=True)
    def rec(s, d):
        v = P.get((s, d)); inf = INFO.get((s, d)); sp = P.get(("SPY", d))
        if v is None or inf is None or sp is None: return None
        p, atr, adv, b = inf
        if not (np.isfinite(p) and np.isfinite(atr) and atr > 0 and np.isfinite(v["o930"]) and np.isfinite(v["o950"])): return None
        gap = v["o930"] / p - 1; sg = np.sign(gap)
        if sg == 0: return None
        b = b if np.isfinite(b) else 1.0
        o = dict(gap=gap, sg=sg, held=bool(np.sign(v["c949"] / v["o930"] - 1) == sg))
        for h in ("c1129", "c1555"):
            g = sg * (v[h] - v["o950"]) / atr; m = (sp[h] / sp["o950"] - 1) * v["o950"] / atr
            o[f"g_{h}"] = g; o[f"x_{h}"] = g - sg * b * m
        return o
    rows = []
    for r in ev.itertuples():
        o = rec(r.symbol, r.react)
        if o is None: continue
        o.update(symbol=r.symbol, date=r.react, timing=str(getattr(r, tcol)).lower(), sb=r.sb)
        o["agree"] = ("agree" if (r.sb == "beat" and o["sg"] > 0) or (r.sb == "miss" and o["sg"] < 0) else
                      ("disagree" if r.sb in ("beat", "miss") else r.sb))
        ab = abs(o["gap"]); o["gb"] = "<2%" if ab < .02 else ("2-5%" if ab < .05 else ">5%")
        cands = [c for c in pool if (c, r.react) not in evset and (c, r.react) in P]
        RNG.shuffle(cands); ctl = None
        for c in cands:
            oc = rec(c, r.react)
            if oc is None: continue
            gb = "<2%" if abs(oc["gap"]) < .02 else ("2-5%" if abs(oc["gap"]) < .05 else ">5%")
            if gb == o["gb"]: ctl = oc; break
        for h in ("c1129", "c1555"):
            o[f"cg_{h}"] = ctl[f"g_{h}"] if ctl else np.nan; o[f"cx_{h}"] = ctl[f"x_{h}"] if ctl else np.nan
        rows.append(o)
    X = pd.DataFrame(rows); X.to_csv(HERE / "evd1_rows.csv.gz", index=False)
    for h in ("c1129", "c1555"):
        X[f"dm_{h}"] = X[f"g_{h}"] - X.groupby("date")[f"g_{h}"].transform("mean")
    def dt_(v, d):
        g = pd.Series(v.to_numpy(), index=d.to_numpy()).groupby(level=0).mean().dropna()
        return (round(float(g.mean()), 4), round(float(g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))), 2) if len(g) > 2 else np.nan, len(g))
    print(f"\nrows {len(X)} events on {X.date.nunique()} sessions; timing {X.timing.value_counts().to_dict()}; agree buckets {X.agree.value_counts().to_dict()}")
    for h, nm in (("c1129", "09:50->11:30"), ("c1555", "09:50->15:55")):
        print(f"\n== {nm} (gap-sign direction, ATR units; mean, day-t, days)")
        for split, m in (("ALL", X.date.notna()), ("TRAIN", X.date <= SPLIT), ("VALID", X.date > SPLIT)):
            for tm in ("all", "bmo", "amc"):
                Y = X[m & ((X.timing == tm) if tm != "all" else True)]
                if not len(Y): continue
                line = f"  {split:5s} {tm:3s}"
                for b in ("agree", "disagree", "inline", "unknown"):
                    Z = Y[Y.agree == b]
                    if len(Z) >= 10: line += f" | {b} n {len(Z)} gross {dt_(Z[f'g_{h}'], Z.date)[0]:+.3f} ex {dt_(Z[f'x_{h}'], Z.date)[0]:+.3f}"
                A, Dg = Y[Y.agree == "agree"], Y[Y.agree == "disagree"]
                if len(A) > 10 and len(Dg) > 10:
                    dd = A.groupby("date")[f"x_{h}"].mean().sub(Dg.groupby("date")[f"x_{h}"].mean(), fill_value=np.nan).dropna()
                    line += f" || agree-disagree ex (same-day pairs) {dd.mean():+.3f} t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):.2f} days {len(dd)}" if len(dd) > 2 else ""
                    ac = (A[f"x_{h}"] - A[f"cx_{h}"]).dropna(); dd2 = ac.groupby(A.date[ac.index]).mean()
                    line += f" | agree-minus-random-gapper ex {dd2.mean():+.3f} t {dd2.mean() / (dd2.std(ddof=1) / np.sqrt(len(dd2))):.2f}" if len(dd2) > 2 else ""
                print(line)
        print("  by |gap| x agree (ALL, gross mean):", X.groupby(["gb", "agree"])[f"g_{h}"].mean().round(3).to_dict())
        print("  held vs faded at 09:50 (ALL, agree only, gross):", X[X.agree == "agree"].groupby("held")[f"g_{h}"].mean().round(3).to_dict())
    print("\nLooks: 2 (agree-disagree, agree-random gapper) x 2 horizons, one family (N 858 + looks -> BAR90 ~3.31). Gross first;"
          "\nex = minus beta60 x SPY move; random gapper = same-day non-event name, |gap| bucket matched, own gap-sign direction.")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
