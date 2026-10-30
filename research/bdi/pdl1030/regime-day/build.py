"""pdl1030/regime-day build (copy of combo/build.py + daily SPY pre-open features): p05 (and p10 for parity) entries, long and Sx-short legs under parent (P) and S3 exits, with entry-time
tape columns. TRAIN+VALID only; HOLD months and locked block never loaded. Educational only - not financial advice."""
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
OUT = Path(__file__).resolve().parent / "cache"
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
INF = np.inf
SPEC = {"p05": dict(p=0.05, vr=INF, so=0.25), "p10": dict(p=0.10, vr=INF, so=0.0)}
_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in ("2026-04", "2026-05", "2026-06", "2026-10")
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    key = ds + "|" + fh["tod"].astype(str)
    sp = f[f["symbol"] == "SPY"]
    spk = sp["date"].astype(str) + "|" + sp["tod"].astype(str)
    spy_vd = pd.Series(sp["vwapDistPct"].to_numpy(float), index=spk).reindex(key).to_numpy(float)
    spy_gap = sp.groupby(sp["date"].astype(str))["gap"].first().reindex(ds).to_numpy(float)  # known at the open
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(ds).to_numpy(float)  # EOD: descriptive split only
    fb = sp.sort_values(["date", "tod"]).groupby(sp["date"].astype(str)).first()
    rng_all = (sp["dist_pdh_atr"] + sp["dist_pdl_atr"]).groupby(sp["date"].astype(str)).agg(["min", "max"])
    assert ((rng_all["max"] - rng_all["min"]).abs() < 1e-6).all(), "prior range not constant intraday"
    op = fb["close"] / (1 + fb["fromOpen"] / 100); pc = op / (1 + fb["gap"] / 100)
    pdl_ = fb["close"] - fb["dist_pdl_atr"] * fb["atr_d"]; pdh_ = fb["close"] + fb["dist_pdh_atr"] * fb["atr_d"]
    DAY = pd.DataFrame({"date": fb.index.astype(str), "gap": fb["gap"].to_numpy(float), "prng": (fb["dist_pdh_atr"] + fb["dist_pdl_atr"]).to_numpy(float),
                        "pclv": ((pc - pdl_) / (pdh_ - pdl_)).to_numpy(float), "atrp": (fb["atr_d"] / pc * 100).to_numpy(float),
                        "pc": pc.to_numpy(float), "first_tod": fb["tod"].to_numpy(int), "spy_day": sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(fb.index).to_numpy(float)})
    DAY.to_parquet(OUT / f"day_{month}.parquet", index=False)
    ctx = lib.load_context(month)
    br = pd.Series(ctx["breadth"].to_numpy(float), index=ctx["date"].astype(str) + "|" + ctx["tod"].astype(str)).reindex(key).to_numpy(float)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy()
    risk = 0.25 * fh["atr_d"].to_numpy(float)
    base = (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
    rows = []
    with np.errstate(invalid="ignore"):
        for s, b in SPEC.items():
            m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=b["vr"]), b["p"]), bool)
            mm = m & base & (ftod >= 950) & (ftod <= 1500)
            e1 = gates.first_per_symbol_day(fsym, fdat, mm)
            ent = fh2P[e1].astype(np.int64); Rv = risk[e1]
            out = {}
            sides = (("L", 1), ("S", -1)) if s == "p05" else (("L", 1),)
            for sn, side in sides:
                for ex, dn in (("P", 1.0), ("S3", 3.0)):
                    res = sim(h, l, c, tod, dend, tierP, ent, Rv, side, 0.5, dn, 0, 0, 0.0, 0.0, b["so"], 0.5, 1555, 0.0)
                    out[f"r{sn}_{ex}"] = res[0] / dn
            cst = (0.01 + c[ent] * 1e-4) * np.where(ftod[e1] < 1030, 1.4, 1.0) + 0.01 + c[ent] * 1e-4
            rows.append(pd.DataFrame({"setup": s, "date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], **out,
                                      "cost_rt_R": cst * tier_fh[e1] / Rv, "spy_vd": spy_vd[e1], "breadth": br[e1],
                                      "spy_gap": spy_gap[e1], "spy_day": spy_day[e1]}))
    T = pd.concat(rows, ignore_index=True)
    print(month, len(T), round(time.time() - t0), flush=True)
    return T


if __name__ == "__main__":
    for m in sys.argv[1:] or MONTHS:
        o = OUT / f"tr_{m}.parquet"
        if not o.exists():
            month_job(m).to_parquet(o, index=False)
