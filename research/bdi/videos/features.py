"""Video-digest price-structure features (BDI 2026-10-08), one row per completed 5-minute bar, causal.

day_features(b1, p1, prior5, acv, atr) uses only:
  b1      today's RTH 1-minute bars so far (open/high/low/close/volume, tz-aware index)  -> ctx.bars
  p1      the prior session's RTH 1-minute bars (volume profile, prior-day anchors)      -> NOT in DayContext today
  prior5  the prior 40 five-minute bars (EMA warm-up)                                     -> ctx.prior5
  acv     prior-14-session average cumulative volume by minute of session (len 390)       -> ctx.avg_cum_volume
  atr     daily ATR as of the prior close                                                 -> ctx.atr
Every value at bar i uses bars that closed at or before bar i's close (checked by test_causal in build.py).

Columns (L = long side, S = short side):
  o5 h5 l5 c5 v5, h_p1 l_p1 c_p1 c_p2 v_p1      5-minute bar and its predecessors (today; NaN before the open)
  e9 e20 vw5                                    5-minute EMA9/EMA20 (prior5 warm-up), session VWAP of 5-minute typical price
  pbL_len pbL_de9 pbL_dvw pbL_hold pbL_vr       micro-pullback run before bar i (consecutive lower-high bars, cap 4):
                                                  min (low-EMA9)/ATR, min (low-VWAP)/ATR, min (close-VWAP)/ATR,
                                                  mean run volume / mean volume of the 3 bars before the run
  pbS_*                                         mirror (consecutive higher-low bars; distances measured above)
  hod_p lod_p vpk_p                             today's high / low / peak 5-minute volume BEFORE bar i
  uw lw                                         upper / lower wick share of the bar range
  pct_abv pct_blw                               share of today's 5-minute closes so far above / below VWAP
  m15                                           last completed 15-min bar: +1 close > 15-min EMA9 and > VWAP, -1 both below
  rvol                                          today's cumulative volume / acv at the bar's last minute
  orh orl                                       15-minute opening range (09:30-09:44) high / low
  day_open lod hod                              09:30 open, today's low / high including bar i
  ppoc pvah{60,70,80} pval{60,70,80}            prior-day 1-minute volume profile (contiguous value area)
  hh6 ll6                                       highest high / lowest low of the 6 bars before bar i
  airU_{25,50,75} airD_{25,50,75}               composite (prior day + today so far) profile: mean volume per bin over
                                                (close, close + k ATR] (resp. below), / POC-bin volume
  av_{A} sd_{A}                                 anchored VWAP and its volume-weighted SD, A in open/pdhv/pdh/pdl/tdhv
  rtL_{A}_{d} rtS_{A}_{d}                       1 on the FIRST touch of AVWAP after a >= d ATR departure, if it held
                                                (close back on the departure side); d in 20/30/50 (x0.01 ATR)
  bkL_{L}_{c}_{e} bkS_*                         block POC retest (lab entry): L bars, range <= c/100 ATR, extension e/100 ATR
  bpL_{L}_{c}_{e} bpS_*                         bar where the block's extension completed (limit order placed)
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

ANCHORS = ("open", "pdhv", "pdh", "pdl", "tdhv")
DEPS = (20, 30, 50)
BLK_L, BLK_C, BLK_E = (6, 12), (30, 50), (15, 25, 40)
VA_PCTS = (60, 70, 80)


def _resample5(b1: pd.DataFrame) -> pd.DataFrame:
    d5 = b1.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    return d5.dropna(subset=["open"])


def value_area(prof: np.ndarray, pcts=VA_PCTS):
    """POC index and contiguous value areas (expand from the POC toward the larger neighbour) for each pct."""
    tot = prof.sum()
    if tot <= 0:
        return -1, {p: (-1, -1) for p in pcts}
    poc = int(np.argmax(prof))
    lo = hi = poc
    acc = prof[poc]
    out, todo = {}, sorted(pcts)
    n = len(prof)
    while todo:
        while todo and acc >= tot * todo[0] / 100:
            out[todo.pop(0)] = (lo, hi)
        if not todo:
            break
        a = prof[hi + 1] if hi + 1 < n else -1.0
        b = prof[lo - 1] if lo - 1 >= 0 else -1.0
        if a < 0 and b < 0:
            for p in todo:
                out[p] = (lo, hi)
            break
        if a >= b:
            hi += 1
            acc += a
        else:
            lo -= 1
            acc += b
    return poc, out


def _spread(lo_px, hi_px, vol, org, binw, nb, row=None, nrow=1):
    """Distribute each bar's volume uniformly over the bins its range covers. Returns (nrow, nb)."""
    a = np.clip(np.floor((lo_px - org) / binw).astype(np.int64), 0, nb - 1)
    b = np.clip(np.floor((hi_px - org) / binw).astype(np.int64), 0, nb - 1)
    cnt = b - a + 1
    rep = np.repeat(np.arange(len(a)), cnt)
    off = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    bins = a[rep] + off
    w = (vol / cnt)[rep]
    r = np.zeros(len(a), np.int64) if row is None else row
    out = np.bincount(r[rep] * nb + bins, weights=w, minlength=nrow * nb)
    return out.reshape(nrow, nb)


def day_features(b1: pd.DataFrame, p1: pd.DataFrame | None, prior5: pd.DataFrame | None, acv: np.ndarray | None,
                 atr: float, aux: bool = False):
    o1, h1, l1, c1, v1 = (b1[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    mos = (b1.index.hour * 60 + b1.index.minute - 570).to_numpy()
    d5 = _resample5(b1)
    last_end = b1.index[-1] + pd.Timedelta(minutes=1)
    d5 = d5[d5.index + pd.Timedelta(minutes=5) <= last_end]
    n = len(d5)
    if n == 0:
        return (pd.DataFrame(), {}) if aux else pd.DataFrame()
    o5, h5, l5, c5, v5 = (d5[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    end_ts = d5.index + pd.Timedelta(minutes=5)
    tod = (end_ts.hour * 100 + end_ts.minute).to_numpy()
    # last 1-minute index inside each 5-minute bar
    m_end = np.searchsorted(mos, (d5.index.hour * 60 + d5.index.minute - 570).to_numpy() + 4, side="right") - 1
    X = {"tod": tod, "o5": o5, "h5": h5, "l5": l5, "c5": c5, "v5": v5}
    sh = lambda x, k=1: np.r_[np.full(k, np.nan), x[:-k]] if len(x) > k else np.full(len(x), np.nan)
    X["h_p1"], X["l_p1"], X["c_p1"], X["c_p2"], X["v_p1"] = sh(h5), sh(l5), sh(c5), sh(c5, 2), sh(v5)

    # EMAs with prior5 warm-up (same history LabStrategy builds)
    hist = d5 if prior5 is None or len(prior5) == 0 else pd.concat([prior5[["open", "high", "low", "close", "volume"]], d5])
    hc = hist["close"]
    e9 = hc.ewm(span=9, adjust=False).mean().to_numpy()[-n:]
    e20 = hc.ewm(span=20, adjust=False).mean().to_numpy()[-n:]
    typ5 = (h5 + l5 + c5) / 3
    cv5 = np.cumsum(v5)
    vw5 = np.cumsum(typ5 * v5) / np.where(cv5 > 0, cv5, np.nan)
    X["e9"], X["e20"], X["vw5"] = e9, e20, vw5
    A = atr if atr and atr > 0 else np.nan

    # micro-pullback runs
    for side, nm in ((1, "L"), (-1, "S")):
        ln = np.zeros(n)
        de9, dvw, hold, vr = (np.full(n, np.nan) for _ in range(4))
        for i in range(2, n):
            p = 0
            j = i - 1
            while j >= 1 and p < 5 and ((h5[j] <= h5[j - 1]) if side == 1 else (l5[j] >= l5[j - 1])):
                p += 1
                j -= 1
            if p == 0 or p > 4:
                ln[i] = p
                continue
            ln[i] = p
            run = slice(i - p, i)
            if side == 1:
                de9[i] = np.min(l5[run] - e9[run]) / A
                dvw[i] = np.min(l5[run] - vw5[run]) / A
                hold[i] = np.min(c5[run] - vw5[run]) / A
            else:
                de9[i] = np.min(e9[run] - h5[run]) / A
                dvw[i] = np.min(vw5[run] - h5[run]) / A
                hold[i] = np.min(vw5[run] - c5[run]) / A
            a0 = i - p - 3
            if a0 >= 0:
                base = v5[a0:i - p].mean()
                vr[i] = v5[run].mean() / base if base > 0 else np.nan
        X[f"pb{nm}_len"], X[f"pb{nm}_de9"], X[f"pb{nm}_dvw"], X[f"pb{nm}_hold"], X[f"pb{nm}_vr"] = ln, de9, dvw, hold, vr

    X["hod_p"] = sh(np.maximum.accumulate(h5))
    X["lod_p"] = sh(np.minimum.accumulate(l5))
    X["vpk_p"] = sh(np.maximum.accumulate(v5))
    rng = np.where(h5 > l5, h5 - l5, np.nan)
    X["uw"] = (h5 - np.maximum(o5, c5)) / rng
    X["lw"] = (np.minimum(o5, c5) - l5) / rng
    k = np.arange(1, n + 1)
    X["pct_abv"] = np.cumsum(c5 > vw5) / k
    X["pct_blw"] = np.cumsum(c5 < vw5) / k
    X["hod"], X["lod"] = np.maximum.accumulate(h5), np.minimum.accumulate(l5)
    X["day_open"] = np.full(n, o1[0])

    # 15-minute alignment: completed 15-minute bars of (prior5 + today)
    h15 = hist.resample("15min", label="left", closed="left").agg({"close": "last", "open": "count"}).dropna()
    h15 = h15[h15["open"] >= 3]
    e15 = h15["close"].ewm(span=9, adjust=False).mean()
    end15 = h15.index + pd.Timedelta(minutes=15)
    pos = np.searchsorted(end15.values, end_ts.values, side="right") - 1
    m15 = np.zeros(n)
    for i in range(n):
        if pos[i] < 0:
            continue
        t_end = end15[pos[i]]
        if t_end <= d5.index[0]:
            continue                                   # last completed 15-min bar is from a prior day
        jj = np.searchsorted(end_ts.values, t_end.to_datetime64())
        if jj >= n or end_ts[jj] != t_end:
            continue
        cc, ee, vv = h15["close"].iloc[pos[i]], e15.iloc[pos[i]], vw5[jj]
        m15[i] = 1 if (cc > ee and cc > vv) else (-1 if (cc < ee and cc < vv) else 0)
    X["m15"] = m15

    # RVOL (cumulative)
    cumv = np.cumsum(v1)
    if acv is not None and len(acv) > 0:
        mm = np.clip(mos[m_end], 0, len(acv) - 1)
        den = np.asarray(acv, float)[mm]
        X["rvol"] = cumv[m_end] / np.where(den > 0, den, np.nan)
    else:
        X["rvol"] = np.full(n, np.nan)
    orm = mos < 15
    X["orh"] = np.full(n, h1[orm].max() if orm.any() else np.nan)
    X["orl"] = np.full(n, l1[orm].min() if orm.any() else np.nan)
    X["orh"][tod < 950] = np.nan
    X["orl"][tod < 950] = np.nan
    X["hh6"] = pd.Series(h5).shift(1).rolling(6).max().to_numpy()
    X["ll6"] = pd.Series(l5).shift(1).rolling(6).min().to_numpy()

    # ---- volume profiles (1-minute bars, uniform over each bar's range)
    have_p = p1 is not None and len(p1) > 30 and np.isfinite(A)
    binw = max(0.01, A / 40) if np.isfinite(A) else 0.01
    if have_p:
        ph1, pl1, pv1 = (p1[k].to_numpy(float) for k in ("high", "low", "volume"))
        lo0, hi0 = min(pl1.min(), o1[0]) - 4 * A, max(ph1.max(), o1[0]) + 4 * A
    else:
        lo0, hi0 = o1[0] - 6 * A if np.isfinite(A) else o1[0] * 0.9, o1[0] + 6 * A if np.isfinite(A) else o1[0] * 1.1
    org = np.floor(lo0 / binw) * binw
    nb = int(min(4000, np.ceil((hi0 - org) / binw) + 1))
    binw = max(binw, (hi0 - org) / (nb - 1))
    ctr = org + (np.arange(nb) + 0.5) * binw
    if have_p:
        pprof = _spread(pl1, ph1, pv1, org, binw, nb)[0]
        poc, va = value_area(pprof)
        X["ppoc"] = np.full(n, ctr[poc])
        for p in VA_PCTS:
            X[f"pvah{p}"] = np.full(n, org + (va[p][1] + 1) * binw)
            X[f"pval{p}"] = np.full(n, org + va[p][0] * binw)
    else:
        pprof = np.zeros(nb)
        X["ppoc"] = np.full(n, np.nan)
        for p in VA_PCTS:
            X[f"pvah{p}"] = X[f"pval{p}"] = np.full(n, np.nan)
    # composite profile at each 5-minute close
    bar5 = np.searchsorted(m_end, np.arange(len(mos)), side="left")      # 5-minute bar of every minute
    keep = bar5 < n
    today = _spread(l1[keep], h1[keep], v1[keep], org, binw, nb, row=bar5[keep], nrow=n)
    comp = np.cumsum(today, axis=0) + pprof[None, :]
    pocv = comp.max(axis=1)
    cs = np.concatenate([np.zeros((n, 1)), np.cumsum(comp, axis=1)], axis=1)
    cb = np.clip(np.floor((c5 - org) / binw).astype(int), 0, nb - 1)
    for kk in (25, 50, 75):
        w = max(1, int(round(kk / 100 * A / binw))) if np.isfinite(A) else 1
        up_hi = np.clip(cb + 1 + w, 0, nb)
        up_lo = np.clip(cb + 1, 0, nb)
        dn_lo = np.clip(cb - w, 0, nb)
        rr = np.arange(n)
        su = cs[rr, up_hi] - cs[rr, up_lo]
        sd = cs[rr, cb] - cs[rr, dn_lo]
        X[f"airU_{kk}"] = np.where(up_hi - up_lo > 0, su / np.maximum(up_hi - up_lo, 1), np.nan) / np.where(pocv > 0, pocv, np.nan)
        X[f"airD_{kk}"] = np.where(cb - dn_lo > 0, sd / np.maximum(cb - dn_lo, 1), np.nan) / np.where(pocv > 0, pocv, np.nan)

    # ---- anchored VWAPs (prefix sums over prior day + today, 1-minute typical price)
    typ1 = (h1 + l1 + c1) / 3
    if have_p:
        pt = (p1["high"].to_numpy(float) + p1["low"].to_numpy(float) + p1["close"].to_numpy(float)) / 3
        T = np.r_[pt, typ1]
        V = np.r_[pv1, v1]
        off = len(pt)
    else:
        T, V, off = typ1, v1, 0
    cV = np.r_[0.0, np.cumsum(V)]
    cTV = np.r_[0.0, np.cumsum(T * V)]
    cT2V = np.r_[0.0, np.cumsum(T * T * V)]

    def line(anchor_idx, upto):
        """AVWAP and SD from global minute anchor_idx through upto (arrays of global indices)."""
        vv = cV[upto + 1] - cV[anchor_idx]
        vv = np.where(vv > 0, vv, np.nan)
        m = (cTV[upto + 1] - cTV[anchor_idx]) / vv
        var = (cT2V[upto + 1] - cT2V[anchor_idx]) / vv - m * m
        return m, np.sqrt(np.clip(var, 0, None))

    nm1 = len(mos)
    run_tdhv = np.full(nm1, -1)
    best, bi = -1.0, -1
    for t in range(nm1):
        if mos[t] >= 5 and v1[t] > best:
            best, bi = v1[t], t
        run_tdhv[t] = bi
    anchors = {"open": np.full(nm1, off)}
    if have_p:
        anchors["pdhv"] = np.full(nm1, int(np.argmax(pv1)))
        anchors["pdh"] = np.full(nm1, int(np.argmax(ph1)))
        anchors["pdl"] = np.full(nm1, int(np.argmin(pl1)))
    anchors["tdhv"] = np.where(run_tdhv >= 0, run_tdhv + off, -1)
    lines = {}
    for a in ANCHORS:
        if a not in anchors:
            X[f"av_{a}"] = X[f"sd_{a}"] = np.full(n, np.nan)
            for d in DEPS:
                X[f"rtL_{a}_{d}"] = X[f"rtS_{a}_{d}"] = np.zeros(n, np.int8)
            continue
        an = anchors[a]
        g = np.arange(nm1) + off
        ok = an >= 0
        mline, sline = np.full(nm1, np.nan), np.full(nm1, np.nan)
        mline[ok], sline[ok] = line(an[ok], g[ok])
        lines[a] = mline
        av, sd = mline[m_end], sline[m_end]
        X[f"av_{a}"], X[f"sd_{a}"] = av, sd
        tol = 0.02 * A
        for side, nm in ((1, "L"), (-1, "S")):
            dep = side * (c5 - av) / A
            dmax_prev = sh(np.fmax.accumulate(np.where(np.isfinite(dep), dep, -np.inf)))
            touch = (l5 <= av + tol) if side == 1 else (h5 >= av - tol)
            held = (c5 > av) if side == 1 else (c5 < av)
            for d in DEPS:
                cand = touch & (dmax_prev >= d / 100)
                f = np.zeros(n, np.int8)
                j = np.flatnonzero(cand)
                if len(j) and held[j[0]]:
                    f[j[0]] = 1
                X[f"rt{nm}_{a}_{d}"] = f

    # ---- accumulation blocks (Trader Dale): latest tight block, breakout, extension, first POC retest
    blk_aux = {}
    for L in BLK_L:
        for cpar in BLK_C:
            for e in BLK_E:
                for side, nm in ((1, "L"), (-1, "S")):
                    rt = np.zeros(n, np.int8)
                    bp = np.zeros(n, np.int8)
                    orders = []
                    blk, state, ext = None, 0, np.nan        # 0 armed, 1 broke, 2 extended, 3 done/dead
                    for i in range(n):
                        if blk is not None and np.isfinite(A):
                            hi_, lo_, pc_, val_, vah_ = blk
                            if state == 2:
                                if (l5[i] <= pc_ and c5[i] >= pc_) if side == 1 else (h5[i] >= pc_ and c5[i] <= pc_):
                                    rt[i] = 1
                                    state = 3
                                elif (c5[i] < val_) if side == 1 else (c5[i] > vah_):
                                    state = 3
                            elif state == 1:
                                ext = max(ext, h5[i]) if side == 1 else min(ext, l5[i])
                                if (c5[i] < lo_) if side == 1 else (c5[i] > hi_):
                                    state = 3
                                elif (ext >= hi_ + e / 100 * A) if side == 1 else (ext <= lo_ - e / 100 * A):
                                    state = 2
                                    bp[i] = 1
                                    orders.append((i, pc_, val_ if side == 1 else vah_, ext))
                            elif state == 0:
                                if (c5[i] > hi_) if side == 1 else (c5[i] < lo_):
                                    state = 1
                                    ext = h5[i] if side == 1 else l5[i]
                                    if (ext >= hi_ + e / 100 * A) if side == 1 else (ext <= lo_ - e / 100 * A):
                                        state = 2
                                        bp[i] = 1
                                        orders.append((i, pc_, val_ if side == 1 else vah_, ext))
                        # block update with the window ending at bar i (not while a breakout is live)
                        if i >= L - 1 and state in (0, 3) and np.isfinite(A):
                            hh, ll = h5[i - L + 1:i + 1].max(), l5[i - L + 1:i + 1].min()
                            if hh - ll <= cpar / 100 * A and rt[i] == 0:
                                mlo, mhi = (m_end[i - L] + 1 if i - L >= 0 else 0), m_end[i]
                                pr = _spread(l1[mlo:mhi + 1], h1[mlo:mhi + 1], v1[mlo:mhi + 1], org, binw, nb)[0]
                                pk, vva = value_area(pr, (70,))
                                lo70, hi70 = vva[70]
                                blk = (hh, ll, ctr[pk], org + lo70 * binw, org + (hi70 + 1) * binw)
                                state = 0
                    key = f"{L}_{cpar}_{e}"
                    X[f"bk{nm}_{key}"], X[f"bp{nm}_{key}"] = rt, bp
                    blk_aux[(nm, key)] = orders
    F = pd.DataFrame({k: (np.asarray(v, np.float32) if np.asarray(v).dtype.kind == "f" else v) for k, v in X.items()},
                     index=d5.index)
    if not aux:
        return F
    return F, {"m_end": m_end, "lines": lines, "blk": blk_aux, "mos": mos}
