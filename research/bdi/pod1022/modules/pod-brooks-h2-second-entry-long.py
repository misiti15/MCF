"""pod-brooks-h2-second-entry-long - Al Brooks High 2: second-attempt pullback buy near EMA20 on a trend day (LONG).

Source: Al Brooks (Brooks Trading Course, 'Two-legged pullback to the moving average'; Desire To Trade interview
2017; Speculators podcast); TradingView 'Price Action High 2'. Merged from pod-brooks-h2-second-entry and
pod-brooks-high2-trend-day-long.
URL: https://www.brookstradingcourse.com/blog/trading-strategies/

VARIANT of MP Ross micro-pullback (bdi-vid-micropullback-long, failed: first new-high candle), R09 (failed),
bdi-tg-p-pullback-vwap-long (failed: non-selective) and trend-pullback. Stated change: skip the first resumption
attempt (H1) and enter only on the second (H2) after a two-legged pullback, on a classified trend day, with an HOD
target. Side: LONG (this file). The SHORT mirror (L2 at the LOD) is pod-brooks-h2-second-entry-short.

Rules (plain English; long shown, short = exact mirror with LOD / L1 / L2):
  EMA20 = 20-bar EMA of the 5-minute close per symbol (spans previous days; seeded from the frame's SMA20 on the
  symbol's first row of the month). VWAP = close / (1 + vwapDistPct%). HOD so far = close + dist_hod_atr x atr_d.
  1. Trend day: >= 70% of the 5m closes from 10:00 up to this bar are above EMA20; sma20_slope_pct > 0;
     fromOpen >= +0.6 x atr_d / close (in %).
  2. Two-legged pullback from a swing high (the bar that set the HOD): first leg down, then H1 = the first bar whose
     high is above the prior bar's high without a new HOD; then a second leg with a low below the H1 bar's low.
     3-10 pullback bars between the swing high and the H2 bar. A new HOD resets the count.
  3. Leg-2 low within 0.2 x atr_d of EMA20 (at the leg-2 low bar) and above the session VWAP.
  4. H2: the first bar after leg 2 with high > the prior bar's high (no new HOD), closing in the upper half of its
     range. One attempt per pullback.
  Entry: the H2 close, bar close 10:00-14:30. Stop (GEOM S): leg-2 low - 0.025 x atr_d. Target: the HOD so far;
  skip when the HOD is < 0.5R above the entry. Flat 15:55. Costs per config/default.yaml (scorer).
Pre-declared choices (source ranges, set once, no tuning on valid): trend share 70% (range 70-75%), EMA proximity
0.2 x atr_d (range 0.15-0.3), stop buffer 0.025 x atr_d (range 0.02-0.03), target = HOD itself (the '+0.1 ATR'
extension is not used). No other tweak.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = []
LAYERS = [">= 70% of closes since 10:00 above EMA20, SMA20 slope > 0, fromOpen >= 0.6 ATR",
          "two-legged pullback: H1 then a lower low below the H1 bar low, 3-10 pullback bars, no new HOD",
          "leg-2 low within 0.2 ATR of EMA20 and above VWAP", "H2 bar: high > prior high, close in upper half",
          "stop leg-2 low - 0.025 ATR, target HOD (>= 0.5R)", "10:00-14:30 ET"]

TREND_SHARE = 0.70
EMA_NEAR = 0.20
STOP_BUF = 0.025

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _codes(df, by_day=True):
    s = pd.Series(df["symbol"].astype(str).to_numpy())
    if by_day:
        s = s + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _gcum(x, k):
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


@numba.njit(cache=False)
def _ema(b, e, c, seed, n):
    a = 2.0 / (n + 1.0)
    out = np.full(len(c), np.nan)
    for s in range(len(b)):
        v = np.nan
        for i in range(b[s], e[s]):
            if v != v:
                v = seed[i] if seed[i] == seed[i] else c[i]
            elif c[i] == c[i]:
                v = v + a * (c[i] - v)
            out[i] = v
    return out


@numba.njit(cache=False)
def _kernel(b, e, h, l, c, ext, ema, vw, atr, ok, near, buf):
    """Sign-normalised (short = negated prices, ext = -LOD). ext[i] = HOD so far including bar i."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        sh = -1
        state = -1
        h1low = np.nan
        l2 = np.nan
        l2ema = np.nan
        for i in range(i0 + 1, i1):
            if not (h[i] == h[i] and l[i] == l[i] and ext[i - 1] == ext[i - 1]):
                continue
            if h[i] >= ext[i - 1]:              # new HOD: new swing high, restart the count
                sh = i
                state = 0
                continue
            if sh < 0:
                continue
            if state == 0:
                if h[i] > h[i - 1]:
                    state = 1
                    h1low = l[i]
            elif state == 1:
                if l[i] < h1low:
                    state = 2
                    l2 = l[i]
                    l2ema = ema[i]
            elif state == 2:
                if h[i] > h[i - 1]:
                    state = 3                   # the H2 attempt (one per pullback)
                    npb = i - sh - 1
                    rng = h[i] - l[i]
                    if ok[i] and npb >= 3 and npb <= 10 and rng > 0 and (c[i] - l[i]) >= 0.5 * rng \
                            and abs(l2 - l2ema) <= near * atr[i] and l2 > vw[i]:
                        st = l2 - buf * atr[i]
                        risk = c[i] - st
                        t = ext[i]
                        if risk > 0 and t - c[i] >= 0.5 * risk:
                            m[i] = True
                            stop[i] = st
                            tgt[i] = t
                elif l[i] < l2:
                    l2 = l[i]
                    l2ema = ema[i]
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    long_ = SIDE == "long"
    sg = 1.0 if long_ else -1.0
    k = _codes(df, True)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        sma20 = c / (1 + _f(df, "sma20_dist_pct") / 100)
        bs, es = _segments(_codes(df, False))
        ema = _ema(bs, es, c, sma20, 20)
        vw = c / (1 + _f(df, "vwapDistPct") / 100)
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        after10 = tod >= 1000
        above = after10 & (sg * (c - ema) > 0)
        share = _gcum(above, k) / np.maximum(_gcum(after10, k), 1)
        ok = (share >= TREND_SHARE) & (sg * _f(df, "sma20_slope_pct") > 0)
        ok &= sg * _f(df, "fromOpen") >= 0.6 * atr / c * 100
        ok &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    if long_:
        H, L, C, X, E, V = h, l, c, hod, ema, vw
    else:
        H, L, C, X, E, V = -l, -h, -c, -lod, -ema, -vw
    b, e = _segments(k)
    m, stop, tgt = _kernel(b, e, H, L, C, X, E, V, atr, np.asarray(ok, np.bool_), EMA_NEAR, STOP_BUF)
    _ST[id(df)] = (sg * stop, sg * tgt)
    return np.asarray(m, dtype=bool)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)
