"""Build the CWT14 event set from the OPEN 2-year frames (PLAN.md). Educational only - not financial advice.

Per open month (lib.months() lists open months only; lib.load_month refuses the locked block; MCF_HIST_ALLOW_LOCKED is
never set): lab frame rows (adv20 >= 95M) + the 09:35-09:45 / 15:05-15:55 rows of test_b/data/headtail.parquet.
  events_<m>.parquet : one row per kernel signal (level x p, kmax 5) on a 09:50-15:00 bar: fi, L, p, ks, v0, depth, ord
  rows_<m>.parquet   : one row per frame row that carries any event: features, SPY / breadth context, 22 outcomes
                       (2 sides x 11 exits, production costs) and their same-minute random baselines (95M universe)
    python build.py <scratch_dir> [month ...]
"""
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(HERE)]
import lib  # noqa: E402
from mcf.research.gates import prod_r  # noqa: E402
from sim import b3k, sim  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
OUT = Path(sys.argv[1]) if __name__ == "__main__" else None
FEAT = ["close", "high", "low", "vwapDistPct", "gap", "fromOpen", "atr_d", "dist_pdh_atr", "dist_pdl_atr",
        "volumeRatio", "adv20", "rsi", "rsi5", "heat", "sma20_slope_pct", "emaDiff", "atrPct"]
FG = ("t1s1", "t05s1", "t1s05")
# id: (up, dn, be, so, sof, trail_r, trail_after, tsb, tsr)
SIMX = {"t05s05": (0.5, 0.5, 0, 0, 0.5, 0, 0, 0, 0), "t05s1so": (0.5, 1.0, 0, 0.25, 0.5, 0, 0, 0, 0),
        "t1s1so": (1.0, 1.0, 0, 0.5, 0.5, 0, 0, 0, 0), "t1s1be": (1.0, 1.0, 0.5, 0, 0.5, 0, 0, 0, 0),
        "t1s1tr": (1.0, 1.0, 0, 0, 0.5, 0.5, 0.5, 0, 0), "t1s1ts": (1.0, 1.0, 0, 0, 0.5, 0, 0, 6, 0.25),
        "hold": (0.0, 1.0, 0, 0, 0.5, 0, 0, 0, 0), "holdtr": (0.0, 1.0, 0, 0, 0.5, 1.0, 1.0, 0, 0)}
EXITS = list(FG) + list(SIMX)
PS = (0.03, 0.05, 0.10, 0.15, 0.20, 0.30)
LEVELS = ("PDL", "PDH", "ORL", "ORH")
PARITY = {"t1s1": (1.0, 1.0, 0, 0, 0.5, 0, 0, 0, 0), "t05s1": (0.5, 1.0, 0, 0, 0.5, 0, 0, 0, 0),
          "t1s05": (1.0, 0.5, 0, 0, 0.5, 0, 0, 0, 0)}


def month_job(m):
    t0 = time.time()
    cols = ["symbol", "date", "tod"] + FEAT + [f"{k}_{s}_{g}" for s in ("long", "short") for g in FG for k in ("r", "win")]
    f = lib.load_month(m, cols)
    spy = f.loc[f.symbol == "SPY", ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    f = f[(f["adv20"].to_numpy(float) >= 95e6) & (f["atr_d"].to_numpy(float) > 0)].reset_index(drop=True)
    f["symbol"] = f["symbol"].astype(str)
    f["_fi"] = np.arange(len(f))
    a = pd.Timestamp(m + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    ht = ht[(ht.tod < 950) | (ht.tod > 1500)]
    ht = ht.merge(f[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    h = pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"].astype(f["tod"].dtype),
                      "close": ht["c"].astype(float), "high": ht["h"].astype(float), "low": ht["l"].astype(float),
                      "_fi": -1})
    P = pd.concat([f[["symbol", "date", "tod", "close", "high", "low", "_fi"]], h], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    sy, dt = P["symbol"].to_numpy(), P["date"].to_numpy()
    new = np.r_[True, (sy[1:] != sy[:-1]) | (dt[1:] != dt[:-1])]
    seg = np.cumsum(new) - 1
    last = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1]
    dend = last[seg].astype(np.int64)
    fi = P["_fi"].to_numpy()
    f2P = np.full(len(f), -1, np.int64)
    f2P[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
    # per-row arrays on P (frame values broadcast via f2P)
    def onP(col, fill=np.nan):
        v = np.full(len(P), fill, float)
        v[f2P] = f[col].to_numpy(float)
        return v
    c, hh, ll = P["close"].to_numpy(float), P["high"].to_numpy(float), P["low"].to_numpy(float)
    tod = P["tod"].to_numpy(np.int64)
    first = lambda v: pd.Series(v).groupby(seg).transform("first").to_numpy(float)  # noqa: E731 (first non-NaN)
    atr_r = onP("atr_d")
    atr = first(atr_r)
    pdh = first(onP("close") + onP("dist_pdh_atr") * atr_r)
    pdl = first(onP("close") - onP("dist_pdl_atr") * atr_r)
    vr = onP("volumeRatio")
    hod = pd.Series(hh).groupby(seg).cummax().to_numpy(float)
    lod = pd.Series(ll).groupby(seg).cummin().to_numpy(float)
    orh = pd.Series(np.where(tod == 1000, hod, np.nan)).groupby(seg).ffill().to_numpy(float)
    orl = pd.Series(np.where(tod == 1000, lod, np.nan)).groupby(seg).ffill().to_numpy(float)
    ok_all = np.ones(len(P), bool)
    ok_or = tod >= 1005
    LV = {"PDL": (pdl, ok_all, False), "PDH": (pdh, ok_all, True), "ORL": (orl, ok_or, False), "ORH": (orh, ok_or, True)}
    ev = []
    for li, L in enumerate(LEVELS):
        lev, lo_ok, upper = LV[L]
        for pi, p in enumerate(PS):
            flag, ks, v0, dep, ordn = b3k(new, lo_ok, lev, hh, ll, c, vr, atr, p, 5, upper)
            ix = np.flatnonzero(flag & (fi >= 0))
            ev.append(pd.DataFrame({"fi": fi[ix].astype(np.int32), "L": np.int8(li), "p": np.int8(pi),
                                    "ks": ks[ix], "v0": v0[ix], "depth": dep[ix], "ord": ordn[ix]}))
    ev = pd.concat(ev, ignore_index=True)
    # outcomes for every frame row of the universe (baselines) - frame geoms via prod_r, the rest via sim
    nf = len(f)
    O = {}
    Rv = 0.25 * f["atr_d"].to_numpy(float)
    for s in ("long", "short"):
        for g in FG:
            O[f"{s}_{g}"] = prod_r(f[f"r_{s}_{g}"].to_numpy(float), f[f"win_{s}_{g}"].to_numpy(float),
                                   f["close"].to_numpy(float), f["atr_d"].to_numpy(float), g,
                                   tod=f["tod"].to_numpy(float)).astype(np.float32)
        sd = 1 if s == "long" else -1
        for x, prm in SIMX.items():
            O[f"{s}_{x}"] = sim(hh, ll, c, tod, dend, f2P, Rv, sd, *map(float, prm[:7]), int(prm[7]), float(prm[8]))
    par = {}
    if m == "2025-06":          # simulator parity with the frame geometries
        for s in ("long", "short"):
            sd = 1 if s == "long" else -1
            for g, prm in PARITY.items():
                rs = sim(hh, ll, c, tod, dend, f2P, Rv, sd, *map(float, prm[:7]), int(prm[7]), float(prm[8]))
                ref = O[f"{s}_{g}"]
                okk = np.isfinite(ref) & np.isfinite(rs)
                par[f"{s}_{g}"] = (int(okk.sum()), float(np.mean(np.abs(rs[okk] - ref[okk]) < 0.02)),
                                   float(np.nanmean(rs[okk])), float(np.nanmean(ref[okk])))
    O = pd.DataFrame(O)
    base = pd.concat([f[["date", "tod"]], O], axis=1)
    B = base.groupby(["date", "tod"]).mean()
    B.columns = ["b_" + k for k in B.columns]
    up = (f["fromOpen"].to_numpy(float) > 0).astype(float)
    brd = pd.DataFrame({"date": f["date"], "tod": f["tod"], "breadth": up}).groupby(["date", "tod"])["breadth"].mean()
    B = B.join(brd).reset_index().merge(spy, on=["date", "tod"], how="left")
    # rows that carry an event
    u = np.unique(ev["fi"].to_numpy())
    R = f.loc[u, ["symbol", "date", "tod"] + [k for k in FEAT if k not in ("high", "low")]].copy()
    R["fi"] = u.astype(np.int32)
    for k in FEAT:
        if k in R and k not in ("adv20",):
            R[k] = R[k].astype(np.float32)
    Pi = f2P[u]
    R["pdh"], R["pdl"], R["orh"], R["orl"] = (pdh[Pi].astype(np.float32), pdl[Pi].astype(np.float32),
                                              orh[Pi].astype(np.float32), orl[Pi].astype(np.float32))
    for k in O.columns:
        R["o_" + k] = O[k].to_numpy()[u]
    R = R.merge(B, on=["date", "tod"], how="left")
    for k in R.columns:
        if R[k].dtype == np.float64 and k != "adv20":
            R[k] = R[k].astype(np.float32)
    R["month"] = m
    ev["month"] = m
    R.to_parquet(OUT / f"rows_{m}.parquet")
    ev.to_parquet(OUT / f"events_{m}.parquet")
    msg = f"{m} frame {nf} events {len(ev)} rows {len(R)} {round(time.time() - t0)}s {par}"
    print(msg, flush=True)
    return msg


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    ms = sys.argv[2:] or lib.months()
    assert not set(ms) & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("NPROC", "3"))) as pool:
        res = pool.map(month_job, ms, chunksize=1)
    open(OUT / "build.log", "w").write("\n".join(res))
