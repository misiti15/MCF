"""pdl1030/entry-confirm: entry confirmation / timing variants of CWT14-failbrk-pdl-p05-long (PLAN.md, written first).
TRAIN+VALID only: HOLD (2026-04..06, 2026-09-16..) and the locked block are never loaded. Same kernel (S6.b3_any),
same costs and exit mechanics as swarm15 (top5_1028 sim). Educational only - not financial advice.
    python scan_ec.py [months...]   -> tr_<month>.parquet in this folder
"""
import os, sys, time
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numba
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"), str(ROOT / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa
from scan_1019 import lib, S6, CL, scan  # noqa
from scan_1028 import sim  # noqa
from scan_1015 import _mult  # noqa
from mcf.research import gates  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path(__file__).resolve().parent
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
ONLY = [v for v in os.environ.get("EC_ONLY", "").split(",") if v]
HOLD = ("2026-04", "2026-05", "2026-06", "2026-10")
_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))

# mode: 0 immediate, 1 hold, 2 followthru, 3 retest, 4 limit
# hold params: k, nolow, strict, spy ; limit params: kind (0 pdl+0.02atr, 1 mid, 2 c-0.25R), fallback
CFG = {
    "P":   dict(mode=0),
    "C01": dict(mode=1, k=1), "C02": dict(mode=1, k=2), "C03": dict(mode=1, k=3),
    "C04": dict(mode=1, k=6, nolow=1), "C05": dict(mode=1, k=2, strict=1),
    "C06": dict(mode=2, k=3), "C07": dict(mode=3, k=6),
    "C08": dict(mode=4, lk=0), "C09": dict(mode=4, lk=1), "C10": dict(mode=4, lk=2), "C11": dict(mode=4, lk=1, fb=1),
    "C12": dict(mode=1, k=2, spy=1), "C13": dict(mode=1, k=1, spy=1),
    "C14": dict(mode=0, far=0.15),
    "C15": dict(mode=1, k=6, nolow=1, cost=0.05), "C16": dict(mode=1, k=2, spy=1, cost=0.05),
    "C17": dict(mode=4, lk=0, cost=0.05), "C18": dict(mode=1, k=2, cost=0.05),
    "C19": dict(mode=1, k=1, spy=1, cost=0.05),
}


@numba.njit(cache=True)
def confirm(i_arr, h, l, c, dend, spyc, pdl, lod, atr, R, mode, k, nolow, strict, spy, lk, fb):
    n = len(i_arr)
    J = np.full(n, -1, np.int64)
    E = np.full(n, np.nan)
    LIM = np.zeros(n, np.bool_)
    for q in range(n):
        i = i_arr[q]
        end = dend[i]
        L = pdl[q]
        if mode == 0:
            J[q], E[q] = i, c[i]
        elif mode == 1:
            if i + k > end:
                continue
            ok = True
            for b in range(i + 1, i + k + 1):
                if not (c[b] > L):
                    ok = False
                if strict and not (l[b] >= L):
                    ok = False
                if nolow and l[b] < lod[q]:
                    ok = False
            if ok and spy:
                if not (spyc[i + k] >= spyc[i]):  # NaN -> fail
                    ok = False
            if ok:
                J[q], E[q] = i + k, c[i + k]
        elif mode == 2:
            for b in range(i + 1, min(i + k, end) + 1):
                if not (c[b] > L):
                    break
                if c[b] > h[i]:
                    J[q], E[q] = b, c[b]
                    break
        elif mode == 3:
            for b in range(i + 1, min(i + k, end) + 1):
                if not (c[b] > L) or l[b] < lod[q]:
                    break
                if l[b] <= L + 0.05 * atr[q]:
                    J[q], E[q] = b, c[b]
                    break
        else:
            if lk == 0:
                lp = L + 0.02 * atr[q]
            elif lk == 1:
                lp = 0.5 * (c[i] + L)
            else:
                lp = c[i] - 0.25 * R[q]
            lp = min(lp, c[i])
            lp = np.floor(lp * 100.0) / 100.0
            for b in range(i + 1, min(i + 3, end) + 1):
                if l[b] <= lp - 0.01:
                    J[q], E[q], LIM[q] = b, lp, True
                    break
            if J[q] < 0 and fb == 1 and i + 3 <= end and c[i + 3] > L:
                J[q], E[q] = i + 3, c[i + 3]
    return J, E, LIM


@numba.njit(cache=True)
def sim2(h, l, c, tod, dend, tierP, ent, J, E, LIM, Rv, side, up, dn, tsb, tsr, be, so, sof, xt):
    """top5_1028 sim with the entry bar J / price E given (LIM: fill bar checked for stop only). Same cost model."""
    n = len(ent)
    r = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    etod = np.zeros(n, np.int32)
    mfe_o = np.full(n, np.nan)
    for q in range(n):
        i = ent[q]
        R = Rv[q]
        j = J[q]
        if i < 0 or j < 0 or not (R > 0):
            continue
        end = dend[i]
        e = E[q]
        ec = (0.01 + e * 1e-4) * _mult(tod[j])
        stop = e - side * dn * R
        tgt = e + side * up * R
        spx = e + side * so * R
        scaled = False
        mfe, mae = 0.0, 0.0
        x, cd, xr = 0.0, 0, -1
        if LIM[q]:
            adv0 = l[j] if side == 1 else h[j]
            if side * (adv0 - stop) <= 0:
                x, cd, xr = stop, 2, j
        clock = tod[j] < xt
        if cd == 0:
            for kk in range(j + 1, end + 1):
                if clock and tod[kk] > xt:
                    x, cd, xr = c[kk - 1], 5, kk - 1
                    break
                adv = l[kk] if side == 1 else h[kk]
                fav = h[kk] if side == 1 else l[kk]
                mae = min(mae, side * (adv - e) / R)
                if side * (adv - stop) <= 0:
                    x, xr = stop, kk
                    cd = 2 if side * (stop - e) < -0.999 * dn * R else 3
                    break
                mfe = max(mfe, side * (fav - e) / R)
                if side * (fav - tgt) >= 0:
                    x, cd, xr = tgt, 1, kk
                    break
                if tsb > 0 and (kk - j) >= tsb and mfe < tsr:
                    x, cd, xr = c[kk], 4, kk
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
        code[q], etod[q], mfe_o[q] = cd, tod[j], mfe
    return r, code, etod, mfe_o


def tod_mult(t):
    t = np.asarray(t)
    return np.where(t < 935, 3.8, np.where(t < 950, 2.1, np.where(t < 1030, 1.4, 1.0)))


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in HOLD
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    # SPY close per P row (same date|tod), from P itself (SPY rows are in P)
    pk = P["date"].astype(str).to_numpy() + "|" + P["tod"].astype(str).to_numpy()
    sp = P[P["symbol"] == "SPY"]
    spys = pd.Series(sp["close"].to_numpy(float), index=sp["date"].astype(str) + "|" + sp["tod"].astype(str))
    spys = spys[~spys.index.duplicated()]
    spyc = spys.reindex(pk).to_numpy(float)
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy()
    risk = 0.25 * fh["atr_d"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=np.inf), 0.05), bool)
        mm = m & (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0) & (ftod >= 950) & (ftod <= 1500)
    # parent via the original sim (parity)
    e1 = gates.first_per_symbol_day(fsym, fdat, mm)
    res0 = sim(h, l, c, tod, dend, tierP, fh2P[e1].astype(np.int64), risk[e1], 1, 0.5, 1.0, 0, 0, 0.0, 0.0, 0.25, 0.5, 1555, 0.0)
    cand = np.flatnonzero(mm)
    iP = fh2P[cand].astype(np.int64)
    assert (iP >= 0).all()
    pdl, lod, atr, Rc = x.pdl[cand], x.lod[cand], x.atr[cand], risk[cand]
    kd = pd.Series(fsym[cand].astype(str)) + "|" + pd.Series(fdat[cand])
    rows = []
    reg_spy_nan = 0
    for v, cf in CFG.items():
        if ONLY and v not in ONLY:
            continue
        J, E, LIM = confirm(iP, h, l, c, dend, spyc, pdl, lod, atr, Rc, cf["mode"], cf.get("k", 0), cf.get("nolow", 0),
                            cf.get("strict", 0), cf.get("spy", 0), cf.get("lk", 0), cf.get("fb", 0))
        ok = J >= 0
        if "far" in cf:
            ok &= (c[iP] - pdl) <= cf["far"] * atr
        if "cost" in cf:
            tq = np.where(LIM, tod[np.minimum(iP + 1, len(tod) - 1)], tod[np.maximum(J, 0)])
            cfrac = tier_fh[cand] * (0.01 + E * 1e-4) * tod_mult(tq) / Rc
            ok &= cfrac <= cf["cost"]
        # per symbol-day: confirmed candidate with the earliest entry bar
        idx = np.flatnonzero(ok)
        if len(idx):
            dfp = pd.DataFrame({"k": kd.to_numpy()[idx], "J": J[idx], "q": idx}).sort_values(["k", "J", "q"], kind="mergesort")
            sel = dfp.drop_duplicates("k")["q"].to_numpy()
        else:
            sel = idx
        sel = np.sort(sel)
        r, cd, et, mfe = sim2(h, l, c, tod, dend, tierP, iP[sel], J[sel], E[sel], LIM[sel], Rc[sel], 1, 0.5, 1.0, 0, 0.0, 0.0, 0.25, 0.5, 1555)
        if v == "P" and "P" in (ONLY or CFG):
            r0 = res0[0]
            assert len(r0) == len(r) and np.allclose(np.nan_to_num(r0, nan=-99), np.nan_to_num(r, nan=-99)), "sim2 parity"
        t = pd.DataFrame({"var": v, "date": fdat[cand[sel]], "symbol": fsym[cand[sel]], "sig_tod": ftod[cand[sel]], "tod": et,
                          "r": r, "code": cd, "mfe": mfe, "lim": LIM[sel]})
        rows.append(t[np.isfinite(t["r"].to_numpy())])
    T = pd.concat(rows, ignore_index=True)
    T = T.astype({"var": "category", "symbol": "category", "r": "float32", "mfe": "float32"})
    print(month, len(T), "spy_nan_share", round(float(np.isnan(spyc[iP]).mean()), 4), round(time.time() - t0), flush=True)
    return T


if __name__ == "__main__":
    for mo in sys.argv[1:] or MONTHS:
        o = OUT / (f"tr_{mo}.parquet" if not ONLY else f"tr19_{mo}.parquet")
        if o.exists():
            continue
        month_job(mo).to_parquet(o, index=False)
