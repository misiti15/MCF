"""Stages A-C of PLAN.md; every configuration is written to scan_all.csv.gz (empty ones too).
Educational only - not financial advice."""
import itertools
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import (EXITS, FILTERS, FR, HERE, KS, LEVELS, NAT, OPP, PARENTS, PS, VOLS, WINS, WM, core_rows, evfilter,
                    pick, score)

WB = ("0950-1500", "0950-1130", "1130-1500")
XC = ("t05s1", "t1s1", "t05s1so")


def rec(stage, L, p, k, vol, filt, side, x, win, refire, idx):
    r = {"stage": stage, "L": L, "p": p, "k": k, "vol": vol, "filters": filt, "side": side, "exit": x, "win": win,
         "refire": refire}
    r.update(score(idx, side, x) if len(idx) else {"n_tr": 0, "n_va": 0, "n_all": 0})
    return r


def frows(L, p, k, vol, f):
    if f in FR:
        rows = core_rows(L, p, k, vol)
        return rows[FR[f][rows]]
    return core_rows(L, p, k, vol, evfilter(f, L))


def stage_a(L):
    out = []
    t0 = time.time()
    for p, k, vol in itertools.product(PS, KS, VOLS):
        rows = core_rows(L, p, k, vol)
        for side, w, rf in itertools.product((NAT[L], OPP[NAT[L]]), WINS, (False, True)):
            idx = pick(rows[WM[w][rows]], rf)
            for x in EXITS:
                out.append(rec("A", L, p, k, vol, "", side, x, w, rf, idx))
    print("A", L, len(out), round(time.time() - t0), flush=True)
    return out


def stage_b(L):
    out = []
    t0 = time.time()
    for p, vol, f in itertools.product((0.05, 0.10, 0.20), ("any", "v<1"), FILTERS):
        rows = frows(L, p, 3, vol, f)
        for side, w in itertools.product((NAT[L], OPP[NAT[L]]), WB):
            idx = pick(rows[WM[w][rows]])
            for x in EXITS:
                out.append(rec("B", L, p, 3, vol, f, side, x, w, False, idx))
    print("B", L, len(out), round(time.time() - t0), flush=True)
    return out


def stage_c(name):
    L, p, vol, side, _ = PARENTS[name]
    out = []
    t0 = time.time()
    base = core_rows(L, p, 3, vol)
    FM = {}
    for f in FILTERS:
        if f in FR:
            FM[f] = FR[f][base]
        else:
            fr = frows(L, p, 3, vol, f)
            FM[f] = np.isin(base, fr)
    for f1, f2 in itertools.combinations(FILTERS, 2):
        rows = base[FM[f1] & FM[f2]]
        idx = pick(rows[WM["0950-1500"][rows]])
        for x in XC:
            r = rec("C", L, p, 3, vol, f1 + "+" + f2, side, x, "0950-1500", False, idx)
            r["parent"] = name
            out.append(r)
    print("C", name, len(out), round(time.time() - t0), flush=True)
    return out


def job(a):
    st, arg = a
    return {"A": stage_a, "B": stage_b, "C": stage_c}[st](arg)


if __name__ == "__main__":
    jobs = [("A", L) for L in LEVELS] + [("B", L) for L in LEVELS] + [("C", n) for n in PARENTS]
    with Pool(4) as pool:
        res = pool.map(job, jobs, chunksize=1)
    out = pd.DataFrame([r for rr in res for r in rr])
    out.to_csv(HERE / "scan_all.csv.gz", index=False, float_format="%.5g")
    print("configs", len(out), out.groupby("stage").size().to_dict())
