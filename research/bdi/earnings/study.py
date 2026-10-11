"""ER earnings study, part 2 (NOTES.md section 1): reaction-based families B, U, P, G on daily bars and the
after-hours family A on the 1-minute sample. One process, < 1 GB RAM.
    python research/bdi/earnings/study.py       -> trades.parquet (data/), results.csv, gates.csv, diag.csv
Educational only - not financial advice.
"""
from __future__ import annotations

import glob
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import elib as E  # noqa: E402

HERE = E.HERE
N_PART2 = 204
N_LINEAGE = N_PART2 + 60
T_REQ = math.sqrt(2 * math.log(N_LINEAGE))
Cn, On, T = E.Cn, E.On, E.T
SHORT_OK = np.array([s in E.SHORTABLE for s in E.syms])

# SPY monthly return (entry month regime)
spy = pd.Series(Cn[:, E.SPY], index=E.dates)
spy_m = spy.resample("ME").last().pct_change()
SPY_UP = {(i.year, i.month): v > 0 for i, v in spy_m.items() if np.isfinite(v)}
adv = np.where(E.ELIG, E.adv20, -np.inf)
TOP300 = E.ELIG & ((-adv).argsort(axis=1).argsort(axis=1) < 300)
del adv


# ---------------------------------------------------------------------------------------------- trade engine
def trades(ev: pd.DataFrame, side: int, entry: str, H: int, cost_mult=1.0, entry_px=None, entry_cost=None) -> pd.DataFrame:
    """ev rows with R, j. entry 'CLOSE' = C[R], 'OPEN' = O[R+1], 'AH' = entry_px (daily frame, after the close of R).
    Exit C[R+H]. Family A passes R = report day d."""
    R = ev.R.to_numpy(); j = ev.j.to_numpy()
    xr = R + H - 1 if entry == "OPENR" else R + H         # OPENR (part 3): O[R], H1 = the reaction day itself
    ok = xr < T
    if entry == "OPENR":
        er, p0 = R, On[R, j]
    elif entry == "CLOSE":
        er, p0 = R, Cn[R, j]
    elif entry == "OPEN":
        er, p0 = R + 1, On[np.minimum(R + 1, T - 1), j]
    else:                                   # AH: family A rows carry R = d (report day), entry after its close
        er, p0 = R, np.asarray(entry_px, float)
    xr_c = np.minimum(xr, T - 1)
    p1 = Cn[xr_c, j]
    ok &= np.isfinite(p0) & np.isfinite(p1) & (p0 > 0)
    if side < 0:
        ok &= SHORT_OK[j]
    r = p1 / p0 - 1
    ewk = "O" if entry in ("OPEN", "OPENR") else "C"
    ew_a = er
    ew = np.array([E.ew_ret(ewk, int(a), int(b), int(a)) if o else np.nan for a, b, o in zip(ew_a, xr_c, ok)])
    # costs per side: entry, exit
    c_in = (E.SLIP_PS / p0 + E.SLIP_BPS) if entry_cost is None else np.asarray(entry_cost, float)
    c_out = E.SLIP_PS / p1 + E.SLIP_BPS
    cost = (c_in + c_out) * cost_mult
    days = (E.dates[xr_c] - E.dates[np.minimum(er, T - 1)]).days.to_numpy()
    if side < 0:
        cost = cost + E.BORROW * np.maximum(days, 1) / 365
    out = pd.DataFrame({"symbol": ev.symbol.to_numpy(), "R": R, "entry_date": E.dates[np.minimum(er, T - 1)],
                        "split": ev.split.to_numpy(), "net_raw": side * r - cost, "net_ex": side * (r - ew) - cost})
    return out[ok & np.isfinite(out.net_ex.to_numpy())].reset_index(drop=True)


def stats(tr: pd.DataFrame) -> dict:
    o = {"n": len(tr)}
    if len(tr) < 3:
        return o
    day = tr.groupby("entry_date").net_ex.mean()
    o.update(mean=tr.net_ex.mean(), median=tr.net_ex.median(), hit=(tr.net_ex > 0).mean(), raw=tr.net_raw.mean(),
             days=len(day), t=day.mean() / day.std(ddof=1) * math.sqrt(len(day)) if len(day) > 2 else np.nan)
    for sp in ("train", "valid", "valid2"):
        x = tr[tr.split == sp].net_ex
        o[f"m_{sp}"] = x.mean() if len(x) else np.nan
        o[f"n_{sp}"] = len(x)
    best = tr.groupby("entry_date").net_ex.sum().idxmax()
    o["ex_best_day"] = tr[tr.entry_date != best].net_ex.mean()
    o["busiest_share"] = tr.groupby("entry_date").size().max() / len(tr)
    up = np.array([SPY_UP.get((d.year, d.month), True) for d in tr.entry_date])
    o["m_up"] = tr.net_ex[up].mean() if up.any() else np.nan
    o["m_down"] = tr.net_ex[~up].mean() if (~up).any() else np.nan
    mon = tr.groupby(tr.entry_date.dt.to_period("M")).net_ex.agg(["mean", "size"])
    mon = mon[mon["size"] >= 10].iloc[3:]
    o["wf_share"] = (mon["mean"] > 0).mean() if len(mon) else np.nan
    o["wf_months"] = len(mon)
    for y in range(2019, 2027):
        x = tr[tr.entry_date.dt.year == y].net_ex
        o[f"y{y}"] = x.mean() if len(x) else np.nan
    return o


# ---------------------------------------------------------------------------------------------- events
ev_all = E.events()
EV = ev_all[ev_all.elig & (ev_all.split != "none") & ~ev_all.locked_touch].reset_index(drop=True)
print("events", len(EV), EV.split.value_counts().to_dict(), flush=True)


def cond_mask(ev, fam, cond, side):
    s = side
    re = ev.REACT * s
    if fam in ("B", "A"):
        return np.ones(len(ev), bool)
    if fam == "U":
        k, dirn = cond
        x = ev[f"RUN{k}"]; th = 0.05 if k == 5 else 0.10
        return (x >= th) if dirn == "up" else (x <= -th)
    if fam == "P":
        if cond in ("SAME2", "SAME3", "SAME4"):
            k = int(cond[-1])
            return np.all([(ev[f"PREV{i}"] * s > 0) for i in range(1, k + 1)], axis=0)
        if cond == "OPP2":
            return (ev.PREV1 * s < 0) & (ev.PREV2 * s < 0)
        if cond == "BIG3":
            m = ev[["PREV1", "PREV2", "PREV3"]].abs()
            return (m.notna().all(axis=1)) & (m.mean(axis=1) >= 0.06)
        if cond == "FT3":
            m = ev[["FTPREV1", "FTPREV2", "FTPREV3"]]
            return m.notna().all(axis=1) & (m.mean(axis=1) > 0)
    if fam == "G":
        g = ev.GAP * s; i = ev.INTRA * s
        if cond == "GAPGO":
            return (g >= 0.02) & (i >= 0)
        if cond == "GAPFADE":
            return (g >= 0.02) & (i < 0)
        if cond == "INTRADAY":
            return g.abs() < 0.02
    raise ValueError((fam, cond))


CONFIGS = []
for side in (1, -1):
    for th in (0.04, 0.08):
        for en in ("CLOSE", "OPEN"):
            for H in (1, 5, 20):
                CONFIGS.append(dict(fam="B", cond=None, side=side, th=th, entry=en, H=H))
    for cond in [(5, "up"), (5, "down"), (20, "up"), (20, "down")]:
        for en in ("CLOSE", "OPEN"):
            for H in (1, 5, 20):
                CONFIGS.append(dict(fam="U", cond=cond, side=side, th=0.04, entry=en, H=H))
    for cond in ("SAME2", "SAME3", "SAME4", "OPP2", "BIG3", "FT3"):
        for en in ("CLOSE", "OPEN"):
            for H in (1, 5, 20):
                CONFIGS.append(dict(fam="P", cond=cond, side=side, th=0.04, entry=en, H=H))
    for cond in ("GAPGO", "GAPFADE", "INTRADAY"):
        for en in ("CLOSE", "OPEN"):
            for H in (1, 5, 20):
                CONFIGS.append(dict(fam="G", cond=cond, side=side, th=0.04, entry=en, H=H))
    for th in (0.04, 0.08):
        for en in ("AH", "OPEN"):
            for H in (1, 5, 20):
                CONFIGS.append(dict(fam="A", cond=None, side=side, th=th, entry=en, H=H))
assert len(CONFIGS) == N_PART2, len(CONFIGS)


def cid(c):
    cs = "" if c["cond"] is None else ("_RUN%d%s" % c["cond"] if c["fam"] == "U" else "_" + c["cond"])
    return f"{c['fam']}_{'L' if c['side'] > 0 else 'S'}_th{int(c['th'] * 100)}{cs}_{c['entry']}_H{c['H']}"


# ---------------------------------------------------------------------------------------------- after-hours sample
def load_ah():
    files = sorted(glob.glob(str(E.DATA / "ah" / "*.parquet")))
    if not files:
        return None
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    q = df[df.kind == "quote"].set_index(["day", "symbol"])["o"].rename("spread")
    b = df[df.kind == "bar"].copy()
    b["ts"] = pd.to_datetime(b.t, utc=True).dt.tz_convert("America/New_York")
    b["hm"] = b.ts.dt.hour * 100 + b.ts.dt.minute
    rows = []
    for (day, sym), g in b.groupby(["day", "symbol"]):
        g = g.sort_values("hm")
        ref = g[g.hm == 1559]
        if ref.empty:
            continue
        vol = g[(g.hm >= 1601) & (g.hm <= 1654)].v.sum()
        sig = g[(g.hm >= 1630) & (g.hm <= 1654)]
        ent = g[(g.hm >= 1650) & (g.hm <= 1655)]
        rows.append({"day": day, "symbol": sym, "p1559": ref.c.iloc[-1], "ahvol": vol,
                     "psig": sig.c.iloc[-1] if len(sig) else np.nan, "pent": ent.c.iloc[-1] if len(ent) else np.nan})
    a = pd.DataFrame(rows).set_index(["day", "symbol"])
    a = a.join(q, how="left")
    return a.reset_index()


AH = None if __import__("os").environ.get("ER_SKIP_AH") else load_ah()   # skip until the sample is complete
EVA = None
if AH is not None:
    spy_ah = AH[AH.symbol == "SPY"].set_index("day")
    spy_mv = (spy_ah.psig / spy_ah.p1559 - 1)
    ev = ev_all[ev_all.elig & (ev_all.split != "none") & ~ev_all.locked_touch].copy()
    ev["day"] = E.dates[ev.d.to_numpy()]
    ev = ev.merge(AH, on=["day", "symbol"], how="inner")
    ev["vmed"] = E.vmed20[ev.d.to_numpy() - 1, ev.j.to_numpy()]
    ev = ev[(ev.ahvol >= 0.10 * ev.vmed) & ev.psig.notna() & ev.pent.notna()].copy()
    ev["R"] = ev.d            # family A rows: R = report day d (AH entry after its close, OPEN = O[d+1], exit C[d+H])
    ev = ev[ev.R + 2 < T]
    ev["REACT"] = ev.psig / ev.p1559 - 1 - ev.day.map(spy_mv).fillna(0).to_numpy()   # AHMOVE, used as the signal
    ev["ah_px"] = Cn[ev.d.to_numpy(), ev.j.to_numpy()] * ev.pent / ev.p1559         # entry in the daily frame
    half = (ev.spread / 2).clip(lower=0.0010).fillna(0.0050)
    ev["ah_cost_half"] = half
    ev["ah_cost"] = half + E.SLIP_PS / ev.pent + E.SLIP_BPS
    EVA = ev.reset_index(drop=True)
    print("AH confirmed events", len(EVA), "dates with AH data", AH.day.nunique(), flush=True)


def run(c, cost_mult=1.0, ah_cost_mult=1.0, top300=False, fixed=None):
    if c["fam"] == "A":
        ev = EVA
        if ev is None:
            return pd.DataFrame()
    else:
        ev = EV if fixed is None else fixed
    m = (ev.REACT * c["side"] >= c["th"]) & cond_mask(ev, c["fam"], c["cond"], c["side"])
    if top300:
        m &= TOP300[ev.R.to_numpy() - 1, ev.j.to_numpy()]
    e = ev[np.asarray(m)]
    if c["entry"] == "AH":
        return trades(e, c["side"], "AH", c["H"], cost_mult, e.ah_px.to_numpy(), e.ah_cost.to_numpy() * ah_cost_mult)
    return trades(e, c["side"], c["entry"], c["H"], cost_mult)


# ---------------------------------------------------------------------------------------------- score
rows, ALLTR = [], {}
for c in CONFIGS:
    tr = run(c)
    k = cid(c)
    ALLTR[k] = tr
    rows.append({"id": k, **{x: c[x] for x in ("fam", "side", "th", "entry", "H")}, "cond": str(c["cond"]), **stats(tr)})
    print(k, len(tr), flush=True)
# controls (not counted): every event, same side
for side in (1, -1):
    for en in ("CLOSE", "OPEN"):
        for H in (1, 5, 20):
            tr = trades(EV, side, en, H)
            rows.append({"id": f"CTRL_ALL_{'L' if side > 0 else 'S'}_{en}_H{H}", "fam": "CTRL", "side": side, "entry": en, "H": H, **stats(tr)})
    if EVA is not None:
        for en in ("AH", "OPEN"):
            for H in (1, 5, 20):
                tr = trades(EVA, side, en, H, 1.0, EVA.ah_px.to_numpy(), EVA.ah_cost.to_numpy()) if en == "AH" else trades(EVA, side, en, H)
                rows.append({"id": f"CTRL_AHALL_{'L' if side > 0 else 'S'}_{en}_H{H}", "fam": "CTRL", "side": side, "entry": en, "H": H, **stats(tr)})
res = pd.DataFrame(rows)
res.to_csv(HERE / "results.csv", index=False, float_format="%.5f")

# ---------------------------------------------------------------------------------------------- gates
R = res.set_index("id")
HST = [1, 5, 20]


def neighbours(c):
    out = []
    for o in CONFIGS:
        if o is c or o["fam"] != c["fam"] or o["side"] != c["side"]:
            continue
        diff = [k for k in ("cond", "th", "entry", "H") if o[k] != c[k]]
        if len(diff) != 1:
            continue
        k = diff[0]
        if k == "H":
            ok = abs(HST.index(o["H"]) - HST.index(c["H"])) == 1
        elif k in ("entry", "th"):
            ok = True
        else:
            if c["fam"] == "U":
                ok = o["cond"][1] == c["cond"][1]
            elif c["fam"] == "P":
                ss = ["SAME2", "SAME3", "SAME4"]
                ok = c["cond"] in ss and o["cond"] in ss and abs(ss.index(c["cond"]) - ss.index(o["cond"])) == 1
            else:
                ok = False
        if ok:
            out.append(cid(o))
    return out


g = []
for c in CONFIGS:
    k = cid(c); r = R.loc[k]
    nb = neighbours(c)
    nbm = float(np.nanmean([R.loc[x, "mean"] for x in nb])) if nb else np.nan
    sp = [r.get(f"m_{s}", np.nan) for s in ("train", "valid", "valid2")]
    gates = {
        "g_n": r["n"] >= 150, "g_splits": all(np.nan_to_num(x, nan=-1) > 0 for x in sp),
        "g_t": np.nan_to_num(r.get("t", np.nan), nan=-9) >= T_REQ,
        "g_regime": np.nan_to_num(r.get("m_up"), nan=-1) > 0 and np.nan_to_num(r.get("m_down"), nan=-1) > 0,
        "g_wf": np.nan_to_num(r.get("wf_share"), nan=0) >= 0.6, "g_plateau": (not nb) or nbm > 0,
        "g_exbest": np.nan_to_num(r.get("ex_best_day"), nan=-1) > 0,
        "g_busy": np.nan_to_num(r.get("busiest_share"), nan=1) <= 0.10,
    }
    if all(gates.values()):
        v = "candidate"
    elif np.nan_to_num(r.get("mean"), nan=-1) > 0 and sum(np.nan_to_num(x, nan=-1) > 0 for x in sp) >= 2:
        v = "near"
    else:
        v = "fail"
    g.append({"id": k, "fam": c["fam"], "verdict": v, **gates, "nb_mean": nbm, "neighbours": ";".join(nb),
              **{x: r.get(x) for x in ("n", "mean", "t", "m_train", "m_valid", "m_valid2", "m_up", "m_down", "wf_share",
                                     "ex_best_day", "busiest_share", "raw", "hit")}})
G = pd.DataFrame(g)
G.to_csv(HERE / "gates.csv", index=False, float_format="%.5f")
print("T_REQ", round(T_REQ, 3))
print(G.groupby(["fam", "verdict"]).size().unstack(fill_value=0))

# ---------------------------------------------------------------------------------------------- diagnostics
picks = list(G.loc[G.verdict == "candidate", "id"])
for fam in ("B", "U", "P", "G", "A"):
    sub = G[(G.fam == fam) & (G.verdict != "candidate")]
    if len(sub):
        picks.append(sub.sort_values("t", ascending=False).iloc[0]["id"])
byid = {cid(c): c for c in CONFIGS}
EVF = None
d_rows = []
for k in dict.fromkeys(picks):
    c = byid[k]
    var = {"cost2x": dict(cost_mult=2.0), "top300": dict(top300=True)}
    if c["fam"] == "A":
        var["ahcost2x"] = dict(ah_cost_mult=2.0)
    elif c["entry"] in ("CLOSE", "OPEN"):
        if EVF is None:
            f = E.events(fixed_window=True)
            EVF = f[f.elig & (f.split != "none") & ~f.locked_touch].reset_index(drop=True)
        var["fixed_window"] = dict(fixed=EVF)
    for vn, kw in var.items():
        d_rows.append({"base": k, "variant": vn, **stats(run(c, **kw))})
pd.DataFrame(d_rows).to_csv(HERE / "diag.csv", index=False, float_format="%.5f")
print("diagnostics", picks)
pd.concat([t.assign(id=k) for k, t in ALLTR.items() if len(t)]).to_parquet(E.DATA / "trades.parquet", index=False)
