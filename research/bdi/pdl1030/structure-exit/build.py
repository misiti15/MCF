"""pdl1030/structure-exit step 1: cache the p05 / p10 parent entries and their 5-minute paths (entry bar .. 15:55),
TRAIN+VALID months only. HOLD months and the locked block are never loaded; 2026-09 rows after 09-15 are dropped at load
(same loader patch as pdl1030/why/feat.py). Kernel S6.b3_any, same base filters as swarm15.
Educational only - not financial advice.
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
from mcf.research import gates  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path(__file__).resolve().parent / "cache"
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
SPEC = {"p05": 0.05, "p10": 0.10}

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
    sp = f[f["symbol"] == "SPY"]
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(ds).to_numpy(float)  # descriptive (up/down day) only
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy()
    atr_d = fh["atr_d"].to_numpy(float)
    risk = 0.25 * atr_d
    base = (adv >= 95e6) & (atr_d > 0) & np.isfinite(risk) & (risk > 0) & (ftod >= 950) & (ftod <= 1500)
    rows = []
    with np.errstate(invalid="ignore"):
        for s, p in SPEC.items():
            m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=np.inf), p), bool) & base
            e1 = gates.first_per_symbol_day(fsym, fdat, m)
            rows.append(pd.DataFrame({"setup": s, "fhi": e1}))
    T = pd.concat(rows, ignore_index=True)
    e1 = T["fhi"].to_numpy()
    ent = fh2P[e1]
    T = T[ent >= 0].reset_index(drop=True); e1 = T["fhi"].to_numpy(); ent = fh2P[e1]
    T["date"], T["symbol"], T["tod"] = fdat[e1], fsym[e1], ftod[e1]
    T["e"], T["R0"], T["A"], T["tier"] = c[ent], risk[e1], atr_d[e1], tier_fh[e1]
    T["lod"], T["pdl"], T["open"], T["pc"], T["vwap"] = x.lod[e1], x.pdl[e1], x.open_d[e1], x.pc[e1], x.vwap[e1]
    T["spy_day"] = spy_day[e1]
    # paths: rows ent .. dend[ent]
    st, en = ent, dend[ent]
    ln = en - st + 1
    off = np.r_[0, np.cumsum(ln)]
    idx = np.concatenate([np.arange(a, b + 1) for a, b in zip(st, en)])
    np.savez(OUT / f"paths_{month}.npz", off=off.astype(np.int64), h=h[idx].astype(np.float32), l=l[idx].astype(np.float32),
             c=c[idx].astype(np.float32), tod=tod[idx].astype(np.int16), e=c[ent])
    T.drop(columns=["fhi"]).to_parquet(OUT / f"tr_{month}.parquet", index=False)
    print(month, len(T), int(off[-1]), round(time.time() - t0), flush=True)


if __name__ == "__main__":
    for m in sys.argv[1:] or MONTHS:
        if not (OUT / f"tr_{m}.parquet").exists():
            month_job(m)
