"""rdt1030/F1 orb15-fvg-break build: signals, patched stop-first sim, random control, per-month trade parquet (scratch).
TRAIN+VALID only; HOLD months and the locked block are never loaded. Educational only - not financial advice."""
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
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F1")
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

# signal families: (g, kmax, tod_hi); configs: id -> (signal key, target rule, cost cap)
SIG = {"A": (0.05, 1, 1100), "B": (0.02, 1, 1100), "C": (0.10, 1, 1100), "H": (0.05, 3, 1100), "I": (0.05, 1, 1500)}
CFG = {  # id: (sig, switch_atr or None, fixed_up or None, cost_cap)
    "F1-A": ("A", 0.085, None, None), "F1-B": ("B", 0.085, None, None), "F1-C": ("C", 0.085, None, None),
    "F1-D": ("A", 0.20, None, None), "F1-E": ("A", None, 1.0, None), "F1-F": ("A", None, 2.0, None),
    "F1-G": ("A", 0.085, None, 0.10), "F1-H": ("H", 0.085, None, None), "F1-I": ("I", 0.085, None, None),
}
CFG_RW = {  # amendment 2026-10-30 (PLAN.md), declared after the 18 rows failed
    "F1-RW1": ("A", 0.085, None, 0.05), "F1-RW2": ("C", 0.085, None, 0.10), "F1-RW3": ("A", None, 2.0, 0.10),
}
REWORK = "rework" in sys.argv
if REWORK:
    sys.argv.remove("rework")
    CFG = CFG_RW


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, tierP, ent, Rv, side, upv, be, patched):
    """top5_1028 sim, stop first, entry at the signal close (em=0), dn = 1 on a per-trade R, per-trade target multiple.
    patched=True: 1c+1bp on every exit (targets too) and gap-through stop fills at min(stop, high) / max(stop, low).
    patched=False reproduces the original's charging (targets free, stop at the stop price).
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
        e = c[i]
        ec = (0.01 + e * 1e-4) * _mult(tod[i])
        stop = e - side * R
        tgt = e + side * upv[q] * R
        mfe = 0.0
        x, cd, xr = 0.0, 0, -1
        for k in range(i + 1, end + 1):
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
def signals(ss, se, h, l, c, mins, tod, atr, orh, orl, side, g, kmax, tod_hi):
    """One candidate per symbol-day segment for one side: the first FVG completed at the fresh OR break (break bar = FVG
    candle 2 or 3), or within kmax rows after the break while every close stays beyond the level. -1 if none."""
    out = np.full(len(ss), -1, np.int64)
    for s in range(len(ss)):
        a, z = ss[s], se[s]
        lvl = orh[s] if side == 1 else orl[s]
        if not np.isfinite(lvl):
            continue
        b = -1
        for i in range(a, z + 1):
            if tod[i] >= 950 and side * (c[i] - lvl) > 0:
                b = i
                break
        if b < 0:
            continue
        for i in range(b, min(b + kmax, z) + 1):
            if side * (c[i] - lvl) <= 0:
                break
            if tod[i] > tod_hi:
                break
            if tod[i] < 955 or i - 2 < a:
                continue
            if mins[i] - mins[i - 1] != 5 or mins[i - 1] - mins[i - 2] != 5:
                continue
            gap = (l[i] - h[i - 2]) if side == 1 else (l[i - 2] - h[i])
            if gap >= g * atr[i] and gap >= 0.02:
                out[s] = i
                break
    return out


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in ("2026-04", "2026-05", "2026-06", "2026-10")
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    sp = f[f["symbol"] == "SPY"]
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last()  # EOD: descriptive split only
    fsym, fdat = fh["symbol"].to_numpy(), ds.to_numpy()
    tod = fh["tod"].to_numpy(np.int64)
    mins = (tod // 100) * 60 + tod % 100
    h, l, c = (fh[k].to_numpy(float) for k in ("high", "low", "close"))
    atr = fh["atr_d"].to_numpy(float)
    adv = fh["adv20"].fillna(0).to_numpy(float)
    with np.errstate(invalid="ignore"):
        tier = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
    key = fsym.astype(object) + "|" + fdat.astype(object)
    new = np.r_[True, key[1:] != key[:-1]]
    ss = np.flatnonzero(new); se = np.r_[ss[1:] - 1, len(fh) - 1]
    seg = np.cumsum(new) - 1
    # OR15 from the head rows; all three must be present
    hd = fh["tod"].isin([935, 940, 945]).to_numpy()
    g3 = pd.DataFrame({"seg": seg[hd], "h": h[hd], "l": l[hd]}).groupby("seg").agg(n=("h", "size"), H=("h", "max"), L=("l", "min"))
    orh = np.full(len(ss), np.nan); orl = np.full(len(ss), np.nan)
    ok3 = g3["n"].to_numpy() == 3
    orh[g3.index[ok3]] = g3["H"].to_numpy()[ok3]; orl[g3.index[ok3]] = g3["L"].to_numpy()[ok3]
    seg_atr = pd.Series(atr).groupby(seg).max().to_numpy()
    with np.errstate(invalid="ignore"):
        bad = ~((orh - orl) >= 0.05 * seg_atr)
    orh[bad] = np.nan; orl[bad] = np.nan
    orw = (orh - orl)[seg] / atr
    with np.errstate(invalid="ignore"):
        univ = (adv >= 95e6) & (atr > 0) & np.isfinite(orh[seg])
    tierP = np.ones(len(P)); tierP[fh2P] = tier
    hP, lP, cP, todP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    # control pool by (date, tod)
    pool_idx = np.flatnonzero(univ & (tod >= 955))
    pkey = (pd.Series(fdat[pool_idx]).astype(str) + "|" + pd.Series(tod[pool_idx]).astype(str)).to_numpy()
    pk = {k: v for k, v in pd.Series(pool_idx).groupby(pkey)}
    pk = {k: np.asarray(v) for k, v in pk.items()}
    rng = np.random.default_rng(SEED + zlib.crc32(month.encode()))
    rows = []
    sigcache = {}
    for sk, (g, kmax, thi) in SIG.items():
        for sn, side in (("L", 1), ("S", -1)):
            sigcache[(sk, side)] = signals(ss, se, h, l, c, mins, tod, atr, orh, orl, side, g, kmax, thi)
    for cid, (sk, sw, fix, ccap) in CFG.items():
        for sn, side in (("L", 1), ("S", -1)):
            i = sigcache[(sk, side)]
            i = i[i >= 0]
            stop = l[i - 2] if side == 1 else h[i - 2]
            R = side * (c[i] - stop)
            ra = R / atr[i]
            cst = ((0.01 + c[i] * 1e-4) * np.where(tod[i] < 1030, 1.4, 1.0) + 0.01 + c[i] * 1e-4) * tier[i] / R
            keep = univ[i] & (ra >= 0.03) & (ra <= 1.0)
            if ccap is not None:
                keep &= cst <= ccap
            i, R, ra, cst = i[keep], R[keep], ra[keep], cst[keep]
            up = np.full(len(i), fix) if fix is not None else np.where(ra <= sw, 2.0, 1.0)
            r, mfe, code, xr = sim(hP, lP, cP, todP, dend, tierP, fh2P[i], R, side, up, 0.0, True)
            # random control: 5 other universe symbols at the same signal row, same side / R in ATR / target multiple
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
                rc = sim(hP, lP, cP, todP, dend, tierP, np.asarray(ce, np.int64), np.asarray(cR, float), side,
                         np.asarray(cu, float), 0.0, True)[0]
                ctrl = pd.Series(rc).groupby(np.asarray(cq)).mean().reindex(range(len(i))).to_numpy()
            rows.append(pd.DataFrame({"cfg": cid, "side": sn, "date": fdat[i], "symbol": fsym[i], "tod": tod[i].astype(np.int16),
                                      "r": r, "code": code, "mfe": mfe, "up": up, "R_atr": ra, "cost_R": cst, "ctrl": ctrl,
                                      "or_w": orw[i], "spy_day": spy_day.reindex(fdat[i]).to_numpy(float)}))
    T = pd.concat(rows, ignore_index=True)
    meta = {"month": month, "sessions": int(len(np.unique(fdat))),
            "liquid_symbol_days": int(len(np.unique(key[univ]))), "secs": round(time.time() - t0)}
    print(json.dumps(meta), len(T), flush=True)
    return T, meta


def sim_check(month="2025-06"):
    """Patched copy with patches off == scan_1028.sim on F1-A long trades with a fixed 1R target."""
    from scan_1028 import sim as sim0
    f, fh, P, dend, fh2P = SC.build_paths(month)
    tierP = np.ones(len(P))
    hP, lP, cP, todP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    rng = np.random.default_rng(1)
    i = np.sort(rng.choice(np.flatnonzero((fh["tod"].to_numpy() >= 955) & (fh["tod"].to_numpy() <= 1100)), 20000, replace=False))
    ent = fh2P[i]; R = 0.1 * fh["atr_d"].to_numpy(float)[i]
    a = sim(hP, lP, cP, todP, dend, tierP, ent, R, 1, np.ones(len(i)), 0.0, False)[0]
    b = sim0(hP, lP, cP, todP, dend, tierP, ent, R, 1, 1.0, 1.0, 0, 0, 0.0, 0.0, 0.0, 0.5, 1555, 0.0)[0]
    ok = np.isfinite(a) | np.isfinite(b)
    d = np.nanmax(np.abs(a[ok] - b[ok]))
    print("sim_check max |diff|", d, "n", ok.sum())
    return d


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        assert sim_check() < 1e-9
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
