"""top5_1103 step 3-4: execution variants of the 5 chosen live setups (PLAN.md, written before this was run).
Entries: gates1021's live-shaped signal rows (rebuilt by build_cache.py into /dev/shm/t5_1103/g). Exits: the top5_1028
simulator (imported, unchanged), in 0.25-ATR units; r is divided by the row's stop multiple (same $ risk). Locked
block never loaded (lib.months() is open months only; asserts). Educational only - not financial advice.

    G21SCR=/dev/shm/t5_1103/g python research/bdi/top5_1103/scan_1103.py   # -> /dev/shm/t5_1103/trades.parquet
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
from scan_1019 import lib, build_paths, spy_fo, CL  # noqa: E402
from scan_1028 import sim, keep_mask as keep_1028  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/dev/shm/t5_1103")
G21 = Path(os.environ.get("G21SCR", str(SCR / "g")))

CACHED = ("exhaustion_short-FD", "RW3S-gapdn-flowsell-short-FD", "RW1-gapdn-bounce-flowsell-short-FD",
          "L3-gap-slope-lowdist-FD", "ST7-rsi50dn-long-pm-t1s1-FD")
SETUPS = CACHED
SIDE = {"exhaustion_short-FD": -1, "RW3S-gapdn-flowsell-short-FD": -1, "RW1-gapdn-bounce-flowsell-short-FD": -1,
        "L3-gap-slope-lowdist-FD": -1, "ST7-rsi50dn-long-pm-t1s1-FD": 1}
GEOM = {s: "t1s1" for s in SETUPS}
GK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0)}
BASE = {s: dict(zip(("up", "dn"), GK[GEOM[s]])) for s in SETUPS}
CTRL = {s: f"c_{'long' if SIDE[s] == 1 else 'short'}_{GEOM[s]}" for s in SETUPS}
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, lim=0.0, keep=None)
CLOCK = {"exhaustion_short-FD": 1430, "RW3S-gapdn-flowsell-short-FD": 1200, "RW1-gapdn-bounce-flowsell-short-FD": 1200,
         "L3-gap-slope-lowdist-FD": 1400, "ST7-rsi50dn-long-pm-t1s1-FD": 1430}
SPLIT = {"exhaustion_short-FD": ("le1300", "gt1300"), "RW3S-gapdn-flowsell-short-FD": ("le1030", "ge1030"),
         "RW1-gapdn-bounce-flowsell-short-FD": ("le1300", "gt1300"), "L3-gap-slope-lowdist-FD": ("until1130", "from1130"),
         "ST7-rsi50dn-long-pm-t1s1-FD": ("le1300", "gt1300")}
CF_LIM = 0.15


def grid_s(s):
    """PLAN.md section 3 (16 rows per setup, relative to the live parent)."""
    b = BASE[s]
    up, dn = b["up"], b["dn"]
    a, z = SPLIT[s]
    g14 = ("G14", "spy_side_filter", dict(keep="spyup" if SIDE[s] == 1 else "spydn"))
    return [("P", "parent", {}),
            ("G01", "stop_x1.5", dict(dn=1.5 * dn)), ("G02", "stop_x2.0", dict(dn=2.0 * dn)),
            ("G03", "target_x0.75", dict(up=0.75 * up)), ("G04", "target_x1.5", dict(up=1.5 * up)),
            ("G05", "half_at_0.5tgt_be", dict(so=0.5 * up)),
            ("G06", f"clock_exit_{CLOCK[s]}", dict(xt=CLOCK[s])),
            ("G07", "timestop60_lt0.25", dict(tsb=12, tsr=0.25 * dn)),
            ("G08", "limit_entry_0.1", dict(lim=0.1 * dn)),
            ("G09", "next_bar_entry", dict(em=1)),
            ("G10", "index_veto_0.5", dict(keep="spy_not_crash" if SIDE[s] == 1 else "spy_not_chase")),
            ("G11", a, dict(keep=a)), ("G12", z, dict(keep=z)),
            ("G13", "skip_stock_dn_gt2", dict(keep="stock_not_crash")),
            g14,
            ("G15", "first5_per_session", dict(keep="first5_day")),
            ("G16", "cf_stopcost_le0.15", dict(keep="cf")),
            ("G17", "skip_spy_flat_0.10", dict(keep="spy_not_flat"))]


def grid_of(s):
    return grid_s(s)


def keep_mask(g, k, dn):
    tod = g["tod"].to_numpy(int)
    if k == "first_symday":
        return (g.groupby(["symbol", "date"]).cumcount() == 0).to_numpy()
    if k == "first5_day":
        o = g.sort_values(["date", "tod", "symbol"], kind="mergesort")
        c = o.groupby("date").cumcount()
        return (c.reindex(g.index) < 5).to_numpy()
    if k == "le1300":
        return tod <= 1300
    if k == "gt1300":
        return tod > 1300
    if k == "le1400":
        return tod <= 1400
    if k == "gt1400":
        return tod > 1400
    if k == "le1030":
        return tod <= 1030
    if k == "ge1030":
        return tod >= 1030
    if k == "spy_not_flat":
        sp = g["spy_fo"].to_numpy(float)
        return ~(np.abs(sp) <= 0.10)
    if k == "cf":
        px = g["close"].to_numpy(float)
        R = dn * 0.25 * g["atr_d"].to_numpy(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            cost = (2 * (0.01 + px * 1e-4) + 0.02) / R
        return cost <= CF_LIM
    return keep_1028(tod, g["spy_fo"].to_numpy(float), g["fromOpen"].to_numpy(float), k)


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
    key = fh[["symbol", "date", "tod"]].copy()
    key["date"] = pd.to_datetime(key["date"]).dt.date
    key["fhi"] = np.arange(len(fh))
    sg = sg.merge(key, on=["symbol", "date", "tod"], how="left")
    ok = sg["fhi"].notna().to_numpy()
    sg = sg[ok].reset_index(drop=True)
    rows = []
    for s in SETUPS:
        g = sg[sg.setup == s].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        if not len(g):
            continue
        side = SIDE[s]
        ent_all = fh2P[g["fhi"].to_numpy(np.int64)]
        for vid, knob, ov in grid_s(s):
            prm = {**EX0, **BASE[s], **ov}
            m = keep_mask(g, prm["keep"], BASE[s]["dn"])
            ent = ent_all[m].astype(np.int64)
            res = sim(*A, ent, 0.25 * atrP[np.maximum(ent, 0)], side, prm["up"], prm["dn"], prm["em"], prm["tsb"],
                      prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"], prm["lim"])
            r, mfe, mae, cd, et, xr = res
            sc = prm["dn"]
            t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": g["tod"].to_numpy(int)[m], "tod": et,
                              "r": r / sc, "mfe": mfe / sc, "mae": mae / sc, "code": cd,
                              "ctrl": g[CTRL[s]].to_numpy(float)[m], "spy_fo": g["spy_fo"].to_numpy(float)[m]})
            t["cache_r"] = g["r"].to_numpy(float)[m] if vid == "P" else np.nan
            t["setup"], t["var"], t["knob"] = s, vid, knob
            rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    out = out.astype({"setup": "category", "var": "category", "knob": "category", "symbol": "category",
                      "r": "float32", "cache_r": "float32", "mfe": "float32", "mae": "float32", "ctrl": "float32",
                      "spy_fo": "float32"})
    print(month, len(out), "unmatched", int((~ok).sum()), round(time.time() - t0), flush=True)
    return out


def main():
    from load import load_sig  # gates1021 cache loader (asserts no locked rows)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    S = load_sig(list(CACHED))
    S["month"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m")
    for k in ("c_long_t1s1", "c_short_t05s1", "c_long_t05s1"):
        if k not in S:
            S[k] = np.nan
    S = S[["setup", "symbol", "date", "tod", "spy_fo", "fromOpen", "close", "atr_d", "c_short_t1s1", "c_short_t05s1",
           "c_long_t05s1", "c_long_t1s1", "r", "month"]]
    print("signals by setup", S.groupby("setup").size().to_dict(), "cache r", S.groupby("setup").r.mean().round(4).to_dict(),
          flush=True)
    jobs = [(m, S[S.month == m].drop(columns="month")) for m in months]
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, jobs), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), exp=("r", "mean")).round(4).to_string())


if __name__ == "__main__":
    main()
