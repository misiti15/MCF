"""so1a build: regime-day build.py p05 only, S3 exits with half-off (so=0.25) and without (so=0), plus the bar tod at
which the half-off level is reached (scale trigger) for the cap-order variant. TRAIN+VALID only. Educational only."""
import os, sys, time
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd, numba
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"), str(ROOT / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa
from scan_1019 import lib, S6, CL, scan, _mult  # noqa
from scan_1028 import sim  # noqa
from mcf.research import gates  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path(sys.argv[1]); CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df): return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))


@numba.njit(cache=False)
def scale_hit(h, l, c, tod, dend, ent, Rv, side, up, dn, so):
    """Mirror of sim's loop (em=0, no lim/tsb/be/clock): tod of the bar where the half-off level is reached before the
    stop/target, -1 otherwise; also the exit tod."""
    n = len(ent); st = np.full(n, -1, np.int32); xt = np.full(n, -1, np.int32)
    for q in range(n):
        i = ent[q]; R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]; e = c[i]; stop = e - side * dn * R; tgt = e + side * up * R; spx = e + side * so * R
        scaled = False; xr = end
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]; fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                xr = k; break
            if side * (fav - tgt) >= 0:
                xr = k; break
            if not scaled and side * (fav - spx) >= 0:
                scaled = True; st[q] = tod[k]
                stop = max(stop, e) if side == 1 else min(stop, e)
        xt[q] = tod[xr]
    return st, xt


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in ("2026-04", "2026-05", "2026-06", "2026-10")
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    sp = f[f["symbol"] == "SPY"]
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(ds).to_numpy(float)
    fb = sp.sort_values(["date", "tod"]).groupby(sp["date"].astype(str)).first()
    prng = pd.Series((fb["dist_pdh_atr"] + fb["dist_pdl_atr"]).to_numpy(float), index=fb.index.astype(str)).reindex(ds).to_numpy(float)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy(); risk = 0.25 * fh["atr_d"].to_numpy(float)
    base = (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
    with np.errstate(invalid="ignore"):
        m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=np.inf), 0.05), bool)
        mm = m & base & (ftod >= 950) & (ftod <= 1500)
        e1 = gates.first_per_symbol_day(fsym, fdat, mm)
        ent = fh2P[e1].astype(np.int64); Rv = risk[e1]
        out = {}
        for sn, side in (("L", 1), ("S", -1)):
            for tag, so in (("SO", 0.25), ("NO", 0.0)):
                res = sim(h, l, c, tod, dend, tierP, ent, Rv, side, 0.5, 3.0, 0, 0, 0.0, 0.0, so, 0.5, 1555, 0.0)
                out[f"r{sn}_{tag}"] = res[0] / 3.0
                if tag == "SO":
                    out[f"code{sn}"] = res[3]
            st, xt = scale_hit(h, l, c, tod, dend, ent, Rv, side, 0.5, 3.0, 0.25)
            out[f"stod{sn}"] = st; out[f"xtod{sn}"] = xt
        cst = (0.01 + c[ent] * 1e-4) * np.where(ftod[e1] < 1030, 1.4, 1.0) + 0.01 + c[ent] * 1e-4
    T = pd.DataFrame({"date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], **out, "cost_rt_R": cst * tier_fh[e1] / Rv,
                      "prng": prng[e1], "spy_day": spy_day[e1]})
    print(month, len(T), round(time.time() - t0), flush=True)
    return T


if __name__ == "__main__":
    for mo in sys.argv[2:] or MONTHS:
        o = OUT / f"tr_{mo}.parquet"
        if not o.exists():
            month_job(mo).to_parquet(o, index=False)
