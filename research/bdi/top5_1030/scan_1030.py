"""top5_1030 step 3-4: execution variants of the 5 chosen live setups (PLAN.md, written before this was run).
Entries: gates1021's live-shaped signal rows for the 5 setups (rebuilt by build_cache.py into scratch). Exits: the
top5_1028 simulator (imported, unchanged), in 0.25-ATR units; r is divided by the row's stop multiple (same $ risk).
Locked block never loaded (lib.months() is open months only; asserts). Educational only - not financial advice.

    G21SCR=$SCRATCH/top5_1030/g python research/bdi/top5_1030/scan_1030.py   # -> $SCR/trades.parquet (scratch)
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
from scan_1019 import lib, build_paths, spy_fo  # noqa: E402
from scan_1028 import sim, keep_mask as keep_1028  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top5_1030")

SETUPS = ("L3-gap-slope-rsi5hi-FD", "MF5-flowsell-vwapup-rsi5hi-FD", "NS3-failed-vwap-reclaim-short-FD",
          "NS3V1-am-widestop-short", "NS1-rsidip-rsi5pop-long-FD")
SIDE = {"L3-gap-slope-rsi5hi-FD": -1, "MF5-flowsell-vwapup-rsi5hi-FD": -1, "NS3-failed-vwap-reclaim-short-FD": -1,
        "NS3V1-am-widestop-short": -1, "NS1-rsidip-rsi5pop-long-FD": 1}
CGEOM = {"L3-gap-slope-rsi5hi-FD": "t05s1", "MF5-flowsell-vwapup-rsi5hi-FD": "t1s1",
         "NS3-failed-vwap-reclaim-short-FD": "t1s1", "NS3V1-am-widestop-short": "t05s1",
         "NS1-rsidip-rsi5pop-long-FD": "t05s1"}  # cache geometry (parity)
GK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0)}
# live parent geometry in 0.25-ATR units (NS3V1: r_atr_frac 0.5 x t05s1 = target 0.25 ATR, stop 0.5 ATR)
BASE = {s: dict(zip(("up", "dn"), GK[CGEOM[s]])) for s in SETUPS}
BASE["NS3V1-am-widestop-short"] = dict(up=1.0, dn=2.0)
CTRL = {s: f"c_{'long' if SIDE[s] == 1 else 'short'}_{CGEOM[s]}" for s in SETUPS}
CTRL["NS3V1-am-widestop-short"] = "c_short_t1s1"  # no exact random column for t1s2 (disclosed)
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, lim=0.0, keep=None)


def grid_s(s):
    """PLAN.md section 3 (15 rows per setup, relative to the live parent)."""
    b = BASE[s]
    up, dn = b["up"], b["dn"]
    ns3v1 = s == "NS3V1-am-widestop-short"
    g = [("P", "parent", {}),
         ("G01", "stop_x1.5", dict(dn=1.5 * dn)), ("G02", "stop_x2.0", dict(dn=2.0 * dn)),
         ("G03", "target_x0.75", dict(up=0.75 * up)), ("G04", "target_x1.5", dict(up=1.5 * up)),
         ("G05", "half_at_0.5tgt_be", dict(so=0.5 * up)),
         ("G06", "clock_exit_1200", dict(xt=1200)),
         ("G07", "timestop60_lt0.25", dict(tsb=12, tsr=0.25 * dn)),
         ("G08", "limit_entry_0.1", dict(lim=0.1 * dn)),
         ("G09", "next_bar_entry", dict(em=1)),
         ("G10", "index_veto_0.5", dict(keep="spy_not_crash" if SIDE[s] == 1 else "spy_not_chase")),
         ("G11", "from1030" if ns3v1 else "until1130", dict(keep="from1030" if ns3v1 else "until1130")),
         ("G12", "until1030" if ns3v1 else "from1130", dict(keep="until1030" if ns3v1 else "from1130")),
         ("G13", "skip_stock_dn_gt2", dict(keep="stock_not_crash")),
         ("G14", "one_per_symbol_day", dict(keep="first_symday")),
         ("G15", "first5_per_session", dict(keep="first5_day"))]
    if ns3v1:
        g.insert(1, ("P0", "parity_cache_geom", dict(up=0.5, dn=1.0)))
    return g


def grid_of(s):
    return [x for x in grid_s(s) if x[0] != "P0"]


def keep_mask(g, k):
    tod = g["tod"].to_numpy(int)
    if k == "first_symday":
        return (g.groupby(["symbol", "date"]).cumcount() == 0).to_numpy()
    if k == "first5_day":
        o = g.sort_values(["date", "tod", "symbol"], kind="mergesort")
        c = o.groupby("date").cumcount()
        return (c.reindex(g.index) < 5).to_numpy()
    if k == "until1030":
        return tod < 1030
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
    key = key[fh["_fi"].to_numpy() >= 0]
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
            m = keep_mask(g, prm["keep"])
            ent = ent_all[m].astype(np.int64)
            res = sim(*A, ent, 0.25 * atrP[np.maximum(ent, 0)], side, prm["up"], prm["dn"], prm["em"], prm["tsb"],
                      prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"], prm["lim"])
            r, mfe, mae, cd, et, xr = res
            sc = prm["dn"]
            t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": g["tod"].to_numpy(int)[m], "tod": et,
                              "r": r / sc, "mfe": mfe / sc, "mae": mae / sc, "code": cd,
                              "ctrl": g[CTRL[s]].to_numpy(float)[m], "spy_fo": g["spy_fo"].to_numpy(float)[m]})
            t["cache_r"] = g["r"].to_numpy(float)[m] if vid in ("P0", "P") else np.nan
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
    S = load_sig(list(SETUPS))
    S["month"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m")
    S = S[["setup", "symbol", "date", "tod", "spy_fo", "fromOpen", "c_short_t1s1", "c_short_t05s1", "c_long_t05s1",
           "r", "month"]]
    print("signals by setup", S.groupby("setup").size().to_dict(), "cache r", S.groupby("setup").r.mean().round(4).to_dict(),
          flush=True)
    jobs = [(m, S[S.month == m].drop(columns="month")) for m in months]
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, jobs), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), exp=("r", "mean")).round(4).to_string())


if __name__ == "__main__":
    main()
