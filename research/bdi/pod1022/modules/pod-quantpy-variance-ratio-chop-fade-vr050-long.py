"""pod-quantpy-variance-ratio-chop-fade-vr050-long - Variance-ratio chop gate: fade a 20-bar low to VWAP when today's tape
is mean-reverting (LONG).

Source: QuantPy YouTube (Hurst exponent / mean reversion vs trend tests in Python), with the Lo-MacKinlay variance
ratio as the stated test. Written from memory, URL not re-checked.
URL: https://www.youtube.com/@QuantPy

VARIANT of Reddit R03 VWAP rubber-band fade and R11 RSI oversold (both failed, not selective). Stated change: a new
feature family - a per-symbol, same-day variance-ratio regime gate (mean-reverting tape now) plus a quiet-SPY gate,
long only, with a structural VWAP target.
Rules (plain English):
  Universe adv20 >= $50M. Decision bar i, bar close 11:00-14:30.
  1. VR(4) = var(4-bar log returns) / (4 x var(1-bar log returns)), on today's 5-minute closes up to bar i
     (overlapping 4-bar returns, sample variances), needs >= 18 of today's bars in the frame; VR <= VR_MAX (0.50, second config).
  2. |spy_fo| <= 0.40% and 0.35 <= breadth <= 0.65.
  3. pricePosition <= 0.10 (at the 20-bar low), vwapDistPct between -1.5% and -0.5%, rsi5 <= 20.
  4. Trigger: close > previous close (first up close).
  Entry: close. Stop (GEOM S): 20-bar low (lows of the last 20 bars of the symbol, bar i included) - 0.05 x atr_d.
  Target: session VWAP at entry; skip the trade if it is < 0.8 x risk away. Flat 15:55.
Harness note: the frames start at the 09:50 bar, so today's 09:30-09:45 bars are not in the VR sample (the 18-bar
minimum is reached at the 11:15 bar).
Pre-declared configs (from the idea text, not tuned): primary VR <= 0.60; second config VR <= 0.50
(pod-quantpy-variance-ratio-chop-fade-vr050-long.py). This file is the pre-declared second config (the one tweak).
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
MIN_ADV = 50e6
VR_MAX = 0.50
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["same-day VR(4) <= VR_MAX (>= 18 bars)", "|spy_fo| <= 0.4, breadth 0.35-0.65",
          "pricePosition <= 0.10, vwapDist -1.5..-0.5, rsi5 <= 20", "close > previous close",
          "stop 20-bar low - 0.05 ATR, target VWAP (>= 0.8R)"]

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr          # prior completed day's low
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") * c / 100                # 5-minute ATR(14), $
    return b


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


@numba.njit(cache=False)
def _vr4_nb(lc, st):
    n = len(lc)
    out = np.full(n, np.nan)
    s1 = q1 = s4 = q4 = 0.0
    n1 = n4 = 0
    pos = 0
    for i in range(n):
        if st[i]:
            s1 = 0.0; q1 = 0.0; s4 = 0.0; q4 = 0.0
            n1 = 0; n4 = 0
            pos = 0
        else:
            pos += 1
            r = lc[i] - lc[i - 1]
            if np.isfinite(r):
                s1 += r; q1 += r * r; n1 += 1
            if pos >= 4:
                r4 = lc[i] - lc[i - 4]
                if np.isfinite(r4):
                    s4 += r4; q4 += r4 * r4; n4 += 1
        if pos + 1 >= 18 and n1 > 1 and n4 > 1:
            v1 = (q1 - s1 * s1 / n1) / (n1 - 1)
            v4 = (q4 - s4 * s4 / n4) / (n4 - 1)
            if v1 > 0:
                out[i] = v4 / (4 * v1)
    return out


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df or "breadth" not in df:
        return z
    b = _base(df)
    k, tod, c, l, atr = b["k"], b["tod"], b["c"], b["l"], b["atr"]
    sym = pd.factorize(df["symbol"].astype(str).to_numpy())[0]
    with np.errstate(invalid="ignore", divide="ignore"):
        vr = _vr4_nb(np.log(c), _start(k))
        m = vr <= VR_MAX                                                             # (1)
        m &= np.abs(_f(df, "spy_fo")) <= 0.40
        br = _f(df, "breadth")
        m &= (br >= 0.35) & (br <= 0.65)                                             # (2)
        vd = _f(df, "vwapDistPct")
        m &= (_f(df, "pricePosition") <= 0.10) & (vd >= -1.5) & (vd <= -0.5) & (_f(df, "rsi5") <= 20)   # (3)
        m &= c > _lag(c, k)                                                          # (4)
        low20 = pd.Series(l).groupby(sym).rolling(20, min_periods=20).min().reset_index(level=0, drop=True).sort_index().to_numpy(float)
        stop = low20 - 0.05 * atr
        tgt = b["vwap"]
        risk = c - stop
        m &= (risk > 0) & ((tgt - c) >= 0.8 * risk)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
