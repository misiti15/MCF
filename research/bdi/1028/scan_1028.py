"""bdi1028: Leader / Laggard Spread (BDI1028-LLS) on the open two-year history, as declared in PLAN.md. Reuses
research/bdi/top5_1019/scan_1019.py unchanged (build_paths, sim) and the top5_1015 same-minute random-control pool.
Locked block never loaded.  Usage: python scan_1028.py [month ...]     Educational only - not financial advice."""
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
import scan_1019 as S  # noqa: E402,F401
from scan_1019 import S5, lib, sim, build_paths  # noqa: E402

OUT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1028")
SEED = 20261028
K = 5
GEOM = {"hold": (99.0, 1.0), "t1s1": (1.0, 1.0)}
CFG = [(T, N, g) for T in (1030, 1200) for N in (5, 10) for g in ("hold", "t1s1")]


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    ctx = lib.load_context(month)[["date", "tod", "qqq_fo"]]
    q = fh[["date", "tod"]].merge(ctx.drop_duplicates(["date", "tod"]), on=["date", "tod"], how="left")
    qfo = q["qqq_fo"].to_numpy(float)
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float),
                    P["tod"].to_numpy(np.int32))
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    pool = S5.ctrl_pool(P, 95e6)
    S5.K_CTRL = K
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    g = lambda k: fh[k].to_numpy(float)  # noqa: E731
    ftod = fh["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        liquid = (g("adv20") >= 95e6) & (g("atr_d") > 0) & (fh2P >= 0)
        rs = g("fromOpen") - qfo
        vd = g("vwapDistPct")
    rows = []

    def run(ent_fh, side, up, dn, tag):
        ent = fh2P[ent_fh]
        Rv = 0.25 * atrP[ent]
        nan = np.full(len(ent), np.nan)
        r = sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, nan, side, up, dn, 0, 0, 0.0, 0.0, 0.0, 0.5, 1555)[0]
        cr = S5.ctrl_rows(pool, ent, rng)
        cr_r = np.full(cr.shape, np.nan)
        for kk in range(K):
            rk = cr[:, kk]
            Rc = np.where(rk >= 0, 0.25 * atrP[np.maximum(rk, 0)], np.nan)
            cr_r[:, kk] = sim(h, l, c, tod, dend, rk.astype(np.int64), Rc, np.full(len(rk), np.nan), side, up, dn,
                              0, 0, 0.0, 0.0, 0.0, 0.5, 1555)[0]
        cnt = np.isfinite(cr_r).sum(1)
        ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
        rows.append(pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "side": side, "r": r, "ctrl": ctrl,
                                  "filled": np.isfinite(r), "cfg": tag}))

    for T in (1030, 1200):
        base = liquid & (ftod == T) & np.isfinite(rs) & np.isfinite(vd)
        idx = np.flatnonzero(base)
        d = pd.DataFrame({"i": idx, "date": fh["date"].to_numpy()[idx], "rs": rs[idx], "vd": vd[idx]})
        for N in (5, 10):
            L = d[d.vd > 0].sort_values("rs", ascending=False).groupby("date").head(N)
            Sh = d[d.vd < 0].sort_values("rs", ascending=True).groupby("date").head(N)
            for geo in ("hold", "t1s1"):
                up, dn = GEOM[geo]
                tag = f"LLS|T{T}|N{N}|{geo}"
                run(L.i.to_numpy(), 1, up, dn, tag)
                run(Sh.i.to_numpy(), -1, up, dn, tag)
    out = pd.concat(rows, ignore_index=True)
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
    x = T[T.filled]
    print(x.groupby(["cfg", "side"]).agg(n=("r", "size"), exp=("r", "mean"), ctrl=("ctrl", "mean")).round(4).to_string())
