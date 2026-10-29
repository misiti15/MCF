"""p1_1029: (a) task 3 one-knob exits (stop distance at the same $ risk, scale-out trigger) on the three Primary short
families from the rebuilt gates1021 cache; (b) CWT14 failed-PDL-break longs (top5_1019 kernel, live geometry) as
parent trades for tasks 2 and 4. Simulator = top5_1028's (imported). Locked block never loaded.
Educational only - not financial advice.

    G21SCR=$SCRATCH/p1/g P1_PROCS=2 python research/bdi/p1_1029/scan_p1.py    # -> $SCRATCH/p1/trades_p1.parquet
"""
from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1028"), str(ROOT / "research" / "bdi" / "top5_1019"),
                str(ROOT / "research" / "bdi" / "gates1021" / "scripts")]
from scan_1019 import lib, build_paths, spy_fo, S6, CL  # noqa: E402
from scan_1028 import simrun, EX0  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/p1")
INF = np.inf
MF2, RW5, RW3 = ("MF2-open-rsimidhi-flowsell-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
                 "RW3-gapdn-rsi5pop-flowsell-short-FD")
SHORTS = (MF2, RW5, RW3)
BASE = {MF2: dict(side=-1, up=1.0, dn=0.5), RW5: dict(side=-1, up=1.0, dn=1.0), RW3: dict(side=-1, up=1.0, dn=1.0)}
CWT14 = {"CWT14-failbrk-pdl-p05-long": dict(level="PD", p=0.05, vr=INF, side=1, so=0.25),
         "CWT14-failbrk-pdl-p05-lowvol-long": dict(level="PD", p=0.05, vr=1.0, side=1, so=0.0),
         "CWT14-failbrk-pdl-p10-long": dict(level="PD", p=0.10, vr=INF, side=1, so=0.0),
         "CWT14-failbrk-pdl-p10-lowvol-long": dict(level="PD", p=0.10, vr=1.0, side=1, so=0.0)}


def grid3(s):
    """PLAN.md task 3: P, S1..S5 stop multiples (same $ risk), O1..O4 scale half at +x R (x in risk units), rest BE."""
    b = BASE[s]["dn"]
    g = [("P", "parent", {})]
    for i, k in enumerate((1.5, 2.0, 2.5, 3.0, 3.5), 1):
        g.append((f"S{i}", f"stop_x{k}", dict(dn=b * k)))
    for i, x in enumerate((0.25, 0.40, 0.60, 0.80), 1):
        g.append((f"O{i}", f"scale_half_{x}R_be", dict(so=x * b)))
    return g


def month_job(args):
    month, sg = args
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P))
    tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    A = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32),
         dend, tierP)
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    rows = []
    # ---- CWT14 pdl longs (live geometry t05s1; p05 has the live 0.25R scale-out)
    x = CL.arrays(fh)
    lev = S6.levels(x)
    ftod = fh["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        ok0 = (fh["adv20"].fillna(0).to_numpy() >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & (ftod >= 950) & (ftod <= 1500)
        for s, d in CWT14.items():
            m = np.asarray(S6.b3_any(x, lev[(d["level"], d["side"])], d, d["p"]), bool) & ok0
            e1 = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fh["date"].to_numpy(), m)
            ent = fh2P[e1]
            prm = {**EX0, "side": 1, "up": 0.5, "dn": 1.0, "so": d["so"]}
            res = simrun(A, ent, 0.25 * atrP[np.maximum(ent, 0)], 1, prm)
            rows.append(pd.DataFrame({"setup": s, "var": "P", "knob": "parent", "date": dat[ent], "symbol": sym[ent],
                                      "tod": A[3][ent], "r": res[0], "cache_r": np.nan}))
    # ---- task 3 shorts from the cache
    key = fh[["symbol", "date", "tod"]].copy()
    key["date"] = pd.to_datetime(key["date"]).dt.date
    key["fhi"] = np.arange(len(fh))
    key = key[fh["_fi"].to_numpy() >= 0]
    sg = sg.merge(key, on=["symbol", "date", "tod"], how="left")
    ok = sg["fhi"].notna().to_numpy()
    sg = sg[ok].reset_index(drop=True)
    for s in SHORTS:
        g = sg[sg.setup == s]
        if not len(g):
            continue
        ent = fh2P[g["fhi"].to_numpy(np.int64)]
        for vid, knob, ov in grid3(s):
            prm = {**EX0, **BASE[s], **ov}
            res = simrun(A, ent, 0.25 * atrP[np.maximum(ent, 0)], -1, prm)
            rows.append(pd.DataFrame({"setup": s, "var": vid, "knob": knob, "date": dat[ent], "symbol": sym[ent],
                                      "tod": g["tod"].to_numpy(int), "r": res[0] / prm["dn"],
                                      "cache_r": g["r"].to_numpy(float) / BASE[s]["dn"] if vid == "P" else np.nan}))  # cache R is in 0.25-ATR units; live R = stop distance
    out = pd.concat(rows, ignore_index=True)
    out = out[np.isfinite(out["r"])]
    print(month, len(out), "unmatched", int((~ok).sum()), round(time.time() - t0), flush=True)
    return out


def main():
    from load import load_sig
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    S = load_sig(list(SHORTS))
    S["month"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m")
    S = S[["setup", "symbol", "date", "tod", "r", "month"]]
    jobs = [(m, S[S.month == m].drop(columns="month")) for m in months]
    with Pool(int(os.environ.get("P1_PROCS", 2))) as p:
        T = pd.concat(p.map(month_job, jobs), ignore_index=True)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    T.to_parquet(SCR / "trades_p1.parquet", index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), exp=("r", "mean")).round(4).to_string())


if __name__ == "__main__":
    main()
