"""top5_1022 step 3-4: execution variants of 6 non-CWT live setups (PLAN.md, written before this was run).
Entries = gates1021's cached live-shaped signal rows (live module / window / ADV / refire chain); exits = top5_1019 sim on
the 5-minute paths of top5_1019.build_paths (costs in). Locked block never loaded (load_sig asserts; months from the
cache, which holds open months only). Educational only - not financial advice.

    python research/bdi/top5_1022/scan_1022.py      # -> $SCR/trades.parquet (scratch)
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
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1019"), str(ROOT / "research" / "bdi" / "gates1021" / "scripts")]
from scan_1019 import lib, sim, build_paths  # noqa: E402
from load import load_sig  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/t5tune1022")
SETUPS = ("MF3-open-flowsell-rsi5hi-FD", "RW7-gapdn-bounce-early-short-FD", "RW4-ns3-adv150-short-FD",
          "exhaustion_short-FD", "MF5-flowsell-vwapup-rsi5hi-FD", "RW1-gapdn-bounce-flowsell-short-FD")
SIDE = -1
EX0 = dict(up=1.0, dn=1.0, em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, keep=None)
GRID = [("P", "parent_t1s1", {}),
        ("E01", "timestop30_lt0.2", dict(tsb=6, tsr=0.2)), ("E02", "timestop60_lt0.25", dict(tsb=12, tsr=0.25)),
        ("E03", "stop_x085", dict(dn=0.85)), ("E04", "stop_x125", dict(dn=1.25)), ("E05", "stop_x150", dict(dn=1.5)),
        ("E06", "scale_half_0.5R_be", dict(so=0.5)), ("E07", "be_after_0.5R", dict(be=0.5)),
        ("E08", "target0.75", dict(up=0.75)), ("E09", "target1.5", dict(up=1.5)), ("E10", "wait1", dict(em=2)),
        ("E11", "from1030", dict(keep="from1030")), ("E12", "until1300", dict(keep="until1300")),
        ("E13", "skip1000_1029", dict(keep="skip1000")), ("E14", "skip_spy_up", dict(keep="spydn")),
        ("E15", "timestop15_lt0.1", dict(tsb=3, tsr=0.1))]


def keep_mask(s, k):
    tod = s["tod"].to_numpy(int)
    if k is None:
        return np.ones(len(s), bool)
    if k == "from1030":
        return tod >= 1030
    if k == "until1300":
        return tod <= 1300
    if k == "skip1000":
        return ~((tod >= 1000) & (tod < 1030))
    if k == "spydn":
        return ~(s["spy_fo"].to_numpy(float) > 0)
    raise ValueError(k)


def month_job(args):
    month, sg = args
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    key = fh[["symbol", "date", "tod"]].copy()
    key["date"] = pd.to_datetime(key["date"]).dt.date
    key["fhi"] = np.arange(len(fh))
    key = key[fh["_fi"].to_numpy() >= 0]
    sg = sg.merge(key, on=["symbol", "date", "tod"], how="left")
    ok = sg["fhi"].notna().to_numpy()
    sg = sg[ok].reset_index(drop=True)
    ent_all = fh2P[sg["fhi"].to_numpy(np.int64)]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float),
                    P["tod"].to_numpy(np.int32))
    atrP = P["atr"].to_numpy(float)
    rows = []
    for vid, knob, ov in GRID:
        prm = {**EX0, **ov}
        m = keep_mask(sg, prm["keep"])
        ent = ent_all[m]
        Rv = 0.25 * atrP[np.maximum(ent, 0)]
        r, mfe, mae, cd, et, xr = sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, np.full(len(ent), np.nan), SIDE,
                                      prm["up"], prm["dn"], prm["em"], prm["tsb"], prm["tsr"], prm["be"], prm["so"],
                                      prm["sof"], prm["xt"])
        sc = prm["dn"]  # same $ risk vs the parent 1R stop
        t = sg.loc[m, ["setup", "date", "symbol", "tod", "r", "c_short_t1s1", "spy_o2c", "split"]].rename(
            columns={"r": "r_cache", "c_short_t1s1": "ctrl"}).reset_index(drop=True)
        t["r"], t["mfe"], t["mae"], t["code"] = r / sc, mfe / sc, mae / sc, cd
        t["var"], t["knob"] = vid, knob
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    print(month, len(sg), "unmatched", int((~ok).sum()), round(time.time() - t0), flush=True)
    return out


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    S = load_sig(list(SETUPS))
    S["month"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m")
    jobs = [(m, g.drop(columns="month")) for m, g in S.groupby("month")]
    assert not {m for m, _ in jobs} & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, jobs), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"]).agg(n=("r", "size"), exp=("r", "mean")).round(4).to_string())


if __name__ == "__main__":
    main()
