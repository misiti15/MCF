"""bdi1027: ideas A (Leaders on the Index Reclaim, long) and B (CWT14 pdl longs by QQQ low age) on the open two-year
history, as declared in PLAN.md. Reuses research/bdi/top5_1019/scan_1019.py unchanged (build_paths, sim, CWT14 kernels)
and top5_1015 random-control pools. Locked block never loaded.  Usage: python scan_1027.py [month ...]
Educational only - not financial advice."""
from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/bdi/top5_1019")
import scan_1019 as S  # noqa: E402
from scan_1019 import CL, S5, S6, lib, gates, sim, build_paths  # noqa: E402

OUT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1027")
SEED = 20261027
K = 5
GEOM = {"hold": (99.0, 1.0), "t1s1": (1.0, 1.0), "t2s1": (2.0, 1.0), "t05s1": (0.5, 1.0)}
A_CFG = [(d, k, g) for d in (0.20, 0.40) for k in (0.5, 1.0) for g in ("hold", "t1s1", "t2s1")]
B_SET = {"CWT14-failbrk-pdl-p10-long": S.CWT14[S.PDL10], "CWT14-failbrk-pdl-p05-lowvol-long": S.CWT14[S.PDL05V]}


def qqq_state(fh, month):
    """Per fh row: qqq_fo, running min of qqq_fo since 09:50 and the age (bars) of that min, from the lab context."""
    c = lib.load_context(month)[["date", "tod", "qqq_fo"]].sort_values(["date", "tod"]).reset_index(drop=True)
    c = c[c.tod >= 950].reset_index(drop=True)
    mins, ages = np.empty(len(c)), np.empty(len(c))
    for _, g in c.groupby("date", sort=False):
        idx = g.index.to_numpy(); v = g.qqq_fo.to_numpy(float)
        m, at = np.inf, 0
        for j, x in enumerate(v):
            if np.isfinite(x) and x <= m:
                m, at = x, j
            mins[idx[j]], ages[idx[j]] = m, j - at
    c["qmin"], c["qage"] = mins, ages
    return fh[["date", "tod"]].merge(c, on=["date", "tod"], how="left")


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    q = qqq_state(fh, month)
    qfo, qmin, qage = (q[k].to_numpy(float) for k in ("qqq_fo", "qmin", "qage"))
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float),
                    P["tod"].to_numpy(np.int32))
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    pool = S5.ctrl_pool(P, 95e6)
    S5.K_CTRL = K
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    ftod = fh["tod"].to_numpy()
    fdate = fh["date"].to_numpy()
    g = lambda k: fh[k].to_numpy(float)  # noqa: E731
    with np.errstate(invalid="ignore"):
        liquid = (g("adv20") >= 95e6) & (g("atr_d") > 0)
    rows = []

    def run(ent_fh, up, dn, tag):
        ent = fh2P[ent_fh]
        ent = ent[ent >= 0]
        Rv = 0.25 * atrP[ent]
        nan = np.full(len(ent), np.nan)
        r, mfe, mae, cd, et, xr = sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, nan, 1, up, dn, 0, 0, 0.0, 0.0,
                                      0.0, 0.5, 1555)
        cr = S5.ctrl_rows(pool, ent, rng)
        cr_r = np.full(cr.shape, np.nan)
        for kk in range(K):
            rk = cr[:, kk]
            Rc = np.where(rk >= 0, 0.25 * atrP[np.maximum(rk, 0)], np.nan)
            cr_r[:, kk] = sim(h, l, c, tod, dend, rk.astype(np.int64), Rc, np.full(len(rk), np.nan), 1, up, dn, 0, 0,
                              0.0, 0.0, 0.0, 0.5, 1555)[0]
        cnt = np.isfinite(cr_r).sum(1)
        ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
        t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": tod[ent], "r": r, "mfe": mfe, "mae": mae,
                          "code": cd, "ctrl": ctrl, "filled": np.isfinite(r)})
        t["cfg"] = tag
        rows.append(t)

    # ---- idea A: Leaders on the Index Reclaim
    with np.errstate(invalid="ignore"):
        rs = g("fromOpen") - qfo
        above = g("vwapDistPct") > 0
        inwin = (ftod >= 1000) & (ftod <= 1300)
    for d in (0.20, 0.40):
        trig_ok = inwin & (qfo >= 0) & (qmin <= -d)
        # first trigger bar per date (same for all symbols): the min tod with trig_ok per date
        td = pd.DataFrame({"date": fdate[trig_ok], "tod": ftod[trig_ok]}).groupby("date").tod.min()
        first = pd.Series(fdate).map(td).to_numpy()
        is_trig = trig_ok & (ftod == first)
        for k in (0.5, 1.0):
            sig = is_trig & liquid & above & (rs >= k)
            e1 = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fdate, sig)
            for geo in ("hold", "t1s1", "t2s1"):
                up, dn = GEOM[geo]
                run(e1, up, dn, f"A|d{d:.2f}|k{k:.1f}|{geo}")
    # ---- idea B: CWT14 pdl longs by QQQ low age
    x = CL.arrays(fh)
    lev = S6.levels(x)
    with np.errstate(invalid="ignore"):
        bok = (ftod >= 950) & (ftod <= 1500) & liquid
        for s, dd in B_SET.items():
            m = np.asarray(S6.b3_any(x, lev[(dd["level"], dd["side"])], dd, dd["p"]), bool) & bok
            e_par = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fdate, m)
            run(e_par, 0.5, 1.0, f"B|{s}|parent")
            for a in (3, 6):
                ma = m & (qage >= a)
                run(gates.first_per_symbol_day(fh["symbol"].to_numpy(), fdate, ma), 0.5, 1.0, f"B|{s}|age{a}")
    out = pd.concat(rows, ignore_index=True)
    out["cfg"] = out["cfg"].astype("category")
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    months = sys.argv[1:] or lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, months), ignore_index=True)
    name = "trades.parquet" if len(months) > 1 else f"trades_{months[0]}.parquet"
    T.to_parquet(OUT / name, index=False)
    print(T[T.filled].groupby("cfg", observed=True).agg(n=("r", "size"), exp=("r", "mean"), ctrl=("ctrl", "mean")).round(4).to_string())
