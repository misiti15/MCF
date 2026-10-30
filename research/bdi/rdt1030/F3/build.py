"""rdt1030/F3 orb5-be-2max build: OR5 break that completes a 5-min FVG, break-even, context gate, max 2 trades per
symbol-day (trade 2 after trade 1's exit, a close back inside the OR and a fresh break). Patched stop-first sim copied
from ../F1/build.py (DESIGN 0.2), K=5 random control, per-month trade parquet in scratch.
TRAIN+VALID only; HOLD months and the locked block are never loaded. Educational only - not financial advice.

    python build.py check      # patched sim copy == scan_1028.sim with patches off
    python build.py sanity     # 2025-06 counts / R_atr / cost_R only (no outcome column printed)
    python build.py [months]   # score months into scratch
"""
import os, sys, time, json, zlib
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numba
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT), str(ROOT / "research/bdi/rdt1030/F1"), str(ROOT / "research/bdi/top5_1028"),
                str(ROOT / "research/bdi/top5_1019"), str(ROOT / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa
from scan_1019 import lib, scan  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
REWORK = "rework" in sys.argv
if REWORK:
    sys.argv.remove("rework")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F3")
SCR.mkdir(parents=True, exist_ok=True)
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
HOLD = ("2026-04", "2026-05", "2026-06", "2026-10")
SEED, K_CTRL, G_FVG = 20261030, 5, 0.05
_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))
from scan_1019 import _mult  # noqa


# ---- verbatim copy of ../F1/build.py sim (top5_1028 sim + DESIGN 0.2 patches) ----
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




# id: (context 'qqq'|'spyvwap'|None, be, switch_atr, fixed_up, max_trades, trade2_only_after_loss, tod_hi)
CFG = {
    "F3-A": ("qqq", 1.0, 0.085, None, 2, False, 1100),
    "F3-B": (None, 1.0, 0.085, None, 2, False, 1100),
    "F3-C": ("qqq", 0.5, 0.085, None, 2, False, 1100),
    "F3-D": ("qqq", 1.0, 0.085, None, 1, False, 1100),
    "F3-E": ("qqq", 1.0, 0.085, None, 2, True, 1100),
    "F3-F": ("qqq", 1.0, 0.20, None, 2, False, 1100),
    "F3-G": ("qqq", 1.0, None, 2.0, 2, False, 1100),
    "F3-H": ("qqq", 1.0, 0.085, None, 2, False, 1500),
    "F3-I": ("spyvwap", 1.0, 0.085, None, 2, False, 1100),
}
if REWORK:
    CFG = json.loads((Path(__file__).resolve().parent / "rework_cfg.json").read_text())
    CFG = {k: tuple(v) for k, v in CFG.items()}


@numba.njit(cache=True)
def trade1(ss, se, tod, c, orh, orl, fvgL, fvgS, okL, okS):
    """Per segment: trade-1 row (-1 none), its side, and its break row. Per side only the first break (first close
    beyond after 0935) and its first FVG candidate (break row, or the next row with the close still beyond)."""
    ns = len(ss)
    i1 = np.full(ns, -1, np.int64); s1 = np.zeros(ns, np.int64); b1 = np.full(ns, -1, np.int64)
    for q in range(ns):
        a, z = ss[q], se[q]
        H, L = orh[q], orl[q]
        if not (np.isfinite(H) and np.isfinite(L)):
            continue
        best, bs, bb = -1, 0, -1
        for side in (1, -1):
            lvl = H if side == 1 else L
            b = -1
            for i in range(a, z + 1):
                if tod[i] > 935 and side * (c[i] - lvl) > 0:
                    b = i
                    break
            if b < 0:
                continue
            cand = -1
            for i in range(b, min(b + 1, z) + 1):
                if side * (c[i] - lvl) <= 0:
                    break
                f = fvgL[i] if side == 1 else fvgS[i]
                if f:
                    cand = i
                    break
            if cand < 0:
                continue
            ok = okL[cand] if side == 1 else okS[cand]
            if ok and (best < 0 or cand < best):
                best, bs, bb = cand, side, b
        i1[q], s1[q], b1[q] = best, bs, bb
    return i1, s1, b1


@numba.njit(cache=True)
def trade2(ss, se, c, orh, orl, fvgL, fvgS, okL, okS, b1, x1, allow):
    """Per segment: trade-2 row (-1 none) and side. After trade 1's break b1: a close inside [ORL, ORH] arms; the next
    close beyond either side is a new break; its first FVG candidate must be after trade 1's exit row x1 and pass gates."""
    ns = len(ss)
    i2 = np.full(ns, -1, np.int64); s2 = np.zeros(ns, np.int64)
    for q in range(ns):
        if not allow[q] or b1[q] < 0 or x1[q] < 0:
            continue
        z = se[q]
        H, L = orh[q], orl[q]
        armed = False
        k = b1[q] + 1
        while k <= z:
            if c[k] >= L and c[k] <= H:
                armed = True
                k += 1
                continue
            if not armed:
                k += 1
                continue
            armed = False
            side = 1 if c[k] > H else -1
            lvl = H if side == 1 else L
            cand = -1
            for i in range(k, min(k + 1, z) + 1):
                if side * (c[i] - lvl) <= 0:
                    break
                f = fvgL[i] if side == 1 else fvgS[i]
                if f:
                    cand = i
                    break
            if cand >= 0 and cand > x1[q] and (okL[cand] if side == 1 else okS[cand]):
                i2[q], s2[q] = cand, side
                break
            k += 1
    return i2, s2


def month_job(month, sanity=False):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in HOLD
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    sp = f[f["symbol"] == "SPY"]
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last()  # EOD: descriptive split only
    ctx = lib.load_context(month)[["date", "tod", "qqq_fo"]]
    ctx["date"] = ctx["date"].astype(str)
    spv = sp[["date", "tod", "vwapDistPct"]].rename(columns={"vwapDistPct": "spy_vw"})
    spv["date"] = spv["date"].astype(str)
    j = pd.DataFrame({"date": ds, "tod": fh["tod"].to_numpy()}).merge(ctx, on=["date", "tod"], how="left").merge(spv, on=["date", "tod"], how="left")
    qfo, spvw = j["qqq_fo"].to_numpy(float), j["spy_vw"].to_numpy(float)
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
    # OR5 = the 0935 row; 0935/0940/0945 must all be present
    hd = fh["tod"].isin([935, 940, 945]).to_numpy()
    nh = pd.Series(hd.astype(int)).groupby(seg).sum().reindex(range(len(ss)), fill_value=0).to_numpy()
    r935 = np.flatnonzero(tod == 935)
    orh = np.full(len(ss), np.nan); orl = np.full(len(ss), np.nan)
    orh[seg[r935]] = h[r935]; orl[seg[r935]] = l[r935]
    seg_atr = pd.Series(atr).groupby(seg).max().to_numpy()
    with np.errstate(invalid="ignore"):
        bad = (nh != 3) | ~((orh - orl) >= 0.05 * seg_atr)
    orh[bad] = np.nan; orl[bad] = np.nan
    # FVG completion flags per row (rows i-2, i-1, i consecutive in the segment)
    cons = np.zeros(len(fh), bool)
    cons[2:] = (seg[2:] == seg[:-2]) & (mins[2:] - mins[1:-1] == 5) & (mins[1:-1] - mins[:-2] == 5)
    gL = np.full(len(fh), -np.inf); gS = np.full(len(fh), -np.inf)
    gL[2:] = l[2:] - h[:-2]; gS[2:] = l[:-2] - h[2:]
    with np.errstate(invalid="ignore"):
        fvgL = cons & (gL >= G_FVG * atr) & (gL >= 0.02)
        fvgS = cons & (gS >= G_FVG * atr) & (gS >= 0.02)
    stopL = np.full(len(fh), np.nan); stopS = np.full(len(fh), np.nan)
    stopL[2:] = l[:-2]; stopS[2:] = h[:-2]
    RL, RS = c - stopL, stopS - c
    with np.errstate(invalid="ignore"):
        univ = (adv >= 95e6) & (atr > 0) & np.isfinite(orh[seg])
        gL_ok = univ & (RL / atr >= 0.03) & (RL / atr <= 1.0)
        gS_ok = univ & (RS / atr >= 0.03) & (RS / atr <= 1.0)
        ctxL = {"qqq": qfo > 0, "spyvwap": spvw > 0, None: np.ones(len(fh), bool), "qqq30": qfo >= 0.30,
                "qqq+spyvwap": (qfo > 0) & (spvw > 0)}
        ctxS = {"qqq": qfo < 0, "spyvwap": spvw < 0, None: np.ones(len(fh), bool), "qqq30": qfo <= -0.30,
                "qqq+spyvwap": (qfo < 0) & (spvw < 0)}
        rt = ((0.01 + c * 1e-4) * np.where(tod < 1030, 1.4, 1.0) + 0.01 + c * 1e-4) * tier
        cstL, cstS = rt / RL, rt / RS
    P2fh = P["_fhi"].to_numpy(np.int64)
    tierP = np.ones(len(P)); tierP[fh2P] = tier
    hP, lP, cP, todP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    pool_idx = np.flatnonzero(univ & (tod >= 950))
    pkey = (pd.Series(fdat[pool_idx]).astype(str) + "|" + pd.Series(tod[pool_idx]).astype(str)).to_numpy()
    pk = {k: np.asarray(v) for k, v in pd.Series(pool_idx).groupby(pkey)}
    rng = np.random.default_rng(SEED + zlib.crc32(month.encode()))
    first_break_lost = None

    def run(i, sd, be, sw, fix):
        """sim one batch of trades (rows i, sides sd); returns per-trade frame pieces and exit rows (fh index)."""
        stop = np.where(sd == 1, stopL[i], stopS[i])
        R = sd * (c[i] - stop)
        ra = R / atr[i]
        cst = ((0.01 + c[i] * 1e-4) * np.where(tod[i] < 1030, 1.4, 1.0) + 0.01 + c[i] * 1e-4) * tier[i] / R
        up = np.full(len(i), fix) if fix is not None else np.where(ra <= sw, 2.0, 1.0)
        out = {k: np.full(len(i), np.nan) for k in ("r", "mfe", "ctrl")}
        code = np.zeros(len(i), np.int8); xr = np.full(len(i), -1, np.int64)
        for side in (1, -1):
            m = np.flatnonzero(sd == side)
            if not len(m):
                continue
            r_, mfe_, code_, xr_ = sim(hP, lP, cP, todP, dend, tierP, fh2P[i[m]], R[m], side, up[m], be, True)
            out["r"][m], out["mfe"][m], code[m] = r_, mfe_, code_
            xr[m] = np.where(xr_ >= 0, P2fh[np.maximum(xr_, 0)], -1)
            ce, cR, cu, cq = [], [], [], []
            for q in m:
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
                         np.asarray(cu, float), be, True)[0]
                cm = pd.Series(rc).groupby(np.asarray(cq)).mean()
                out["ctrl"][cm.index.to_numpy()] = cm.to_numpy()
        return out, code, xr, up, ra, cst

    rows, sane = [], {}
    for cid, (cx, be, sw, fix, mx, after_loss, thi, *cc) in CFG.items():
        win = (tod >= 950) & (tod <= thi)
        okL = gL_ok & win & ctxL[cx]; okS = gS_ok & win & ctxS[cx]
        if cc and cc[0] is not None:
            with np.errstate(invalid="ignore"):
                okL &= cstL <= cc[0]; okS &= cstS <= cc[0]
        i1, s1, b1 = trade1(ss, se, tod, c, orh, orl, fvgL, fvgS, okL, okS)
        has = i1 >= 0
        o1, cd1, x1r, up1, ra1, cs1 = run(i1[has], s1[has], be, sw, fix)
        parts = [(1, i1[has], s1[has], o1, cd1, up1, ra1, cs1)]
        if mx >= 2:
            x1 = np.full(len(ss), -1, np.int64); x1[has] = x1r
            allow = has.copy()
            if after_loss:
                lost = np.zeros(len(ss), bool); lost[has] = o1["r"] < 0
                allow &= lost
            i2, s2 = trade2(ss, se, c, orh, orl, fvgL, fvgS, okL, okS, b1, x1, allow)
            h2 = i2 >= 0
            o2, cd2, _, up2, ra2, cs2 = run(i2[h2], s2[h2], be, sw, fix)
            parts.append((2, i2[h2], s2[h2], o2, cd2, up2, ra2, cs2))
        for tno, i, sd, o, cd, up, ra, cs in parts:
            rows.append(pd.DataFrame({"cfg": cid, "side": np.where(sd == 1, "L", "S"), "tno": np.int8(tno), "date": fdat[i],
                                      "symbol": fsym[i], "tod": tod[i].astype(np.int16), "r": o["r"], "code": cd, "mfe": o["mfe"],
                                      "up": up, "R_atr": ra, "cost_R": cs, "ctrl": o["ctrl"],
                                      "spy_day": spy_day.reindex(fdat[i]).to_numpy(float)}))
        if sanity and cid == "F3-B":
            # how many first breaks are lost to the window (break at 0940)
            firstL = np.array([ss[q] + np.argmax(c[ss[q]:se[q] + 1] > orh[q]) if np.isfinite(orh[q]) and (c[ss[q] + 1:se[q] + 1] > orh[q]).any() else -1 for q in range(len(ss))])
            fb = firstL[firstL >= 0]
            sane["first_long_break_tod_counts"] = pd.Series(tod[fb]).value_counts().sort_index().head(8).to_dict()
    T = pd.concat(rows, ignore_index=True)
    meta = {"month": month, "sessions": int(len(np.unique(fdat))), "liquid_symbol_days": int(len(np.unique(key[univ]))),
            "or5_w_med": float(np.nanmedian((orh - orl) / seg_atr)), "secs": round(time.time() - t0)}
    print(json.dumps(meta), len(T), flush=True)
    if sanity:
        print(json.dumps({k: {str(a): int(b) for a, b in v.items()} for k, v in sane.items()}))
        g = T.groupby(["cfg", "side", "tno"])
        print(pd.DataFrame({"n": g.size(), "per_session": (g.size() / meta["sessions"]).round(2),
                            "med_R_atr": g["R_atr"].median().round(3), "med_cost_R": g["cost_R"].median().round(3),
                            "share_2R": g["up"].apply(lambda u: (u == 2).mean()).round(3),
                            "med_tod": g["tod"].median()}).to_string())
    return T, meta


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        assert sim_check() < 1e-9  # F1's check: patched copy (patches off) == scan_1028.sim
        sys.exit()
    if sys.argv[1:] == ["sanity"]:
        month_job("2025-06", sanity=True)
        sys.exit()
    tag = "rw" if REWORK else "tr"
    mp = SCR / f"meta_{tag}.json"
    metas = json.loads(mp.read_text()) if mp.exists() else []
    done = {m["month"] for m in metas}
    for m in sys.argv[1:] or MONTHS:
        if m in done:
            continue
        T, meta = month_job(m)
        T.to_parquet(SCR / f"{tag}_{m}.parquet", index=False)
        metas.append(meta)
        mp.write_text(json.dumps(metas))
