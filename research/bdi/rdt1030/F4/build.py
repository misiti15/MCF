"""rdt1030/F4 irl-erl build: liquidity sweep (PDL/ORL, mirror PDH/ORH) -> 15-min displacement -> first 15-min FVG.
Patched stop-first sim, random control, per-month trade parquet (scratch). TRAIN+VALID only; HOLD months and the locked
block are never loaded. Educational only - not financial advice.

Usage: python build.py check | python build.py parity | python build.py sanity | python build.py [months...]"""
import os, sys, time, json, zlib
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numba
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT), str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"),
                str(ROOT / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa
from scan_1019 import lib, scan, _mult  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F4")
SCR.mkdir(parents=True, exist_ok=True)
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
SEED = 20261030
K_CTRL = 5
_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))

# signal keys: (level, side, depth_atr (None = any trade-through), disp_atr, g_atr)
SIG = {"PDL": ("PD", 1, 0.05, 0.20, 0.05), "ORL": ("OR", 1, 0.05, 0.20, 0.05),
       "PDH": ("PD", -1, 0.05, 0.20, 0.05), "ORH": ("OR", -1, 0.05, 0.20, 0.05),
       "PDL_D30": ("PD", 1, 0.05, 0.30, 0.05), "PDL_G10": ("PD", 1, 0.05, 0.20, 0.10), "PDL_ANY": ("PD", 1, None, 0.20, 0.05)}
CFG = {  # id: (sig, retrace, tmode 0=DOL 1=2R, be)
    "F4-01": ("PDL", False, 0, 0.0), "F4-02": ("PDL", False, 1, 0.0), "F4-03": ("PDL", True, 0, 0.0), "F4-04": ("PDL", True, 1, 0.0),
    "F4-05": ("ORL", False, 0, 0.0), "F4-06": ("ORL", False, 1, 0.0), "F4-07": ("ORL", True, 0, 0.0), "F4-08": ("ORL", True, 1, 0.0),
    "F4-09": ("PDH", False, 0, 0.0), "F4-10": ("PDH", False, 1, 0.0), "F4-11": ("PDH", True, 0, 0.0),
    "F4-12": ("ORH", False, 0, 0.0), "F4-13": ("ORH", False, 1, 0.0),
    "F4-14": ("PDL_D30", False, 0, 0.0), "F4-15": ("PDL_G10", False, 0, 0.0), "F4-16": ("PDL_ANY", False, 0, 0.0),
    "F4-17": ("PDL", False, 0, 1.0),
}
CFG_RW = {}
if (Path(__file__).resolve().parent / "rework.json").exists():
    for k, v in json.loads((Path(__file__).resolve().parent / "rework.json").read_text()).items():
        CFG_RW[k] = tuple(v["cfg"])
REWORK = "rework" in sys.argv
if REWORK:
    sys.argv.remove("rework")
    CFG = CFG_RW


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, tierP, ent, epx, Rv, side, upv, be, chk_fill, patched):
    """scan_1028.sim, stop first. ent = P row of entry; epx = entry price (NaN = that row's close, else a limit fill price);
    chk_fill = the fill bar is checked for the stop (never the target). Per-trade R and target multiple.
    patched=True: 1c+1bp on every exit (targets too), +2c stop slip, gap-through stops fill at min(stop, high)/max(stop, low).
    patched=False reproduces the original (targets free, stop at the stop price).
    Codes: 1 target, 2 stop, 3 moved stop, 6 flatten 15:55. r in units of R, net of costs."""
    n = len(ent)
    r = np.full(n, np.nan)
    mfe_o = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    xrow = np.full(n, -1, np.int64)
    for q in range(n):
        i = ent[q]
        R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]
        e = c[i] if np.isnan(epx[q]) else epx[q]
        ec = (0.01 + e * 1e-4) * _mult(tod[i])
        stop = e - side * R
        tgt = e + side * upv[q] * R
        mfe = 0.0
        x, cd, xr = 0.0, 0, -1
        k0 = i + 1
        if chk_fill:
            adv = l[i] if side == 1 else h[i]
            if side * (adv - stop) <= 0:
                x, cd, xr = stop, 2, i
            k0 = i + 1
        if cd == 0:
            for k in range(k0, end + 1):
                adv = l[k] if side == 1 else h[k]
                fav = h[k] if side == 1 else l[k]
                if side * (adv - stop) <= 0:
                    x = stop
                    if patched:
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
        if cd == 1 and not patched:
            xc = 0.0
        else:
            xc = 0.01 + x * 1e-4 + (0.02 if (cd == 2 or cd == 3) else 0.0)
        r[q] = side * (x - e) / R - tierP[i] * (ec + xc) / R
        mfe_o[q], code[q], xrow[q] = mfe, cd, xr
    return r, mfe_o, code, xrow


@numba.njit(cache=True)
def _tgt(e, R, liq1, liq2, tmode):
    """Target multiple (in R) for a long-space entry e: nearest of the two liquidity levels >= 1R above, cap 4; else 2R."""
    if tmode == 1:
        return 2.0
    if tmode == 2:
        return 1.0
    best = np.inf
    for v in (liq1, liq2):
        if np.isfinite(v):
            d = (v - e) / R
            if d >= 1.0 and d < best:
                best = d
    if not np.isfinite(best):
        return 2.0
    return min(best, 4.0)


@numba.njit(cache=True)
def signals(ss, se, h, l, c, mins, atr, lvl, dopen, liqA, need_open_beyond, sweep_from, depth, any_through, disp, g,
            tmode, retrace, stopk=0):
    """Long-space signals (shorts are passed negated). One candidate per segment.
    Returns per segment: entry fh row, entry price (NaN = row close), R, up multiple, sweep row, K-bar end row.
    HTF bar index of a row: (mins - 575) // 15 (0 = 09:35-09:45 rows ... 21 = 14:50-15:00)."""
    S = len(ss)
    o_row = np.full(S, -1, np.int64); o_px = np.full(S, np.nan); o_R = np.full(S, np.nan); o_up = np.full(S, np.nan)
    o_sw = np.full(S, -1, np.int64); o_k = np.full(S, -1, np.int64)
    for s in range(S):
        a, z = ss[s], se[s]
        L0 = lvl[s]
        A = atr[a]
        if not (np.isfinite(L0) and A > 0):
            continue
        if need_open_beyond and not (dopen[s] > L0):
            continue
        # HTF bars
        Hh = np.full(22, -np.inf); Ll = np.full(22, np.inf); Cc = np.full(22, np.nan); cnt = np.zeros(22, np.int64)
        last = np.full(22, -1, np.int64); first = np.full(22, -1, np.int64)
        for i in range(a, z + 1):
            b = (mins[i] - 575) // 15
            if b < 0 or b > 21:
                continue
            Hh[b] = max(Hh[b], h[i]); Ll[b] = min(Ll[b], l[i]); Cc[b] = c[i]; cnt[b] += 1; last[b] = i
            if first[b] < 0:
                first[b] = i
        # sweep row
        sw = -1
        for i in range(a, z + 1):
            if mins[i] < sweep_from:
                continue
            hit = (l[i] < L0) if any_through else (l[i] <= L0 - depth * A)
            if hit:
                sw = i
                break
        if sw < 0:
            continue
        sb = (mins[sw] - 575) // 15
        pre_hod = -np.inf
        for i in range(a, sw):
            pre_hod = max(pre_hod, h[i])
        if not np.isfinite(pre_hod):
            pre_hod = np.nan
        # first HTF FVG after the sweep
        for K in range(sb + 2, min(sb + 8, 21) + 1):
            if cnt[K] != 3 or cnt[K - 1] != 3 or cnt[K - 2] != 3:
                continue
            gap = Ll[K] - Hh[K - 2]
            if not (gap >= g * A and gap >= 0.02):
                continue
            # this is THE candidate; any failure ends the day
            endm = mins[last[K]]
            if endm < 10 * 60 + 15 or endm > 14 * 60:
                break
            O1 = Cc[K - 2]
            if not (Cc[K - 1] - O1 >= disp * A):
                break
            if not (Cc[K] > L0):
                break
            dlow = np.inf
            for b in range(0, K - 1):
                if cnt[b] > 0:
                    dlow = min(dlow, Ll[b])
            if Ll[K - 1] < dlow:
                break
            SL = min(dlow, Ll[K - 1], Ll[K])
            stop = SL - 0.02 * A if stopk == 0 else Ll[K - 2] - 0.02 * A
            if not retrace:
                e = Cc[K]
                R = e - stop
                if not (R >= 0.10 * A and R <= 1.0 * A):
                    break
                o_row[s] = last[K]; o_px[s] = np.nan; o_R[s] = R
                o_up[s] = _tgt(e, R, liqA[s], pre_hod, tmode)
                o_sw[s] = sw; o_k[s] = last[K]
            else:
                lim = Ll[K]
                R = lim - stop
                if not (R >= 0.10 * A and R <= 1.0 * A):
                    break
                up = _tgt(lim, R, liqA[s], pre_hod, tmode)
                tgt = lim + up * R
                j0 = last[K]
                for j in range(j0 + 1, min(j0 + 6, z) + 1):
                    if mins[j] - mins[j - 1] != 5:
                        break
                    if l[j] <= lim - 0.01:
                        o_row[s] = j; o_px[s] = lim; o_R[s] = R; o_up[s] = up; o_sw[s] = sw; o_k[s] = j0
                        break
                    if h[j] >= tgt:
                        break
            break
    return o_row, o_px, o_R, o_up, o_sw, o_k


def month_frames(month):
    assert month not in lib.LOCKED_MONTHS and month not in ("2026-04", "2026-05", "2026-06", "2026-10")
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    return f, fh, P, dend, fh2P, ds


def seg_arrays(fh, ds):
    fsym, fdat = fh["symbol"].to_numpy(), ds.to_numpy()
    tod = fh["tod"].to_numpy(np.int64)
    mins = (tod // 100) * 60 + tod % 100
    h, l, c = (fh[k].to_numpy(float) for k in ("high", "low", "close"))
    atr = fh["atr_d"].to_numpy(float)
    key = fsym.astype(object) + "|" + fdat.astype(object)
    new = np.r_[True, key[1:] != key[:-1]]
    ss = np.flatnonzero(new); se = np.r_[ss[1:] - 1, len(fh) - 1]
    seg = np.cumsum(new) - 1
    satr = pd.Series(atr).groupby(seg).max().to_numpy()
    atr_seg = satr[seg]  # day-constant ATR on every row (head rows carry it too)
    with np.errstate(invalid="ignore"):
        fo = fh["fromOpen"].to_numpy(float)
        dop = pd.Series(c / (1 + fo / 100)).groupby(seg).first().to_numpy()
        pdl = pd.Series(c - fh["dist_pdl_atr"].to_numpy(float) * atr).groupby(seg).median().to_numpy()
        pdh = pd.Series(c + fh["dist_pdh_atr"].to_numpy(float) * atr).groupby(seg).median().to_numpy()
    hd = fh["tod"].isin([935, 940, 945]).to_numpy()
    g3 = pd.DataFrame({"seg": seg[hd], "h": h[hd], "l": l[hd]}).groupby("seg").agg(n=("h", "size"), H=("h", "max"), L=("l", "min"))
    orh = np.full(len(ss), np.nan); orl = np.full(len(ss), np.nan)
    ok3 = g3["n"].to_numpy() == 3
    orh[g3.index[ok3]] = g3["H"].to_numpy()[ok3]; orl[g3.index[ok3]] = g3["L"].to_numpy()[ok3]
    with np.errstate(invalid="ignore"):
        bad = ~((orh - orl) >= 0.05 * satr)
    orh[bad] = np.nan; orl[bad] = np.nan
    return dict(fsym=fsym, fdat=fdat, tod=tod, mins=mins, h=h, l=l, c=c, atr=atr_seg, key=key, ss=ss, se=se, seg=seg,
                dop=dop, pdl=pdl, pdh=pdh, orh=orh, orl=orl)


def run_signal(X, sk, tmode, retrace, stopk=0):
    """Signals for one SIG key in real price space. Returns fh row, entry price (NaN = close), R, up, sweep row."""
    lv, side, depth, disp, g = SIG[sk]
    if side == 1:
        h, l, c = X["h"], X["l"], X["c"]
        lvl = X["pdl"] if lv == "PD" else X["orl"]
        dop, liqA = X["dop"], X["pdh"]
    else:  # mirror: negate prices
        h, l, c = -X["l"], -X["h"], -X["c"]
        lvl = -(X["pdh"] if lv == "PD" else X["orh"])
        dop, liqA = -X["dop"], -X["pdl"]
    if lv == "OR":  # ORL/ORH sweeps need a defined OR15 regardless
        lvl = np.where(np.isfinite(X["orh"]), lvl, np.nan)
    row, px, R, up, sw, kr = signals(X["ss"], X["se"], np.ascontiguousarray(h), np.ascontiguousarray(l), np.ascontiguousarray(c),
                                     X["mins"], X["atr"], lvl, dop, liqA, lv == "PD", 575 if lv == "PD" else 590,
                                     0.0 if depth is None else depth, depth is None, disp, g, tmode, retrace, stopk)
    m = row >= 0
    px = px[m] * (1 if side == 1 else -1)
    return row[m], px, R[m], up[m], sw[m], side


def month_job(month):
    t0 = time.time()
    f, fh, P, dend, fh2P, ds = month_frames(month)
    X = seg_arrays(fh, ds)
    sp = f[f["symbol"] == "SPY"]
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last()  # EOD: descriptive split only
    fsym, fdat, tod, c = X["fsym"], X["fdat"], X["tod"], X["c"]
    atr = X["atr"]
    adv = fh["adv20"].fillna(0).to_numpy(float)
    with np.errstate(invalid="ignore"):
        tier = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
    univ = (adv >= 95e6) & (atr > 0)
    tierP = np.ones(len(P)); tierP[fh2P] = tier
    hP, lP, cP, todP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    pool_idx = np.flatnonzero(univ & (tod >= 950))
    pkey = (pd.Series(fdat[pool_idx]).astype(str) + "|" + pd.Series(tod[pool_idx]).astype(str)).to_numpy()
    pk = {k: np.asarray(v) for k, v in pd.Series(pool_idx).groupby(pkey)}
    rng = np.random.default_rng(SEED + zlib.crc32(month.encode()))
    rows = []
    ctx = lib.load_context(month)
    qfo = pd.Series(ctx["qqq_fo"].to_numpy(float), index=ctx["date"].astype(str) + "|" + ctx["tod"].astype(str))
    for cid, cf in CFG.items():
        sk, ret, tmode, be, gate, stopk = (tuple(cf) + (None, 0))[:6]
        i, px, R, up, sw, side = run_signal(X, sk, tmode, ret, stopk)
        keep = univ[i]
        if gate is not None:
            qv = qfo.reindex(pd.Series(fdat[i]).astype(str) + "|" + pd.Series(tod[i]).astype(str)).to_numpy(float)
            with np.errstate(invalid="ignore"):
                keep &= (side * qv >= gate)
        i, px, R, up, sw = i[keep], px[keep], R[keep], up[keep], sw[keep]
        e = np.where(np.isnan(px), c[i], px)
        ra = R / atr[i]
        cst = ((0.01 + e * 1e-4) * np.where(tod[i] < 1030, 1.4, 1.0) + 0.01 + e * 1e-4) * tier[i] / R
        r, mfe, code, xr = sim(hP, lP, cP, todP, dend, tierP, fh2P[i], px, R, side, up, be, bool(ret), True)
        ctrl = np.full(len(i), np.nan)
        ce, cR, cu, cq = [], [], [], []
        for q in range(len(i)):
            cand = pk.get(fdat[i[q]] + "|" + str(tod[i[q]]))
            if cand is None:
                continue
            cand = cand[cand != i[q]]
            if not len(cand):
                continue
            pick = rng.choice(cand, size=min(K_CTRL, len(cand)), replace=False)
            ce.extend(fh2P[pick]); cR.extend(ra[q] * atr[pick]); cu.extend([up[q]] * len(pick)); cq.extend([q] * len(pick))
        if ce:
            rc = sim(hP, lP, cP, todP, dend, tierP, np.asarray(ce, np.int64), np.full(len(ce), np.nan), np.asarray(cR, float),
                     side, np.asarray(cu, float), be, False, True)[0]
            ctrl = pd.Series(rc).groupby(np.asarray(cq)).mean().reindex(range(len(i))).to_numpy()
        rows.append(pd.DataFrame({"cfg": cid, "side": "L" if side == 1 else "S", "date": fdat[i], "symbol": fsym[i],
                                  "tod": tod[i].astype(np.int16), "sw_tod": tod[sw].astype(np.int16), "r": r, "code": code,
                                  "mfe": mfe, "up": up, "R_atr": ra, "cost_R": cst, "ctrl": ctrl,
                                  "spy_day": spy_day.reindex(fdat[i]).to_numpy(float)}))
    T = pd.concat(rows, ignore_index=True)
    meta = {"month": month, "sessions": int(len(np.unique(fdat))),
            "liquid_symbol_days": int(len(np.unique(X["key"][univ]))), "secs": round(time.time() - t0)}
    print(json.dumps(meta), len(T), flush=True)
    return T, meta


def sanity(month="2025-06"):
    """Signal features only (no outcome column): trades/session, R/ATR, cost/R, entry time, DOL share."""
    f, fh, P, dend, fh2P, ds = month_frames(month)
    X = seg_arrays(fh, ds)
    adv = fh["adv20"].fillna(0).to_numpy(float)
    univ = (adv >= 95e6) & (X["atr"] > 0)
    nsess = len(np.unique(X["fdat"]))
    nsd = len(np.unique(X["key"][univ]))
    print(f"{month}: sessions {nsess}, liquid symbol-days {nsd}")
    for cid in ("F4-01", "F4-03", "F4-05", "F4-07", "F4-09", "F4-12", "F4-14", "F4-15", "F4-16"):
        sk, ret, tmode, be = CFG[cid]
        i, px, R, up, sw, side = run_signal(X, sk, tmode, ret)
        k = univ[i]; i, px, R, up, sw = i[k], px[k], R[k], up[k], sw[k]
        e = np.where(np.isnan(px), X["c"][i], px)
        cst = ((0.01 + e * 1e-4) * np.where(X["tod"][i] < 1030, 1.4, 1.0) + 0.01 + e * 1e-4) / R
        print(f"{cid} {sk:8s} n {len(i):5d} per-sess {len(i)/nsess:6.2f} per-symday {len(i)/max(nsd,1):.4f} "
              f"medR/ATR {np.median(R/X['atr'][i]) if len(i) else np.nan:.3f} medcost/R {np.median(cst) if len(i) else np.nan:.3f} "
              f"med tod {np.median(X['tod'][i]) if len(i) else np.nan:.0f} med sweep tod {np.median(X['tod'][sw]) if len(i) else np.nan:.0f} "
              f"DOL share {np.mean(up != 2.0) if len(i) else np.nan:.2f} med up {np.median(up) if len(i) else np.nan:.2f}")


def sim_check(month="2025-06"):
    from scan_1028 import sim as sim0
    f, fh, P, dend, fh2P, ds = month_frames(month)
    tierP = np.ones(len(P))
    hP, lP, cP, todP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    rng = np.random.default_rng(1)
    i = np.sort(rng.choice(np.flatnonzero((fh["tod"].to_numpy() >= 1015) & (fh["tod"].to_numpy() <= 1400)), 20000, replace=False))
    ent = fh2P[i]; R = 0.3 * fh["atr_d"].to_numpy(float)[i]
    a = sim(hP, lP, cP, todP, dend, tierP, ent, np.full(len(i), np.nan), R, 1, np.full(len(i), 2.0), 0.0, False, False)[0]
    b = sim0(hP, lP, cP, todP, dend, tierP, ent, R, 1, 2.0, 1.0, 0, 0, 0.0, 0.0, 0.0, 0.5, 1555, 0.0)[0]
    ok = np.isfinite(a) | np.isfinite(b)
    d = np.nanmax(np.abs(a[ok] - b[ok]))
    print("sim_check max |diff|", d, "n", ok.sum())
    return d


def parity():
    """F4-18: CWT14 p05 long, unpatched scan_1028.sim, as pdl1030/combo/build.py (parent exits P)."""
    from scan_1019 import S6, CL
    from scan_1028 import sim as sim0
    from mcf.research import gates
    out = []
    for month in MONTHS:
        f, fh, P, dend, fh2P, ds = month_frames(month)
        with np.errstate(invalid="ignore"):
            tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
        tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
        h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
        x = CL.arrays(fh); lev = S6.levels(x)
        fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
        adv = fh["adv20"].fillna(0).to_numpy()
        risk = 0.25 * fh["atr_d"].to_numpy(float)
        with np.errstate(invalid="ignore"):
            base = (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
            m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=np.inf), 0.05), bool)
        mm = m & base & (ftod >= 950) & (ftod <= 1500)
        e1 = gates.first_per_symbol_day(fsym, fdat, mm)
        ent = fh2P[e1].astype(np.int64); Rv = risk[e1]
        res = sim0(h, l, c, tod, dend, tierP, ent, Rv, 1, 0.5, 1.0, 0, 0, 0.0, 0.0, 0.25, 0.5, 1555, 0.0)
        out.append(pd.DataFrame({"date": fdat[e1], "r": res[0]}))
        print(month, len(e1), flush=True)
    T = pd.concat(out, ignore_index=True)
    tr = T[T["date"] <= "2025-12-31"]["r"].mean(); va = T[T["date"] > "2025-12-31"]["r"].mean()
    ok = abs(tr - (-0.0677)) <= 0.002 and abs(va - (-0.0675)) <= 0.002
    res = {"n": len(T), "train": round(tr, 4), "valid": round(va, 4), "ref": [-0.0677, -0.0675], "ok": bool(ok)}
    (Path(__file__).resolve().parent / "parity.json").write_text(json.dumps(res))
    print(res)
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        assert sim_check() < 1e-9
        sys.exit()
    if sys.argv[1:] == ["parity"]:
        sys.exit(0 if parity() else 1)
    if sys.argv[1:] == ["sanity"]:
        sanity()
        sys.exit()
    metas = []
    mp = SCR / ("meta_rw.json" if REWORK else "meta.json")
    if mp.exists():
        metas = json.loads(mp.read_text())
    done = {m["month"] for m in metas}
    for m in sys.argv[1:] or MONTHS:
        if m in done:
            continue
        T, meta = month_job(m)
        T.to_parquet(SCR / (f"rw_{m}.parquet" if REWORK else f"tr_{m}.parquet"), index=False)
        metas.append(meta)
        mp.write_text(json.dumps(metas))
