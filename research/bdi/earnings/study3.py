"""ER earnings study, part 3 (NOTES.md 3 + 3.1): EPS surprise families with Yahoo report timing.
Reuses the part-2 engine (study.py up to its scoring section, executed here without scoring). RV (revenue) is pending
data and not run. One process, < 1.5 GB.
    python research/bdi/earnings/study3.py   -> results3.csv, gates3.csv, diag3.csv
Educational only - not financial advice.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
_src = (HERE / "study.py").read_text().split("# " + "-" * 94 + " score")[0]
_g = {"__file__": str(HERE / "study.py"), "__name__": "study_engine"}
exec(compile(_src, "study_engine", "exec"), _g)          # engine: trades, stats, cond_mask, AH sample, TOP300
E, trades, stats, cond_mask, AH, TOP300 = (_g[k] for k in ("E", "trades", "stats", "cond_mask", "AH", "TOP300"))
Cn, T = E.Cn, E.T

N_PART3 = 150
N_LINEAGE = 264 + N_PART3
T_REQ = math.sqrt(2 * math.log(N_LINEAGE))

Y = E.events_yahoo()
EV = Y[Y.elig & (Y.split != "none") & ~Y.locked_touch].reset_index(drop=True)
print("yahoo events", len(EV), EV.split.value_counts().to_dict(), EV.timing.value_counts().to_dict(), flush=True)

# after-hours sample on Yahoo amc events (report hour 16:xx), date = report day d
spy_ah = AH[AH.symbol == "SPY"].set_index("day")
spy_mv = spy_ah.psig / spy_ah.p1559 - 1
a = EV[(EV.timing == "amc") & (EV.hour_et < 17)].copy()
a["day"] = pd.to_datetime(a["date"]).astype("datetime64[ns]")
AHm = AH.copy(); AHm["day"] = pd.to_datetime(AHm["day"]).astype("datetime64[ns]")
a = a.merge(AHm, on=["day", "symbol"], how="inner")
a["d"] = np.searchsorted(E.dates.values, a.day.values)
a = a[(E.dates[a.d.to_numpy()] == a.day.values) & a.psig.notna() & a.pent.notna()].copy()
a["R"] = a.d                                                     # family-A convention: R = report day
a = a[a.R + 2 < T]
a["REACT"] = a.psig / a.p1559 - 1 - a.day.map(spy_mv).fillna(0).to_numpy()
a["ah_px"] = Cn[a.d.to_numpy(), a.j.to_numpy()] * a.pent / a.p1559
a["ah_cost"] = (a.spread / 2).clip(lower=0.0010).fillna(0.0050) + E.SLIP_PS / a.pent + E.SLIP_BPS
EVA = a.reset_index(drop=True)
print("AH yahoo-amc events", len(EVA), EVA.split.value_counts().to_dict(), flush=True)

# ---------------------------------------------------------------------------------------------- grid
HS = (1, 5, 20)
CONFIGS = []


def add(**c):
    CONFIGS.append(c)


for side in (1, -1):
    for X in (0, 5, 10):
        for en in ("OPENR", "CLOSE", "OPEN"):
            for H in HS:
                add(fam="E", side=side, X=X, cond=None, entry=en, H=H)
    for cond in ("AGREE", "DISAGREE"):
        for en in ("CLOSE", "OPEN"):
            for H in HS:
                add(fam="EB", side=side, X=5, cond=cond, entry=en, H=H)
    for en in ("OPENR", "CLOSE"):
        for H in HS:
            add(fam="SH", side=side, X=0, cond="SAME3", entry=en, H=H)
    for en in ("AH", "OPEN"):
        for H in HS:
            add(fam="AR", side=side, X=None, cond=None, entry=en, H=H)
        for cond in ("AGREE", "DISAGREE"):
            for H in HS:
                add(fam="AE", side=side, X=0, cond=cond, entry=en, H=H)
for cond in ((5, "down"), (20, "down")):
    for en in ("CLOSE", "OPEN"):
        for H in HS:
            add(fam="TR", side=1, X=None, cond=cond, entry=en, H=H)
for cond in ("SAME2", "SAME3"):
    for en in ("CLOSE", "OPEN"):
        for H in HS:
            add(fam="TRP", side=1, X=None, cond=cond, entry=en, H=H)
assert len(CONFIGS) == N_PART3, len(CONFIGS)


def cid(c):
    cs = "" if c["cond"] is None else ("_RUN%d%s" % c["cond"] if c["fam"] == "TR" else "_" + c["cond"])
    xs = "" if c["X"] is None else f"_X{c['X']}"
    return f"{c['fam']}_{'L' if c['side'] > 0 else 'S'}{xs}{cs}_{c['entry']}_H{c['H']}"


def beat(sp, side, X):
    s = sp * side
    return (s > 0) if X == 0 else (s >= X)


def select(c, ev):
    s = c["side"]; f = c["fam"]
    if f == "E":
        return beat(ev.surprise_pct, s, c["X"])
    if f == "EB":
        if c["cond"] == "AGREE":
            return beat(ev.surprise_pct, s, 5) & (ev.REACT * s >= 0.04)
        return beat(ev.surprise_pct, s, 5) & (ev.REACT * s <= -0.04)       # L: beat but sold off; S: miss but rallied
    if f == "SH":
        return beat(ev.surprise_pct, s, 0) & (ev.SPREV1 * s > 0) & (ev.SPREV2 * s > 0) & (ev.SPREV3 * s > 0)
    if f == "AR":
        return ev.REACT * s >= 0.04
    if f == "AE":
        m = ev.REACT * s >= 0.04
        return m & ((ev.surprise_pct * s > 0) if c["cond"] == "AGREE" else (ev.surprise_pct * s < 0))
    if f == "TR":
        return (ev.REACT >= 0.04) & cond_mask(ev, "U", c["cond"], 1)
    if f == "TRP":
        return (ev.REACT >= 0.04) & cond_mask(ev, "P", c["cond"], 1)
    raise ValueError(f)


def run(c, cost_mult=1.0, ah_cost_mult=1.0, top300=False):
    ev = EVA if c["fam"] in ("AR", "AE") else EV
    sel = select(c, ev)
    m = np.array(sel.fillna(False) if hasattr(sel, "fillna") else sel, dtype=bool)
    if top300:
        m &= TOP300[ev.R.to_numpy() - 1, ev.j.to_numpy()]
    e = ev[m]
    if c["entry"] == "AH":
        return trades(e, c["side"], "AH", c["H"], cost_mult, e.ah_px.to_numpy(), e.ah_cost.to_numpy() * ah_cost_mult)
    return trades(e, c["side"], c["entry"], c["H"], cost_mult)


rows, ALLTR = [], {}
for c in CONFIGS:
    tr = run(c); k = cid(c); ALLTR[k] = tr
    rows.append({"id": k, **{x: str(c[x]) for x in ("fam", "side", "X", "cond", "entry", "H")}, **stats(tr)})
    print(k, len(tr), flush=True)
# controls (not counted): all Yahoo events per side/entry/H; all AH yahoo-amc events
for side in (1, -1):
    for en in ("OPENR", "CLOSE", "OPEN"):
        for H in HS:
            rows.append({"id": f"CTRL3_ALL_{'L' if side > 0 else 'S'}_{en}_H{H}", "fam": "CTRL", **stats(trades(EV, side, en, H))})
    for en in ("AH", "OPEN"):
        for H in HS:
            tr = trades(EVA, side, en, H, 1.0, EVA.ah_px.to_numpy(), EVA.ah_cost.to_numpy()) if en == "AH" else trades(EVA, side, en, H)
            rows.append({"id": f"CTRL3_AHALL_{'L' if side > 0 else 'S'}_{en}_H{H}", "fam": "CTRL", **stats(tr)})
res = pd.DataFrame(rows)
res.to_csv(HERE / "results3.csv", index=False, float_format="%.5f")
R = res.set_index("id")

ENT_ORDER = {"OPENR": 0, "CLOSE": 1, "OPEN": 2, "AH": 1}


def neighbours(c):
    out = []
    for o in CONFIGS:
        if o is c or o["fam"] != c["fam"] or o["side"] != c["side"]:
            continue
        diff = [k for k in ("cond", "X", "entry", "H") if o[k] != c[k]]
        if len(diff) != 1:
            continue
        k = diff[0]
        if k == "H":
            ok = abs(HS.index(o["H"]) - HS.index(c["H"])) == 1
        elif k == "entry":
            ok = abs(ENT_ORDER[o["entry"]] - ENT_ORDER[c["entry"]]) == 1
        elif k == "X":
            ok = abs([0, 5, 10].index(o["X"]) - [0, 5, 10].index(c["X"])) == 1
        else:
            ok = (c["fam"] == "TR" and o["cond"][1] == c["cond"][1]) or (c["fam"] == "TRP")
        if ok:
            out.append(cid(o))
    return out


g = []
for c in CONFIGS:
    k = cid(c); r = R.loc[k]; nb = neighbours(c)
    nbm = float(np.nanmean([R.loc[x, "mean"] for x in nb])) if nb else np.nan
    sp = [r.get(f"m_{s}", np.nan) for s in ("train", "valid", "valid2")]
    nz = lambda v, d: d if v is None or (isinstance(v, float) and np.isnan(v)) else v  # noqa: E731
    gates = {"g_n": nz(r.get("n"), 0) >= 150, "g_splits": all(nz(x, -1) > 0 for x in sp),
             "g_t": nz(r.get("t"), -9) >= T_REQ, "g_regime": nz(r.get("m_up"), -1) > 0 and nz(r.get("m_down"), -1) > 0,
             "g_wf": nz(r.get("wf_share"), 0) >= 0.6, "g_plateau": (not nb) or nbm > 0,
             "g_exbest": nz(r.get("ex_best_day"), -1) > 0, "g_busy": nz(r.get("busiest_share"), 1) <= 0.10}
    if all(gates.values()):
        v = "candidate"
    elif nz(r.get("mean"), -1) > 0 and sum(nz(x, -1) > 0 for x in sp) >= 2:
        v = "near"
    else:
        v = "fail"
    g.append({"id": k, "fam": c["fam"], "verdict": v, **gates, "nb_mean": nbm,
              **{x: r.get(x) for x in ("n", "mean", "t", "m_train", "m_valid", "m_valid2", "m_up", "m_down", "wf_share",
                                     "ex_best_day", "busiest_share", "raw", "hit")}})
G = pd.DataFrame(g)
G.to_csv(HERE / "gates3.csv", index=False, float_format="%.5f")
print("T_REQ", round(T_REQ, 3))
print(G.groupby(["fam", "verdict"]).size().unstack(fill_value=0))

picks = list(G.loc[G.verdict == "candidate", "id"])
for fam in G.fam.unique():
    sub = G[(G.fam == fam) & (G.verdict != "candidate")]
    picks.append(sub.sort_values("t", ascending=False).iloc[0]["id"])
byid = {cid(c): c for c in CONFIGS}
d_rows = []
for k in dict.fromkeys(picks):
    c = byid[k]
    var = {"cost2x": dict(cost_mult=2.0), "top300": dict(top300=True)}
    if c["entry"] == "AH":
        var["ahcost2x"] = dict(ah_cost_mult=2.0)
    for vn, kw in var.items():
        d_rows.append({"base": k, "variant": vn, **stats(run(c, **kw))})
pd.DataFrame(d_rows).to_csv(HERE / "diag3.csv", index=False, float_format="%.5f")
print("diagnostics", picks)
pd.concat([t.assign(id=k) for k, t in ALLTR.items() if len(t)]).to_parquet(E.DATA / "trades3.parquet", index=False)
