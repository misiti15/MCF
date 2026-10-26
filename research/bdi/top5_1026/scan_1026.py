"""top5_1026 step 3-4: execution variants of the 5 chosen live setups (PLAN.md, written before this was run).
CWT14 pdl-p05-long: top5_1019 kernels + per-variant random control. NS3-FD / MF2-FD / MF4-FD / L3-rsi5hi-FD:
gates1021's cached live-shaped signal rows (as top5_1022). Exits: a copy of the top5_1019 simulator with a limit-entry
mode and a clock exit that only applies to trades opened before it. Locked block never loaded (lib.months() is open
months only; asserts). Educational only - not financial advice.

    python research/bdi/top5_1026/scan_1026.py      # -> $SCR/trades.parquet (scratch, deleted after the report)
"""
from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1019"), str(ROOT / "research" / "bdi" / "gates1021" / "scripts")]
from scan_1019 import lib, build_paths, spy_fo, next_after, S5, S6, CL, _mult  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/t5tune1026")
SEED = 20261026
K_CTRL = 5

PDL05 = "CWT14-failbrk-pdl-p05-long"
NS3, MF2, MF4, L3R = ("NS3-failed-vwap-reclaim-short-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD",
                      "L3-gap-slope-rsi5hi-FD")
CWT = {PDL05: dict(level="PD", p=0.05, vr=np.inf, side=1)}
SHORTS = (NS3, MF2, MF4, L3R)
SETUPS = (PDL05,) + SHORTS
GEOM = {NS3: "t1s1", MF2: "t1s05", MF4: "t05s1", L3R: "t05s1"}
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, lim=0.0, keep=None, kind="std")

GRID_C = [("P", "parent_t05s1_so0.25", {}),
          ("C01", "stop_x150", dict(dn=1.5)), ("C02", "stop_x200", dict(dn=2.0)),
          ("C03", "target0.35", dict(up=0.35)), ("C04", "target0.75", dict(up=0.75)),
          ("C05", "timestop15_lt0.1", dict(tsb=3, tsr=0.1)), ("C06", "timestop90_lt0.25", dict(tsb=18, tsr=0.25)),
          ("C07", "clock_exit_1400", dict(xt=1400)), ("C08", "until1300", dict(keep="until1300")),
          ("C09", "skip0950_0959", dict(keep="from1000")), ("C10", "skip1000_1029", dict(keep="skip1000")),
          ("C11", "skip_spy_dn_gt0.5", dict(keep="spy_not_crash")), ("C12", "skip_stock_dn_gt2", dict(keep="stock_not_crash")),
          ("C13", "reentry_cd15", dict(kind="reentry")), ("C14", "limit_entry_0.1R", dict(lim=0.1)),
          ("C15", "skip1030_1129", dict(keep="skip1030_1129")), ("C16", "skip_spy_up_gt0.5", dict(keep="spy_not_chase"))]


def grid_s(s):
    t05 = GEOM[s] == "t05s1"
    g = [("P", "parent_" + GEOM[s], {}),
         ("E01", "timestop30_lt0.2", dict(tsb=6, tsr=0.2)), ("E02", "timestop60_lt0.25", dict(tsb=12, tsr=0.25)),
         ("E03", "stop_x085", dict(dn=0.85)), ("E04", "stop_x125", dict(dn=1.25)), ("E05", "stop_x150", dict(dn=1.5)),
         ("E06", "scale_half_0.25_be" if t05 else "scale_half_0.5_be", dict(so=0.25 if t05 else 0.5)),
         ("E07", "be_after_0.25" if t05 else "be_after_0.5", dict(be=0.25 if t05 else 0.5)),
         ("E08", "target0.35" if t05 else "target0.75", dict(up=0.35 if t05 else 0.75)),
         ("E09", "target0.75" if t05 else "target1.5", dict(up=0.75 if t05 else 1.5)),
         ("E10", "wait1", dict(em=2)),
         ("E11", "from1030", dict(keep="from1030")), ("E12", "until1300", dict(keep="until1300")),
         ("E13", "skip1000_1029", dict(keep="skip1000")), ("E14", "skip_spy_up", dict(keep="spydn")),
         ("E15", "timestop15_lt0.1", dict(tsb=3, tsr=0.1)), ("E16", "clock_exit_1400", dict(xt=1400)),
         ("E17", "limit_entry_0.1", dict(lim=0.1))]
    if s == NS3:
        g.append(("E18", "from1130", dict(keep="from1130")))
    if s == MF4:
        g.append(("E18", "until1130", dict(keep="until1130")))
    return g


BASE = {PDL05: dict(side=1, up=0.5, dn=1.0, so=0.25), NS3: dict(side=-1, up=1.0, dn=1.0),
        MF2: dict(side=-1, up=1.0, dn=0.5), MF4: dict(side=-1, up=0.5, dn=1.0), L3R: dict(side=-1, up=0.5, dn=1.0)}


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, tierP, ent, Rv, side, up, dn, em, tsb, tsr, be, so, sof, xt, lim):
    """top5_1019 sim (stop first) + lim > 0: limit entry lim*R better than the signal close, valid on the next bar only
    (that bar is checked for the stop, never for the target); + the clock exit xt applies only to trades opened before
    xt; all costs x tierP[signal row] (3 on the extended tier: |gap| >= 20% or price < $5).
    Codes: 1 target, 2 stop, 3 moved stop, 4 time stop, 5 clock exit, 6 flatten 15:55. r in units of R."""
    n = len(ent)
    r = np.full(n, np.nan)
    mfe_o = np.full(n, np.nan)
    mae_o = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    etod = np.zeros(n, np.int32)
    xrow = np.full(n, -1, np.int64)
    for q in range(n):
        i = ent[q]
        R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]
        j = -1
        e = 0.0
        if lim > 0:
            if i + 1 > end:
                continue
            lp = c[i] - side * lim * R
            adv0 = l[i + 1] if side == 1 else h[i + 1]
            if side * (adv0 - lp) > 0:
                continue  # not filled
            j, e = i + 1, lp
        elif em == 0:
            j, e = i, c[i]
        elif i + 1 <= end:
            j, e = i + 1, c[i + 1]
        if j < 0:
            continue
        ec = (0.01 + e * 1e-4) * _mult(tod[j])
        stop = e - side * dn * R
        tgt = e + side * up * R
        spx = e + side * so * R
        scaled = False
        mfe, mae = 0.0, 0.0
        x, cd, xr = 0.0, 0, -1
        if lim > 0:
            adv0 = l[j] if side == 1 else h[j]
            mae = min(mae, side * (adv0 - e) / R)
            if side * (adv0 - stop) <= 0:
                x, cd, xr = stop, 2, j
        clock = tod[j] < xt
        if cd == 0:
            for k in range(j + 1, end + 1):
                if clock and tod[k] > xt:
                    x, cd, xr = c[k - 1], 5, k - 1
                    break
                adv = l[k] if side == 1 else h[k]
                fav = h[k] if side == 1 else l[k]
                mae = min(mae, side * (adv - e) / R)
                if side * (adv - stop) <= 0:
                    x, xr = stop, k
                    cd = 2 if side * (stop - e) < -0.999 * dn * R else 3
                    break
                mfe = max(mfe, side * (fav - e) / R)
                if side * (fav - tgt) >= 0:
                    x, cd, xr = tgt, 1, k
                    break
                if tsb > 0 and (k - j) >= tsb and mfe < tsr:
                    x, cd, xr = c[k], 4, k
                    break
                if be > 0 and mfe >= be:
                    stop = max(stop, e) if side == 1 else min(stop, e)
                if so > 0 and not scaled and side * (fav - spx) >= 0:
                    scaled = True
                    stop = max(stop, e) if side == 1 else min(stop, e)
        if cd == 0:
            x, cd, xr = c[end], 6, end
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if (cd == 2 or cd == 3) else 0.0))
        g = side * (x - e) / R
        if scaled:
            g = sof * so + (1 - sof) * g
            xc = (1 - sof) * xc
        r[q] = g - tierP[i] * (ec + xc) / R
        mfe_o[q], mae_o[q], code[q], etod[q], xrow[q] = mfe, mae, cd, tod[j], xr
    return r, mfe_o, mae_o, code, etod, xrow


def keep_mask(tod, spy, sfo, k):
    with np.errstate(invalid="ignore"):
        if k is None:
            return np.ones(len(tod), bool)
        if k == "from1030":
            return tod >= 1030
        if k == "from1000":
            return tod >= 1000
        if k == "until1300":
            return tod <= 1300
        if k == "until1400":
            return tod <= 1400
        if k == "until1130":
            return tod < 1130
        if k == "from1130":
            return tod >= 1130
        if k == "skip1030_1129":
            return ~((tod >= 1030) & (tod < 1130))
        if k == "spy_not_chase":
            return ~(spy > 0.5)
        if k == "skip1000":
            return ~((tod >= 1000) & (tod < 1030))
        if k == "spydn":
            return ~(spy > 0)
        if k == "spy_not_crash":
            return ~(spy < -0.5)
        if k == "stock_not_crash":
            return ~(sfo < -2.0)
    raise ValueError(k)


def simrun(A, ent, Rv, side, prm):
    h, l, c, tod, dend, tierP = A
    return sim(h, l, c, tod, dend, tierP, ent.astype(np.int64), Rv, side, prm["up"], prm["dn"], prm["em"], prm["tsb"],
               prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"], prm["lim"])


def frame(s, vid, knob, dat, sym, ent, tod_sig, res, scale, ctrl, spyv, split=None):
    r, mfe, mae, cd, et, xr = res
    t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": tod_sig, "tod": et, "r": r / scale,
                      "mfe": mfe, "mae": mae, "code": cd, "ctrl": ctrl, "spy_fo": spyv})
    t["setup"], t["var"], t["knob"] = s, vid, knob
    return t


def month_job(args):
    month, sg = args
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    spy = spy_fo(f, fh)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P))
    tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    A = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32),
         dend, tierP)
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    rows = []
    # ---- CWT14 longs
    x = CL.arrays(fh)
    lev = S6.levels(x)
    pool = S5.ctrl_pool(P, 95e6)
    S5.K_CTRL = K_CTRL
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    ftod = fh["tod"].to_numpy()
    sfo = fh["fromOpen"].to_numpy(float) if "fromOpen" in fh else np.full(len(fh), np.nan)
    with np.errstate(invalid="ignore"):
        base = (ftod >= 950) & (ftod <= 1500) & (fh["adv20"].fillna(0).to_numpy() >= 95e6) & (fh["atr_d"].to_numpy(float) > 0)
    for s, d in CWT.items():
        with np.errstate(invalid="ignore"):
            m0 = np.asarray(S6.b3_any(x, lev[(d["level"], d["side"])], d, d["p"]), bool) & base
        for vid, knob, ov in GRID_C:
            prm = {**EX0, **BASE[s], **ov}
            sig = m0 & keep_mask(ftod, spy, sfo, prm["keep"])
            e1 = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fh["date"].to_numpy(), sig)
            ent = fh2P[e1]
            Rv = 0.25 * atrP[np.maximum(ent, 0)]
            res = simrun(A, ent, Rv, 1, prm)
            if prm["kind"] == "reentry":
                allrows = np.sort(fh2P[np.flatnonzero(sig)])
                nx = next_after(allrows, res[5], dend, 3)
                ent2 = nx[nx >= 0]
                res2 = simrun(A, ent2, 0.25 * atrP[ent2], 1, prm)
                ent = np.r_[ent, ent2]
                Rv = np.r_[Rv, 0.25 * atrP[ent2]]
                res = tuple(np.r_[a, b] for a, b in zip(res, res2))
            cr = S5.ctrl_rows(pool, ent, rng)
            cr_r = np.full(cr.shape, np.nan)
            for k in range(K_CTRL):
                rk = cr[:, k]
                Rc = np.where(rk >= 0, 0.25 * atrP[np.maximum(rk, 0)], np.nan)
                cr_r[:, k] = simrun(A, rk, Rc, 1, prm)[0]
            cnt = np.isfinite(cr_r).sum(1)
            ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan) / prm["dn"]
            spyP = np.full(len(P), np.nan)
            spyP[fh2P] = spy
            rows.append(frame(s, vid, knob, dat, sym, ent, A[3][ent], res, prm["dn"], ctrl, spyP[ent]))
    # ---- cached short setups
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
        ent_all = fh2P[g["fhi"].to_numpy(np.int64)]
        gt = g["tod"].to_numpy(int)
        gsfo = g["fromOpen"].to_numpy(float)
        for vid, knob, ov in grid_s(s):
            prm = {**EX0, **BASE[s], **ov}
            m = keep_mask(gt, g["spy_fo"].to_numpy(float), gsfo, prm["keep"])
            ent = ent_all[m]
            res = simrun(A, ent, 0.25 * atrP[np.maximum(ent, 0)], -1, prm)
            fr = frame(s, vid, knob, dat, sym, ent, gt[m], res, prm["dn"],
                       g["c_short_" + GEOM[s]].to_numpy(float)[m], g["spy_fo"].to_numpy(float)[m])
            fr["cache_r"] = g["r"].to_numpy(float)[m] if vid == "P" else np.nan
            rows.append(fr)
    out = pd.concat(rows, ignore_index=True)
    out = out.astype({"setup": "category", "var": "category", "knob": "category", "symbol": "category",
                      "r": "float32", "cache_r": "float32", "mfe": "float32", "mae": "float32", "ctrl": "float32", "spy_fo": "float32"})
    print(month, len(out), "short unmatched", int((~ok).sum()), round(time.time() - t0), flush=True)
    return out


def main():
    from load import load_sig  # gates1021 cache loader (asserts no locked rows)
    SCR.mkdir(parents=True, exist_ok=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    S = load_sig(list(SHORTS))
    S["month"] = pd.to_datetime(S["date"]).dt.strftime("%Y-%m")
    S = S[["setup", "symbol", "date", "tod", "spy_fo", "fromOpen", "c_short_t1s1", "c_short_t1s05", "c_short_t05s1", "r", "month"]]
    print("spy_fo quantiles", S.spy_fo.quantile([.05, .5, .95]).round(3).tolist(), "cached r mean by setup",
          S.groupby("setup").r.mean().round(4).to_dict(), flush=True)
    jobs = [(m, S[S.month == m].drop(columns="month")) for m in months]
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, jobs), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), exp=("r", "mean")).round(4).to_string())


if __name__ == "__main__":
    main()
