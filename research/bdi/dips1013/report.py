"""dips1013 selection (PLAN.md section 4 + A1): finalists, plateau, walk-forward, regimes, same-minute excess by
up / down session, next-bar-open line, Testing-1 bar -> finalists.csv, summary.json. Educational only - not financial
advice. Nothing is scored on the locked block."""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import configs as CF
from engine import HERE, Data, all_exits, gates, levels, lib, simulate, tod_of, trades_frame

res = pd.read_csv(HERE / "results.csv", low_memory=False)
N_A = int((res.part.isin(["A", "Ac"])).sum())
N_B = int((res.part.isin(["B", "Bc"])).sum())
N_STUDY = len(res)
N_LIN_A, N_LIN_B = N_A, N_B + 31454
TB = {"study": gates.t_required(N_STUDY), "A": gates.t_required(N_LIN_A), "B": gates.t_required(N_LIN_B)}
print("N", N_STUDY, N_A, N_B, TB, flush=True)
idx = res.set_index("cfg")

A_THR = {"rsi2": ("5", "10"), "rsi5": ("15", "25"), "rsi14": ("25", "30"), "vwap": ("0.5", "1.0"), "sma20": ("0.5", "1.0"),
         "bb": ("2.0", "2.5"), "streak": ("3", "5"), "dfh": ("1.0", "1.5")}
UNITS = {"p": [0.75, 1.0, 1.5, 2.0], "a": [0.5, 0.75, 1.0]}
ENTRY_NB = {"E945": ["E950"], "E950": ["E945", "E955"], "E955": ["E950"], "PBH": ["E955"], "HL": ["E955"], "VR": ["E955"]}
RUN_FILT_A, RUN_FILT_B = {"none", "pcl"}, {"none", "pcl", "capd"}


def neighbours(r):
    if r.part == "A":
        fam, thr = r.os.split("-")
        o = [t for t in A_THR[fam] if t != thr][0]
        nb = [f"A-{fam}-{o}-{r.L}-{r.trig}-{r.filt}-{r.win}-{r.exit}",
              f"A-{r.os}-{'L3' if r.L == 'L1' else 'L1'}-{r.trig}-{r.filt}-{r.win}-{r.exit}"]
    else:
        xs = UNITS[r.unit]
        i = xs.index(float(r.x))
        nb = [f"B-{r.ref}-{r.unit}{xs[j]}-{r.gapc}-{r.entry}-{r.filt}-{r.exit}" for j in (i - 1, i + 1) if 0 <= j < len(xs)]
        nb += [f"B-{r.ref}-{r.unit}{r.x}-{r.gapc}-{e}-{r.filt}-{r.exit}" for e in ENTRY_NB[r.entry]]
    return nb


def plateau(r):
    v = idx.reindex(neighbours(r))["open_exp"]
    return float(v.min()) if v.notna().all() else float("nan")


def runnable(r):
    if r.part == "A":
        return r.filt in RUN_FILT_A and not r.os.startswith("bb")
    return r.entry != "E945" and r.filt in RUN_FILT_B


# ------------------------------------------------------------------------------------------------ finalists
fin = []
for part, key in (("A", "trig"), ("B", "entry")):
    x = res[(res.part == part) & (res.train_n >= 150) & (res.train_exp > 0)].sort_values("train_t", ascending=False)
    pick = list(x.head(10).cfg)
    for v in x[key].dropna().unique():
        y = x[x[key] == v]
        if len(y) and y.iloc[0].cfg not in pick:
            pick.append(y.iloc[0].cfg)
    fin += pick
FZ = res[res.cfg.isin(fin)].copy()
print("finalists", len(FZ), flush=True)

# ------------------------------------------------------------------------------------------------ re-run finalists
D = Data()
need = sorted(set(FZ.exit))
NET, CT = all_exits(D, exits=need)
PA, PB = CF.PartA(D), CF.PartB(D)
REG = lib.regimes()
REG.index = pd.to_datetime(REG.index)
out = []
for r in FZ.itertuples():
    if r.part == "A":
        d, k = PA.trades(r.os, r.L, r.trig, r.filt, r.win)
    else:
        d, k = PB.trades(r.ref, r.unit, float(r.x), r.gapc, r.entry, r.filt)
    T = trades_frame(D, NET, CT, r.exit, d, k)
    T.to_parquet(HERE / "data" / f"trades_{r.cfg}.parquet", index=False)
    s = gates.summary(T)
    rs = gates.regime_split(T.assign(date=T.date), REG)
    wf = gates.walk_forward(T, exclude_months=lib.LOCKED_MONTHS)
    lin = N_LIN_A if r.part == "A" else N_LIN_B
    v, fails = gates.verdict(s, rs, wf, lin)
    # next-bar-open entry (same exit rule, levels re-anchored to the fill; stop must stay below the fill)
    rn = []
    for kk in np.unique(T.k):
        rows_k = T.row.to_numpy()[T.k.to_numpy() == kk]
        if kk + 1 > 76:
            continue
        px1 = D.O[:, kk + 1]
        stop, tgt = levels(D, kk, r.exit, px=px1)
        net, _, _ = simulate(D, kk, stop, tgt, entry=px1, from_k=kk + 1)
        good = ~(stop >= px1)
        sel = rows_k[good[rows_k]]
        rn.append(pd.DataFrame({"date": D.dates[D.sess[sel]], "r": net[sel]}))
    rn = pd.concat(rn).dropna()
    nb = gates.summary(rn)
    out.append({"cfg": r.cfg, "plateau": plateau(r), "runnable": runnable(r), "wf": wf.get("share_positive"),
                "verdict": v, "fails": "; ".join(fails), "next_open_exp": nb.get("exp_r"), "next_open_t": nb.get("t"),
                "regime_pass": rs.get("pass")})
    print(r.cfg, s.get("n"), s.get("exp_r"), s.get("t"), v, flush=True)
FZ = FZ.merge(pd.DataFrame(out), on="cfg")


def bar(r):
    return bool(r.open_n >= 150 and r.open_exp > 0 and (r.open_t or 0) >= 1.5 and r.train_exp > 0 and r.valid_exp > 0
                and r.ex_best > 0 and r.busiest <= 0.10 and r.open_exc > 0 and r.train_exc > 0 and r.valid_exc > 0
                and r.plateau > 0 and r.runnable)


def bar_no_run(r):
    return bool(r.open_n >= 150 and r.open_exp > 0 and (r.open_t or 0) >= 1.5 and r.train_exp > 0 and r.valid_exp > 0
                and r.ex_best > 0 and r.busiest <= 0.10 and r.open_exc > 0 and r.train_exc > 0 and r.valid_exc > 0
                and r.plateau > 0)


FZ["testing_bar"] = [bar(r) for r in FZ.itertuples()]
FZ["bar_except_runnable"] = [bar_no_run(r) for r in FZ.itertuples()]
FZ = FZ.sort_values(["part", "train_t"], ascending=[True, False])
FZ.to_csv(HERE / "finalists.csv", index=False, float_format="%.5g")

# ------------------------------------------------------------------------------------------------ summary tables
def med(part, col):
    x = res[res.part == part]
    return {str(k): round(float(v), 4) for k, v in x.groupby(col)["open_exp"].median().items()}


summ = {"n_configs": N_STUDY, "n_part_a": N_A, "n_part_b": N_B, "t_bars": TB,
        "reach_study_bar_n150": int(((res.open_t >= TB["study"]) & (res.open_exp > 0) & (res.open_n >= 150)).sum()),
        "excess_reach_study_bar_n150": res[(res.open_exc_t >= TB["study"]) & (res.open_n >= 150)].cfg.tolist(),
        "reach_t15_open_pos": int(((res.open_t >= 1.5) & (res.open_exp > 0) & (res.open_n >= 150)).sum()),
        "positive_open_n150": {p: int(((res.part == p) & (res.open_exp > 0) & (res.open_n >= 150)).sum()) for p in ("A", "B")},
        "positive_excess_t2_n150": {p: int(((res.part == p) & (res.open_exc_t >= 2) & (res.open_n >= 150)).sum()) for p in ("A", "B")},
        "medians_A": {c: med("A", c) for c in ("os", "L", "trig", "filt", "win", "exit")},
        "medians_B": {c: med("B", c) for c in ("ref", "unit", "x", "gapc", "entry", "filt", "exit")},
        "medians_excess_B": {c: {str(k): round(float(v), 4) for k, v in res[res.part == "B"].groupby(c)["open_exc"].median().items()}
                             for c in ("entry", "filt", "gapc", "exit")},
        "medians_excess_A": {c: {str(k): round(float(v), 4) for k, v in res[res.part == "A"].groupby(c)["open_exc"].median().items()}
                             for c in ("os", "trig", "filt", "win", "exit")},
        "controls": res[res.part.isin(["Ac", "Bc"])][["cfg", "open_n", "open_exp", "open_t", "up_exp", "down_exp"]].round(4).to_dict("records"),
        "finalists": FZ.cfg.tolist(), "keep": FZ[FZ.verdict == "keep"].cfg.tolist(),
        "testing_pass": FZ[FZ.testing_bar].cfg.tolist(),
        "bar_except_runnable": FZ[FZ.bar_except_runnable & ~FZ.testing_bar].cfg.tolist()}
json.dump(summ, open(HERE / "summary.json", "w"), indent=1, default=str)
print(json.dumps({k: summ[k] for k in ("n_configs", "t_bars", "reach_study_bar_n150", "excess_reach_study_bar_n150", "reach_t15_open_pos", "positive_open_n150",
                                       "positive_excess_t2_n150", "keep", "testing_pass", "bar_except_runnable")}, indent=1))
