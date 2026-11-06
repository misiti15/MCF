"""top5_1106 step 3-4: execution variants of the 5 chosen live setups (PLAN.md, written before this was run).
Entries: gates1021's live-shaped signal rows for 4 setups (rebuilt by build_cache.py into scratch) + a CWT13 kernel
(cwt_live_lib.b2 on the lab frame with its 09:35-09:45 head rows, first signal per symbol-day in 11:00-15:00, ADV >=
95M). Exits: the top5_1028 simulator (imported, unchanged), in 0.25-ATR units; r is divided by the row's stop multiple
(same $ risk). Locked block never loaded (lib.months() is open months only; asserts). Educational only - not financial
advice.

    G21SCR=/dev/shm/t5_1106/g python research/bdi/top5_1106/scan_1106.py   # -> $SCR/trades.parquet (scratch)
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
SCR = Path("/dev/shm/t5_1106")
G21 = Path(os.environ.get("G21SCR", str(SCR / "g")))

CWT13 = "CWT13-vwapstretch-z05-long"
CACHED = ("NM-HL-T75-pm-long", "exhaustion_short", "MF4-h40-open-flowsell-FD", "NS3-failed-vwap-reclaim-short")
SETUPS = (CWT13,) + CACHED
SIDE = {CWT13: 1, "NM-HL-T75-pm-long": 1, "exhaustion_short": -1, "MF4-h40-open-flowsell-FD": -1,
        "NS3-failed-vwap-reclaim-short": -1}
GEOM = {CWT13: "t05s1", "NM-HL-T75-pm-long": "t05s1", "exhaustion_short": "t1s1", "MF4-h40-open-flowsell-FD": "t05s1",
        "NS3-failed-vwap-reclaim-short": "t1s1"}
GK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0)}
BASE = {s: dict(zip(("up", "dn"), GK[GEOM[s]])) for s in SETUPS}
CTRL = {s: f"c_{'long' if SIDE[s] == 1 else 'short'}_{GEOM[s]}" for s in SETUPS}
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, lim=0.0, keep=None)
CLOCK = {CWT13: 1400, "NM-HL-T75-pm-long": 1430, "exhaustion_short": 1430, "MF4-h40-open-flowsell-FD": 1200,
         "NS3-failed-vwap-reclaim-short": 1100}
SPLIT = {CWT13: ("le1300", "gt1300"), "NM-HL-T75-pm-long": ("le1400", "gt1400"), "exhaustion_short": ("le1400", "gt1400"),
         "MF4-h40-open-flowsell-FD": ("until1130", "from1130"), "NS3-failed-vwap-reclaim-short": ("until1030", "from1030")}
CF_LIM = 0.15
MIN_ADV = {CWT13: 95e6, "NM-HL-T75-pm-long": 125e6, "exhaustion_short": 95e6, "MF4-h40-open-flowsell-FD": 95e6,
           "NS3-failed-vwap-reclaim-short": 95e6}


def grid_s(s):
    """top5_1106 PLAN.md section 3 (18 rows per setup, relative to the live parent)."""
    b = BASE[s]
    up, dn = b["up"], b["dn"]
    a, z = SPLIT[s]
    g18 = ("G18", "one_per_symbol_day", dict(keep="first_symday")) if s == "exhaustion_short" else \
        ("G18", "adv_floor_x1.2", dict(keep="adv_x12"))
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
            ("G13", "flush_chase_guard_0.15", dict(keep="not_chase_extreme")),
            ("G14", "cf_stopcost_le0.15", dict(keep="cf")),
            ("G15", "skip_price_lt20", dict(keep="px_ge20")),
            ("G16", "spy_side_filter", dict(keep="spyup" if SIDE[s] == 1 else "spydn")),
            ("G17", "first5_per_session", dict(keep="first5_day")),
            g18]


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
    if k == "until1030":
        return tod < 1030
    if k == "px_ge20":
        return g["close"].to_numpy(float) >= 20
    if k == "adv_x12":
        return g["adv20"].to_numpy(float) >= 1.2 * MIN_ADV[g["setup"].iloc[0]]
    if k == "not_chase_extreme":
        col = "dist_hod_atr" if SIDE[g["setup"].iloc[0]] == 1 else "dist_lod_atr"
        v = g[col].to_numpy(float)
        return ~(v <= 0.15)   # NaN (no frame value) is kept
    if k == "from1030":
        return tod >= 1030
    if k == "cf":
        px = g["close"].to_numpy(float)
        R = dn * 0.25 * g["atr_d"].to_numpy(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            cost = (2 * (0.01 + px * 1e-4) + 0.02) / R
        return cost <= CF_LIM
    return keep_1028(tod, g["spy_fo"].to_numpy(float), g["fromOpen"].to_numpy(float), k)


def _g21_prod_r_tier():
    import importlib.util
    spec = importlib.util.spec_from_file_location("g21scan", ROOT / "research/bdi/gates1021/scripts/scan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.prod_r_tier


def cwt13_rows(f, fh, spyv, month):
    """CWT13 kernel: live module rule (b2 z0.5 long) over head + frame rows; window / ADV / first per symbol-day."""
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.asarray(CL.b2(fh, z=0.5, side="long"), bool)
        tod = fh["tod"].to_numpy(int)
        ok = m & (tod >= 1100) & (tod <= 1500) & (fh["adv20"].fillna(0).to_numpy(float) >= 95e6) \
            & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(fh["r_long_t05s1"].to_numpy(float))
    idx = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fh["date"].to_numpy(), ok)
    prod_r_tier = _g21_prod_r_tier()  # gates1021 production R (tod costs, x3 extended tier)
    g = pd.DataFrame({"setup": CWT13, "symbol": fh["symbol"].to_numpy()[idx], "tod": tod[idx],
                      "spy_fo": spyv[idx], "fromOpen": fh["fromOpen"].to_numpy(float)[idx],
                      "close": fh["close"].to_numpy(float)[idx], "atr_d": fh["atr_d"].to_numpy(float)[idx],
                      "r": prod_r_tier(fh, idx, "long", "t05s1")})
    g["date"] = pd.to_datetime(fh["date"].to_numpy()[idx]).date
    c = pd.read_parquet(G21 / "ctrl" / f"{month}.parquet")
    c["date"] = pd.to_datetime(c["date"]).dt.date
    g = g.merge(c[["date", "tod", "c_long_t05s1"]], on=["date", "tod"], how="left")
    for k in ("c_short_t1s1", "c_short_t05s1", "c_long_t1s1"):
        g[k] = np.nan
    return g


def month_job(args):
    month, sg = args
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    spyv = spy_fo(f, fh)
    cw = cwt13_rows(f, fh, spyv, month)
    sg = pd.concat([sg, cw[sg.columns]], ignore_index=True)
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
    for c in ("dist_lod_atr", "dist_hod_atr", "adv20"):
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
    print(month, len(out), "unmatched", int((~ok).sum()), "cwt13", len(cw), round(time.time() - t0), flush=True)
    return out


def main():
    from load import load_sig  # gates1021 cache loader (asserts no locked rows)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    S = load_sig(list(CACHED))
    S["month"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m")
    for k in ("c_long_t1s1",):
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
