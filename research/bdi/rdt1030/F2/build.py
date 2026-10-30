"""rdt1030 / F2 build: F1-A entries (15-min OR break that completes a 5-min FVG, DESIGN.md 0.5 / F1) for both sides,
the F2 no-chop gate columns, the patched stop-first 5-min simulator (DESIGN 0.2), a K=5 random control per trade, and
the CWT14 PDL p05 parity rows (unpatched scan_1028.sim). TRAIN+VALID only; the locked block and HOLD months are never
loaded. Per-month trade parquet goes to scratch. Educational only - not financial advice.

    python research/bdi/rdt1030/F2/build.py [months...]
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
from scan_1019 import lib, S6, CL, scan, _mult  # noqa
from scan_1028 import sim as sim0  # noqa  (unpatched; parity only)
from mcf.research import gates  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F2")
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
HOLD = ("2026-04", "2026-05", "2026-06", "2026-10")
SEED, K_CTRL = 20261030, 5
G_FVG, SW_2R, WIN = 0.05, 0.085, (955, 1100)
INF = np.inf
_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))


def spy_g6():
    """date -> 1/0/NaN: SPY prior-day (H-L)/C >= trailing 20-day median (PLAN.md data rule; HOLD/locked rows excluded)."""
    d = lib.daily()
    s = d[d["symbol"] == "SPY"].copy()
    ds = s["date"].astype(str)
    s = s[~ds.str[:7].isin(HOLD) & (ds <= CUT) & ~((ds >= "2024-11-01") & (ds <= "2025-02-28"))].sort_values("date").reset_index(drop=True)
    rng = ((s["high"] - s["low"]) / s["close"]).to_numpy(float)
    dt = pd.to_datetime(s["date"]).to_numpy()
    out = {}
    for j in range(1, len(s)):
        if (dt[j] - dt[j - 1]) / np.timedelta64(1, "D") > 5:
            continue
        lo = max(0, j - 20)
        w = [rng[k] for k in range(lo, j) if (dt[j] - dt[k]) / np.timedelta64(1, "D") <= 45]
        if len(w) < 10:
            continue
        out[str(s["date"].iloc[j])] = float(rng[j - 1] >= np.median(w))
    return out


@numba.njit(cache=True)
def kernel(seg_start, seg_end, tod, bn, h, l, c, fo, atr, g, sw):
    """Per row: ER through the previous row (er_prev). Per segment: F1-A long / short signal rows (-1 none), OR15,
    and the opposite-break-before flag at the signal."""
    n = len(tod)
    er_prev = np.full(n, np.nan)
    ns = len(seg_start)
    sigL = np.full(ns, -1, np.int64); sigS = np.full(ns, -1, np.int64)
    orh = np.full(ns, np.nan); orl = np.full(ns, np.nan)
    oppL = np.zeros(ns, np.bool_); oppS = np.zeros(ns, np.bool_)
    for q in range(ns):
        a, b = seg_start[q], seg_end[q]
        # open proxy from the first frame row (tod >= 950): close / (1 + fromOpen/100)
        od = np.nan
        for i in range(a, b + 1):
            if tod[i] >= 950 and np.isfinite(fo[i]):
                od = c[i] / (1 + fo[i] / 100.0)
                break
        # ER through previous row, closes from the 0935 row
        s = 0.0; prev = np.nan; started = False; nb = 0
        for i in range(a, b + 1):
            if started and nb >= 3 and np.isfinite(od) and s > 0:
                er_prev[i] = abs(prev - od) / s
            if tod[i] == 935:
                started = True
                s = abs(c[i] - od); prev = c[i]; nb = 1
            elif started:
                s += abs(c[i] - prev); prev = c[i]; nb += 1
        # OR15
        H = -np.inf; L = np.inf; k = 0
        for i in range(a, b + 1):
            if tod[i] == 935 or tod[i] == 940 or tod[i] == 945:
                H = max(H, h[i]); L = min(L, l[i]); k += 1
        if k != 3:
            continue
        orh[q] = H; orl[q] = L
        A = atr[a]
        if not (A > 0) or (H - L) < 0.05 * A:
            continue
        gmin = max(g * A, 0.02)
        bu = -1; bd = -1
        for i in range(a, b + 1):
            if tod[i] >= 950:
                if bu < 0 and c[i] > H:
                    bu = i
                if bd < 0 and c[i] < L:
                    bd = i
        for side in (1, -1):
            br = bu if side == 1 else bd
            if br < 0:
                continue
            for i in (br, br + 1):
                if i > b or i - 2 < a:
                    continue
                if tod[i] < WIN[0] or tod[i] > WIN[1]:
                    continue
                if bn[i] - bn[i - 2] != 2 or bn[i] - bn[i - 1] != 1:
                    continue
                if side == 1:
                    ok = (l[i] - h[i - 2] >= gmin) and c[i] > H
                else:
                    ok = (l[i - 2] - h[i] >= gmin) and c[i] < L
                if ok:
                    opp = False
                    for j in range(a, i):
                        if tod[j] >= 950 and ((side == 1 and c[j] < L) or (side == -1 and c[j] > H)):
                            opp = True
                    if side == 1:
                        sigL[q] = i; oppL[q] = opp
                    else:
                        sigS[q] = i; oppS[q] = opp
                    break
    return er_prev, sigL, sigS, orh, orl, oppL, oppS


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, tierP, ent, Rv, side, up, be):
    """scan_1028.sim patched per DESIGN 0.2: per-trade R (dn = 1) and target multiple up[q]; entry at the signal close;
    every exit pays 1c + 1 bp (targets included), stop / moved-stop exits +2c; entry x tod multiplier; all costs x
    tierP[signal row]; gap-through stop fill min(stop, high[k]) (long) / max(stop, low[k]) (short).
    Codes: 1 target, 2 stop, 3 moved stop (BE), 6 flatten 15:55. r net, in R."""
    n = len(ent)
    r = np.full(n, np.nan); code = np.zeros(n, np.int8); xrow = np.full(n, -1, np.int64)
    for q in range(n):
        i = ent[q]; R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]
        e = c[i]
        ec = (0.01 + e * 1e-4) * _mult(tod[i])
        stop = e - side * R
        tgt = e + side * up[q] * R
        mfe = 0.0; x = 0.0; cd = 0; xr = -1
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x = min(stop, h[k]) if side == 1 else max(stop, l[k])
                xr = k
                cd = 2 if side * (stop - e) < -0.999 * R else 3
                break
            mfe = max(mfe, side * (fav - e) / R)
            if side * (fav - tgt) >= 0:
                x, cd, xr = tgt, 1, k
                break
            if be > 0 and mfe >= be:
                stop = max(stop, e) if side == 1 else min(stop, e)
        if cd == 0:
            x, cd, xr = c[end], 6, end
        xc = 0.01 + x * 1e-4 + (0.02 if (cd == 2 or cd == 3) else 0.0)
        r[q] = side * (x - e) / R - tierP[i] * (ec + xc) / R
        code[q] = cd; xrow[q] = xr
    return r, code, xrow


def month_job(month, g6map):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in HOLD
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    key = (ds + "|" + fh["tod"].astype(str)).to_numpy()
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    hP, lP, cP, todP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy().astype(np.int32)
    adv = fh["adv20"].fillna(0).to_numpy(float); atr = fh["atr_d"].to_numpy(float)
    h, l, c = fh["high"].to_numpy(float), fh["low"].to_numpy(float), fh["close"].to_numpy(float)
    sd = fsym.astype(object) + "|" + fdat.astype(object)
    new = np.r_[True, sd[1:] != sd[:-1]]
    sst = np.flatnonzero(new); sen = np.r_[sst[1:] - 1, len(fh) - 1]
    # day-constant atr per segment (head rows carry it too); fromOpen on frame rows
    bn = ((ftod // 100) * 60 + ftod % 100 - 570) // 5
    er_prev, sigL, sigS, orh, orl, oppL, oppS = kernel(sst, sen, ftod, bn.astype(np.int32), h, l, c,
                                                     fh["fromOpen"].to_numpy(float), atr, G_FVG, SW_2R)
    segid = np.cumsum(new) - 1
    # context
    ctx = lib.load_context(month)
    ck = (ctx["date"].astype(str) + "|" + ctx["tod"].astype(str)).to_numpy()
    qqq = pd.Series(ctx["qqq_fo"].to_numpy(float), index=ck)
    sp = (fsym == "SPY")
    spy_er = pd.Series(er_prev[sp], index=key[sp])
    spy_day = pd.Series(fh["fromOpen"].to_numpy(float)[sp & (ftod >= 950)], index=fdat[sp & (ftod >= 950)]).groupby(level=0).last()
    vr = fh["volumeRatio"].to_numpy(float)
    # universe for control
    with np.errstate(invalid="ignore"):
        uni = (adv >= 95e6) & (atr > 0) & (ftod >= 950)
    uidx = np.flatnonzero(uni)
    ug = pd.Series(uidx).groupby(key[uidx]).apply(lambda s: s.to_numpy()).to_dict()
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    out = []
    for side, sig, opp in ((1, sigL, oppL), (-1, sigS, oppS)):
        q = np.flatnonzero(sig >= 0)
        i = sig[q]
        A = atr[i]
        e = c[i]
        stp = np.where(side == 1, l[i - 2], h[i - 2])
        R = side * (e - stp)
        with np.errstate(invalid="ignore"):
            ok = (adv[i] >= 95e6) & (A > 0) & (R >= 0.03 * A) & (R <= 1.0 * A)
        q, i, A, e, R = q[ok], i[ok], A[ok], e[ok], R[ok]
        up = np.where(R <= SW_2R * A, 2.0, 1.0)
        ent = fh2P[i].astype(np.int64)
        r, code, xrow = sim(hP, lP, cP, todP, dend, tierP, ent, R, side, up, 0.0)
        cst = ((0.01 + e * 1e-4) * np.where(ftod[i] < 1030, 1.4, 1.0) + 0.01 + e * 1e-4) * tier_fh[i] / R
        # random control: K symbols in the universe at the same bar, same side, same risk in ATR units, same up
        ce, cR, cu, cq = [], [], [], []
        for t in range(len(i)):
            pool = ug.get(key[i[t]])
            if pool is None:
                continue
            pool = pool[fsym[pool] != fsym[i[t]]]
            if len(pool) == 0:
                continue
            pk = rng.choice(pool, size=min(K_CTRL, len(pool)), replace=False)
            ce.append(pk); cR.append(R[t] / A[t] * atr[pk]); cu.append(np.full(len(pk), up[t])); cq.append(np.full(len(pk), t))
        ctrl = np.full(len(i), np.nan)
        if ce:
            ce, cR, cu, cq = np.concatenate(ce), np.concatenate(cR), np.concatenate(cu), np.concatenate(cq)
            rc, _, _ = sim(hP, lP, cP, todP, dend, tierP, fh2P[ce].astype(np.int64), cR, side, cu, 0.0)
            ctrl = pd.Series(rc).groupby(cq).mean().reindex(np.arange(len(i))).to_numpy(float)
        out.append(pd.DataFrame({
            "date": fdat[i], "symbol": fsym[i], "tod": ftod[i], "side": "L" if side == 1 else "S", "r": r, "code": code,
            "up": up, "R_atr": R / A, "cost_rt_R": cst, "tier": tier_fh[i],
            "orw": (orh[q] - orl[q]) / A, "er": er_prev[i], "qqq_fo": qqq.reindex(key[i]).to_numpy(float),
            "spy_er": spy_er.reindex(key[i]).to_numpy(float), "g6": pd.Series(g6map).reindex(fdat[i]).to_numpy(float),
            "vr": vr[i], "opp_before": opp[q], "spy_day": spy_day.reindex(fdat[i]).to_numpy(float), "ctrl_r": ctrl}))
    # parity: CWT14 PDL p05 long, unpatched sim (pdl1030/combo build.py verbatim)
    x = CL.arrays(fh); lev = S6.levels(x)
    risk = 0.25 * atr
    with np.errstate(invalid="ignore"):
        base = (adv >= 95e6) & (atr > 0) & np.isfinite(risk) & (risk > 0)
        m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=INF), 0.05), bool) & base & (ftod >= 950) & (ftod <= 1500)
    e1 = gates.first_per_symbol_day(fsym, fdat, m)
    res = sim0(hP, lP, cP, todP, dend, tierP, fh2P[e1].astype(np.int64), risk[e1], 1, 0.5, 1.0, 0, 0, 0.0, 0.0, 0.25, 0.5, 1555, 0.0)
    out.append(pd.DataFrame({"date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], "side": "PAR", "r": res[0],
                             "spy_day": spy_day.reindex(fdat[e1]).to_numpy(float)}))
    T = pd.concat(out, ignore_index=True)
    T["date"] = T["date"].astype(str)
    print(month, {s: int((T.side == s).sum()) for s in ("L", "S", "PAR")}, "sessions", len(set(fdat)), round(time.time() - t0), "s", flush=True)
    return T


if __name__ == "__main__":
    SCR.mkdir(parents=True, exist_ok=True)
    g6map = spy_g6()
    for m in sys.argv[1:] or MONTHS:
        o = SCR / f"tr_{m}.parquet"
        if not o.exists():
            month_job(m, g6map).to_parquet(o, index=False)
