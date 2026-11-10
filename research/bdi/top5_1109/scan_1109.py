"""top5_1109 step 3-4: execution variants of the 5 chosen live setups (PLAN.md, written before this was run).
Entries: gates1021's live-shaped signal rows for the 5 setups (rebuilt by build_cache.py into scratch). W60 compass on
history from research/bdi/top20/compass_2y.py (env T20_SCRATCH/compass2y.parquet) for G17 / G18. Exits: the top5_1028 simulator (imported, unchanged), in 0.25-ATR units; r is divided by the row's stop multiple
(same $ risk). Locked block never loaded (lib.months() is open months only; asserts). Educational only - not financial
advice.

    G21SCR=/dev/shm/t5_1109/g T20_SCRATCH=<scratch>/t20_1109 python research/bdi/top5_1109/scan_1109.py   # -> $SCR/trades.parquet (scratch)
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
SCR = Path("/dev/shm/t5_1109")
G21 = Path(os.environ.get("G21SCR", str(SCR / "g")))

RW3S, EXH, RW1, ARAM, L3L = ("RW3S-gapdn-flowsell-short-FD", "exhaustion_short-FD", "RW1-gapdn-bounce-flowsell-short-FD",
                             "NM-AR-AM-gapdown-capitulation-long", "L3-gap-slope-lowdist-FD")
CACHED = (RW3S, EXH, RW1, ARAM, L3L)
SETUPS = CACHED
SIDE = {RW3S: -1, EXH: -1, RW1: -1, ARAM: 1, L3L: -1}
GEOM = {s: "t1s1" for s in SETUPS}
GK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0)}
BASE = {s: dict(zip(("up", "dn"), GK[GEOM[s]])) for s in SETUPS}
CTRL = {s: f"c_{'long' if SIDE[s] == 1 else 'short'}_{GEOM[s]}" for s in SETUPS}
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, lim=0.0, keep=None)
CLOCK = {RW3S: 1200, RW1: 1200, EXH: 1430, L3L: 1400, ARAM: 1300}
SPLIT = {RW3S: ("le1030", "ge1030"), EXH: ("le1300", "gt1300"), RW1: ("le1300", "gt1300"), L3L: ("until1130", "from1130"),
         ARAM: ("le1050", "ge1055")}
CF_LIM = 0.15
MIN_ADV = {RW3S: 95e6, EXH: 95e6, RW1: 95e6, ARAM: 95e6, L3L: 0.0}


def grid_s(s):
    """top5_1109 PLAN.md section 3 (19 rows per setup, relative to the live parent)."""
    b = BASE[s]
    up, dn = b["up"], b["dn"]
    a, z = SPLIT[s]
    g19 = ("G19", "adv_ge95M", dict(keep="adv_ge95")) if MIN_ADV[s] == 0 else ("G19", "adv_floor_x1.2", dict(keep="adv_x12"))
    return [("P", "parent", {}),
            ("G01", "stop_x1.5", dict(dn=1.5 * dn)), ("G02", "stop_x0.75", dict(dn=0.75 * dn)),
            ("G03", "target_x0.75", dict(up=0.75 * up)), ("G04", "target_x1.5", dict(up=1.5 * up)),
            ("G05", "half_at_0.5tgt_be", dict(so=0.5 * up)),
            ("G06", "timestop30_lt0.25", dict(tsb=6, tsr=0.25 * dn)),
            ("G07", "timestop60_lt0.25", dict(tsb=12, tsr=0.25 * dn)),
            ("G08", f"clock_exit_{CLOCK[s]}", dict(xt=CLOCK[s])),
            ("G09", "limit_entry_0.1", dict(lim=0.1 * dn)),
            ("G10", "next_bar_entry", dict(em=1)),
            ("G11", a, dict(keep=a)), ("G12", z, dict(keep=z)),
            ("G13", "cf_stopcost_le0.15", dict(keep="cf")),
            ("G14", "skip_price_lt20", dict(keep="px_ge20")),
            ("G15", "first5_per_session", dict(keep="first5_day")),
            ("G16", "spy_side_filter", dict(keep="spyup" if SIDE[s] == 1 else "spydn")),
            ("G17", "skip_against_compass", dict(keep="not_against")),
            ("G18", "half_size_against_compass", dict(wt="against")),
            g19]


def grid_of(s):
    return grid_s(s)


def against(g):
    c = g["comp"].to_numpy(float)
    return (c == -2) if SIDE[g["setup"].iloc[0]] == 1 else (c == 2)


def keep_mask(g, k, dn):
    tod = g["tod"].to_numpy(int)
    if k is None:
        return np.ones(len(g), bool)
    if k == "first5_day":
        o = g.sort_values(["date", "tod", "symbol"], kind="mergesort")
        c = o.groupby("date").cumcount()
        return (c.reindex(g.index) < 5).to_numpy()
    if k == "le1300":
        return tod <= 1300
    if k == "gt1300":
        return tod > 1300
    if k == "le1030":
        return tod <= 1030
    if k == "ge1030":
        return tod >= 1030
    if k == "le1050":
        return tod <= 1050
    if k == "ge1055":
        return tod >= 1055
    if k == "px_ge20":
        return g["close"].to_numpy(float) >= 20
    if k == "adv_x12":
        return g["adv20"].to_numpy(float) >= 1.2 * MIN_ADV[g["setup"].iloc[0]]
    if k == "adv_ge95":
        return g["adv20"].to_numpy(float) >= 95e6
    if k == "not_against":
        return ~against(g)
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
    fi = sg["fhi"].to_numpy(np.int64)
    for c in ("adv20",):
        sg[c] = fh[c].to_numpy(float)[fi]
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
            w = np.where(against(g)[m], 0.5, 1.0) if prm.get("wt") == "against" else 1.0
            t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": g["tod"].to_numpy(int)[m], "tod": et,
                              "r": r / sc * w, "mfe": mfe / sc * w, "mae": mae / sc * w, "code": cd,
                              "ctrl": g[CTRL[s]].to_numpy(float)[m], "spy_fo": g["spy_fo"].to_numpy(float)[m],
                              "comp": g["comp"].to_numpy(float)[m]})
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
    S = S[["setup", "symbol", "date", "tod", "spy_fo", "fromOpen", "close", "atr_d", "c_short_t1s1", "c_long_t1s1", "r", "month"]]
    C = pd.read_parquet(Path(os.environ["T20_SCRATCH"]) / "compass2y.parquet")
    C = C.astype({"T": "int64"}).sort_values("T")
    S["_m"] = ((S.tod // 100) * 60 + S.tod % 100).astype("int64")
    S["dkey"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m-%d")
    S["_i"] = np.arange(len(S))
    mm = pd.merge_asof(S[["_i", "dkey", "_m"]].sort_values("_m"), C.rename(columns={"date": "dkey", "T": "_m"}),
                       on="_m", by="dkey", direction="backward").set_index("_i").w60
    S["comp"] = mm.reindex(S._i).to_numpy()
    S = S.drop(columns=["_m", "dkey", "_i"])
    print("signals by setup", S.groupby("setup").size().to_dict(), "cache r", S.groupby("setup").r.mean().round(4).to_dict(),
          "compass coverage", round(float(S.comp.notna().mean()), 4), flush=True)
    jobs = [(m, S[S.month == m].drop(columns="month")) for m in months]
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, jobs), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), exp=("r", "mean")).round(4).to_string())


if __name__ == "__main__":
    main()
