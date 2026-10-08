"""Volume II features (BDI 2026-10-08): multi-day anchored VWAPs, session POC, delta proxy, VWAP slope, sweeps,
profile boundaries, 30-minute value-area bars. One row per completed 5-minute bar, causal.

day_features2(b1, hist1, p1, atr, gapday_open_ts) uses:
  b1       today's RTH 1-minute bars so far                                  -> ctx.bars
  hist1    ALL prior RTH 1-minute bars since the earliest anchor (multi-day AVWAPs)  -> NOT in DayContext today
           (live would keep running sums per anchor: sum v, sum v*typ, sum v*typ^2 from each anchor bar)
  p1       prior session's 1-minute bars (composite profile)                  -> NOT in DayContext today
  anchors  dict name -> integer position in hist1 (pwh, pwl, gapday, qopen); chosen from data before today only
Columns:
  av_{pwh,pwl,gap,qop} sd_{...}   multi-day AVWAP and volume-weighted SD at the bar's last minute
  spoc                            today's session volume-profile POC (1-minute bars so far)
  dlt dlt_p1                      delta proxy: sum over the bar's 1-minute bars of sign(close - previous 1-min close) x
                                  volume, / bar volume (tick rule; first minute vs the prior session's last close)
  vsl                             abs(VWAP_i - VWAP_{i-6}) / ATR (30-minute VWAP slope; NaN for the first 6 bars)
  vw5 sd5                         session VWAP (1-minute typical price) and its volume-weighted SD
  swL_{x}_{m} swS_*               VWAP sweep then reclaim: a bar within the last m bars (incl. i) pierced VWAP by
                                  >= x/100 ATR from the trade side's opposite... see NOTES section 0b
  dlo dhi                         composite-profile density at the bar low / high bin, / POC-bin volume
  aDlo aUhi                       mean density over the 0.25 ATR below the low / above the high, / POC-bin volume
  c30a c30b h30a h30b l30a l30b   last (a) and previous (b) completed 30-minute bars (from 09:30)
  rtL_{pwh,pwl}_{d} rtS_*         first-touch AVWAP retest (same rule as features.py) for the prior-week anchors
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from features import _resample5, _spread, value_area

ANCH2 = ("pwh", "pwl", "gap", "qop")
SW_X, SW_M = (5, 10, 20), (1, 2, 3)
DEPS = (20, 30, 50)


def day_features2(b1, hist1, p1, atr, anchors, prev_close):
    o1, h1, l1, c1, v1 = (b1[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    mos = (b1.index.hour * 60 + b1.index.minute - 570).to_numpy()
    d5 = _resample5(b1)
    last_end = b1.index[-1] + pd.Timedelta(minutes=1)
    d5 = d5[d5.index + pd.Timedelta(minutes=5) <= last_end]
    n = len(d5)
    if n == 0:
        return pd.DataFrame()
    o5, h5, l5, c5, v5 = (d5[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    m_end = np.searchsorted(mos, (d5.index.hour * 60 + d5.index.minute - 570).to_numpy() + 4, side="right") - 1
    A = atr if atr and atr > 0 else np.nan
    X = {}
    sh = lambda x, k=1: np.r_[np.full(k, np.nan), x[:-k]] if len(x) > k else np.full(len(x), np.nan)

    # multi-day AVWAPs
    typ1 = (h1 + l1 + c1) / 3
    if hist1 is not None and len(hist1):
        ht = ((hist1["high"] + hist1["low"] + hist1["close"]) / 3).to_numpy(float)
        T, V, off = np.r_[ht, typ1], np.r_[hist1["volume"].to_numpy(float), v1], len(ht)
    else:
        T, V, off = typ1, v1, 0
    cV, cTV, cT2V = (np.r_[0.0, np.cumsum(x)] for x in (V, T * V, T * T * V))
    g = m_end + off
    for a in ANCH2:
        ai = anchors.get(a, -1)
        if ai is None or ai < 0:
            X[f"av_{a}"] = X[f"sd_{a}"] = np.full(n, np.nan)
            continue
        vv = cV[g + 1] - cV[ai]
        vv = np.where(vv > 0, vv, np.nan)
        m = (cTV[g + 1] - cTV[ai]) / vv
        X[f"av_{a}"] = m
        X[f"sd_{a}"] = np.sqrt(np.clip((cT2V[g + 1] - cT2V[ai]) / vv - m * m, 0, None))
    # session VWAP (1-minute typical) and SD
    sv, stv, st2 = np.cumsum(v1), np.cumsum(typ1 * v1), np.cumsum(typ1 * typ1 * v1)
    den = np.where(sv[m_end] > 0, sv[m_end], np.nan)
    vw = stv[m_end] / den
    X["vw1"] = vw
    X["sd1"] = np.sqrt(np.clip(st2[m_end] / den - vw * vw, 0, None))
    typ5 = (h5 + l5 + c5) / 3
    cv5 = np.cumsum(v5)
    vw5 = np.cumsum(typ5 * v5) / np.where(cv5 > 0, cv5, np.nan)
    X["vsl"] = np.abs(vw5 - sh(vw5, 6)) / A
    # delta proxy (tick rule)
    prevc = np.r_[prev_close if np.isfinite(prev_close) else o1[0], c1[:-1]]
    sv1 = np.sign(c1 - prevc) * v1
    csd = np.r_[0.0, np.cumsum(sv1)]
    start = np.r_[0, m_end[:-1] + 1]
    dl = (csd[m_end + 1] - csd[start]) / np.where(v5 > 0, v5, np.nan)
    X["dlt"], X["dlt_p1"] = dl, sh(dl)
    # sweeps of the 5-minute session VWAP (lab vwapDistPct basis)
    for side, nm in ((1, "L"), (-1, "S")):
        for x in SW_X:
            for mm in SW_M:
                f = np.zeros(n, np.int8)
                for i in range(1, n):
                    if not ((c5[i] > vw5[i]) if side == 1 else (c5[i] < vw5[i])):
                        continue
                    for j in range(i, max(0, i - mm + 1) - 1, -1):
                        pierce = (l5[j] <= vw5[j] - x / 100 * A) if side == 1 else (h5[j] >= vw5[j] + x / 100 * A)
                        if not pierce or j < 1:
                            continue
                        pre = (c5[j - 1] > vw5[j - 1]) if side == 1 else (c5[j - 1] < vw5[j - 1])
                        outside = all(((c5[k] <= vw5[k]) if side == 1 else (c5[k] >= vw5[k])) for k in range(j, i))
                        if pre and outside:
                            f[i] = 1
                            break
                X[f"sw{nm}_{x}_{mm}"] = f
    # profiles: session POC, composite densities
    binw = max(0.01, A / 40) if np.isfinite(A) else 0.01
    have_p = p1 is not None and len(p1) > 30 and np.isfinite(A)
    if have_p:
        ph1, pl1, pv1 = (p1[k].to_numpy(float) for k in ("high", "low", "volume"))
        lo0, hi0 = min(pl1.min(), o1[0]) - 4 * A, max(ph1.max(), o1[0]) + 4 * A
    else:
        lo0, hi0 = (o1[0] - 6 * A, o1[0] + 6 * A) if np.isfinite(A) else (o1[0] * 0.9, o1[0] * 1.1)
    org = np.floor(lo0 / binw) * binw
    nb = int(min(4000, np.ceil((hi0 - org) / binw) + 1))
    binw = max(binw, (hi0 - org) / (nb - 1))
    ctr = org + (np.arange(nb) + 0.5) * binw
    pprof = _spread(pl1, ph1, pv1, org, binw, nb)[0] if have_p else np.zeros(nb)
    bar5 = np.searchsorted(m_end, np.arange(len(mos)), side="left")
    keep = bar5 < n
    today = np.cumsum(_spread(l1[keep], h1[keep], v1[keep], org, binw, nb, row=bar5[keep], nrow=n), axis=0)
    X["spoc"] = ctr[np.argmax(today, axis=1)]
    comp = today + pprof[None, :]
    pocv = np.where(comp.max(axis=1) > 0, comp.max(axis=1), np.nan)
    cs = np.concatenate([np.zeros((n, 1)), np.cumsum(comp, axis=1)], axis=1)
    rr = np.arange(n)
    bl = np.clip(np.floor((l5 - org) / binw).astype(int), 0, nb - 1)
    bh = np.clip(np.floor((h5 - org) / binw).astype(int), 0, nb - 1)
    X["dlo"], X["dhi"] = comp[rr, bl] / pocv, comp[rr, bh] / pocv
    w = max(1, int(round(0.25 * A / binw))) if np.isfinite(A) else 1
    lo_a = np.clip(bl - w, 0, nb)
    X["aDlo"] = np.where(bl - lo_a > 0, (cs[rr, bl] - cs[rr, lo_a]) / np.maximum(bl - lo_a, 1), np.nan) / pocv
    hi_b = np.clip(bh + 1 + w, 0, nb)
    hi_a = np.clip(bh + 1, 0, nb)
    X["aUhi"] = np.where(hi_b - hi_a > 0, (cs[rr, hi_b] - cs[rr, hi_a]) / np.maximum(hi_b - hi_a, 1), np.nan) / pocv
    # last two completed 30-minute bars
    for k in ("c30a", "c30b", "h30a", "h30b", "l30a", "l30b"):
        X[k] = np.full(n, np.nan)
    b30 = (mos // 30)
    endm = mos[m_end]
    for i in range(n):
        done = (endm[i] + 1) // 30           # number of completed 30-minute bars
        for tag, q in (("a", done - 1), ("b", done - 2)):
            if q < 0:
                continue
            sel = (b30 == q) & (np.arange(len(mos)) <= m_end[i])
            if sel.any():
                X[f"c30{tag}"][i] = c1[sel][-1]
                X[f"h30{tag}"][i] = h1[sel].max()
                X[f"l30{tag}"][i] = l1[sel].min()
    # prior-week AVWAP first retest
    for a in ("pwh", "pwl"):
        av = X[f"av_{a}"]
        tol = 0.02 * A
        for side, nm in ((1, "L"), (-1, "S")):
            dep = side * (c5 - av) / A
            dmax_prev = sh(np.fmax.accumulate(np.where(np.isfinite(dep), dep, -np.inf)))
            touch = (l5 <= av + tol) if side == 1 else (h5 >= av - tol)
            held = (c5 > av) if side == 1 else (c5 < av)
            for d in DEPS:
                f = np.zeros(n, np.int8)
                j = np.flatnonzero(touch & (dmax_prev >= d / 100))
                if len(j) and held[j[0]]:
                    f[j[0]] = 1
                X[f"rt{nm}_{a}_{d}"] = f
    return pd.DataFrame({k: (np.asarray(v, np.float32) if np.asarray(v).dtype.kind == "f" else v) for k, v in X.items()},
                        index=d5.index)
