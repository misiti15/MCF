"""pdl1030c/ind3 build (copy of pdl1030c/ind1/build.py + RSI(5) and SPY/QQQ index-context fields) (from why/feat.py) of the Failed Prior-Day-Low Break Longs on the open 2-yr frames, TRAIN+VALID only.
HOLD (2026-04..06, 2026-09-16..10-07) and the locked block are never loaded (months skipped; 2026-09 rows > 09-15 dropped
at load). Same kernel (S6.b3_any) and simulator (top5_1028 sim) as swarm15. Educational only - not financial advice.
"""
import os, sys, time
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"), str(ROOT / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa
from scan_1019 import lib, S6, CL, scan  # noqa
from scan_1028 import sim  # noqa
from mcf.research import gates  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030c/ind3/cache")
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
INF = np.inf
SPEC = {"p05": dict(p=0.05, vr=INF, so=0.25), "p05lv": dict(p=0.05, vr=1.0, so=0.0),
        "p10": dict(p=0.10, vr=INF, so=0.0), "p10lv": dict(p=0.10, vr=1.0, so=0.0)}

_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))



SPEC = {"p05": dict(p=0.05, vr=INF, so=0.25), "p05lv": dict(p=0.05, vr=1.0, so=0.0)}

def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in ("2026-04", "2026-05", "2026-06", "2026-10")
    f, fh, P, dend, fh2P = SC.build_paths(month)
    assert (fh["date"].astype(str) <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    ds = fh["date"].astype(str)
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    key = ds + "|" + fh["tod"].astype(str)
    sp = f[f["symbol"] == "SPY"]
    spy_fo = pd.Series(sp["fromOpen"].to_numpy(float), index=sp["date"].astype(str) + "|" + sp["tod"].astype(str)).reindex(key).to_numpy(float)
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(ds).to_numpy(float)  # EOD: up/down-day split only
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy()
    risk = 0.25 * fh["atr_d"].to_numpy(float)
    base = (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
    vd_a = fh["vwapDistPct"].to_numpy(float); fo_a = fh["fromOpen"].to_numpy(float); cl_a = fh["close"].to_numpy(float)
    same = np.r_[False, (fsym[1:] == fsym[:-1]) & (fdat[1:] == fdat[:-1])]  # fh sorted symbol,date,tod
    vd_prev = np.where(same, np.r_[np.nan, vd_a[:-1]], np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        room = (cl_a / (1 + vd_a / 100) - cl_a) / fh["atr_d"].to_numpy(float)
    # RSI(5) fields (same symbol-day, prior bars only)
    r5 = fh["rsi5"].to_numpy(float)
    def prev(a, k):
        o = np.full(len(a), np.nan); ok = np.ones(len(a), bool)
        for j in range(1, k + 1):
            ok[j:] &= (fsym[j:] == fsym[:-j]) & (fdat[j:] == fdat[:-j]); ok[:j] = False
        o[k:] = a[:-k]; o[~ok] = np.nan
        return o
    r5_prev = prev(r5, 1)
    with np.errstate(invalid="ignore"):
        r5_min3 = np.fmin(np.fmin(prev(r5, 1), prev(r5, 2)), prev(r5, 3))
        r5_min3[np.isnan(prev(r5, 1)) | np.isnan(prev(r5, 2)) | np.isnan(prev(r5, 3))] = np.nan
    # index context from the SPY/QQQ rows of fh (head rows included), keyed date|tod
    ictx = {}
    for sym in ("SPY", "QQQ"):
        g = fh[fh["symbol"] == sym].sort_values(["date", "tod"])
        gfo = g["fromOpen"].to_numpy(float); gc = g["close"].to_numpy(float); gl = g["low"].to_numpy(float)
        op = gc / (1 + gfo / 100)
        lowfo = (gl / op - 1) * 100
        runlow = pd.Series(lowfo).groupby(g["date"].astype(str).to_numpy()).cummin().to_numpy()
        k = g["date"].astype(str).to_numpy() + "|" + g["tod"].astype(str).to_numpy()
        for nm, arr in (("fo", gfo), ("runlow", runlow), ("vd", g["vwapDistPct"].to_numpy(float))):
            ictx[f"{sym.lower()}_{nm}"] = pd.Series(arr, index=k).reindex(key).to_numpy(float)
    rows = []
    with np.errstate(invalid="ignore"):
        for s, b in SPEC.items():
            m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=b["vr"]), b["p"]), bool)
            mm = m & base & (ftod >= 950) & (ftod <= 1500)
            e1 = gates.first_per_symbol_day(fsym, fdat, mm)
            ent = fh2P[e1].astype(np.int64); Rv = risk[e1]
            out = {}
            for ex, dn in (("P", 1.0), ("S3", 3.0)):
                res = sim(h, l, c, tod, dend, tierP, ent, Rv, 1, 0.5, dn, 0, 0, 0.0, 0.0, b["so"], 0.5, 1555, 0.0)
                out["r_" + ex] = res[0] / dn
            cst = (0.01 + c[ent] * 1e-4) * np.where(ftod[e1] < 1030, 1.4, 1.0) + 0.01 + c[ent] * 1e-4
            t = pd.DataFrame({"setup": s, "date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], **out,
                              "cost_rt_R": cst * tier_fh[e1] / Rv, "gap": x.gap[e1],
                              "vd": fh["vwapDistPct"].to_numpy(float)[e1],
                              "rs": fh["fromOpen"].to_numpy(float)[e1] - spy_fo[e1],
                              "vr": fh["volumeRatio"].to_numpy(float)[e1], "spy_day": spy_day[e1],
                              "fo": fo_a[e1], "rsi5": r5[e1], "rsi5_prev": r5_prev[e1], "rsi5_min3": r5_min3[e1], **{kk: vv[e1] for kk, vv in ictx.items()}})
            rows.append(t)
    T = pd.concat(rows, ignore_index=True)
    print(month, len(T), round(time.time() - t0), flush=True)
    return T


if __name__ == "__main__":
    ms = sys.argv[1:] or MONTHS
    for m in ms:
        o = OUT / f"tr_{m}.parquet"
        if o.exists():
            continue
        month_job(m).to_parquet(o, index=False)
