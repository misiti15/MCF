"""pdl1030/tape-flip: simulate the p05/p10 long parents plus the two short legs (Sx immediate flip, Sb re-break flip) at
every p05 signal on the open 2-yr frames, TRAIN+VALID only. HOLD months and the locked block are never loaded.
Same kernel (S6.b3_any) / simulator (top5_1028 sim) / costs as swarm15 and pdl1030/why. Educational only - not financial advice.
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
OUT = Path(__file__).resolve().parent / "cache"
OUT.mkdir(exist_ok=True)
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
    def ser(sym, col):
        g = f[f["symbol"] == sym]
        return pd.Series(g[col].to_numpy(float), index=g["date"].astype(str) + "|" + g["tod"].astype(str))
    spy_fo = ser("SPY", "fromOpen").reindex(key).to_numpy(float)
    spy_vd = ser("SPY", "vwapDistPct").reindex(key).to_numpy(float)
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
    pdl = x.pdl
    rows = []
    for s, b in SPEC.items():
        with np.errstate(invalid="ignore"):
            m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=b["vr"]), b["p"]), bool)
        mm = m & base & (ftod >= 950) & (ftod <= 1500)
        e1 = gates.first_per_symbol_day(fsym, fdat, mm)
        ent = fh2P[e1].astype(np.int64); Rv = risk[e1]
        cst = ((0.01 + c[ent] * 1e-4) * np.where(ftod[e1] < 1030, 1.4, 1.0) + 0.01 + c[ent] * 1e-4) * tier_fh[e1] / Rv
        legs = [("L", 1, ent, ftod[e1])]
        if s == "p05":
            legs.append(("Sx", -1, ent, ftod[e1]))
            # Sb: first bar after the signal (<= 15:00) that closes back below PDL
            kb = np.full(len(e1), -1, np.int64)
            for q in range(len(e1)):
                i = ent[q]; d = dend[i]; lv = pdl[e1[q]]
                if i < d:
                    seg_c = c[i + 1:d + 1]; seg_t = tod[i + 1:d + 1]
                    w = np.flatnonzero((seg_c < lv) & (seg_t <= 1500))
                    if len(w):
                        kb[q] = i + 1 + w[0]
            legs.append(("Sb", -1, kb, np.where(kb >= 0, tod[np.maximum(kb, 0)], -1)))
        for leg, side, en, etod in legs:
            r, mfe, mae, cd, et, xr = sim(h, l, c, tod, dend, tierP, en, Rv, side, 0.5, 1.0, 0, 0, 0.0, 0.0, b["so"], 0.5, 1555, 0.0)
            t = pd.DataFrame({"setup": s, "leg": leg, "date": fdat[e1], "symbol": fsym[e1], "sig_tod": ftod[e1], "etod": etod,
                              "r": r, "code": cd, "spy_fo": spy_fo[e1], "spy_vd": spy_vd[e1], "breadth": br[e1], "cost_rt_R": cst})
            rows.append(t)
    T = pd.concat(rows, ignore_index=True)
    print(month, len(T), round(time.time() - t0), flush=True)
    return T


if __name__ == "__main__":
    for mth in (sys.argv[1:] or MONTHS):
        o = OUT / f"t_{mth}.parquet"
        if o.exists():
            continue
        month_job(mth).to_parquet(o, index=False)
