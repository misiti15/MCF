"""pod-three-push-deceleration-low-long - Three pushes down into the session low with shrinking legs (exhaustion),
LONG.

Source: Tradeciety 'three pushes / three drives' pattern articles + Axia Futures talks on momentum exhaustion (each
push weaker, less participation). Not re-fetched this round (web budget used up).
URL: https://www.tradeciety.com/

VARIANT of the backlog idea 'F3 mirror: bullish exhaustion long (rsi5<15, bull_div, lower wick)'. Change: an explicit
three-swing structure with shorter legs and less volume each time, instead of an RSI oscillator trigger.
Rules (plain English, 5-minute bars, same day only):
  Swing lows are 2-bar pivots (low below the 2 bars on each side), known only once the 2 bars after it have closed.
  1. The last three confirmed swing lows L1 > L2 > L3 lie inside the last 60 bars; L3 is the session low (nothing
     lower before or since, 09:30 bars included).
  2. Deceleration: the drop from the swing high between L2 and L3 (H2) to L3 is <= 0.8x the drop from the swing high
     between L1 and L2 (H1) to L2.
  3. Average volumeRatio of the push-3 bars (after H2 through L3) is <= 0.85x that of the push-2 bars (after H1
     through L2).
  4. The total decline from the first swing high (highest high of the 12 bars before L1) to L3 is >= 0.5 x ATR14d,
     and price is below session VWAP at entry. spy_fo >= -1.0% (skip when SPY is down more than 1% from its open).
  Entry: the first 5-minute close above the high of the L3 bar that is also above EMA9 (5m), once L3 is confirmed,
  bar close 10:30-14:30. Stop (GEOM S): L3 - 0.05 x ATR5m. Target: H2 (structural); skip the trade if H2 is less
  than 1R away. Flat 15:55.
Harness approximations: no raw volume in the frames, so push volume uses volumeRatio; '24-60 bars' is read as the
structure fitting in the last 60 bars. No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["three lower 2-bar pivot lows in 60 bars, L3 = session low", "leg 3 <= 0.8 x leg 2",
          "push-3 volumeRatio <= 0.85 x push-2", "decline >= 0.5 ATR, below VWAP, spy_fo >= -1",
          "first close above the L3 bar high and EMA9", "stop L3 - 0.05 ATR5m, target H2 (>= 1R)"]
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
def _scan(st, h, l, c, lod, atr, atr5, vr, ema9, vwd, sfo):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    piv = np.zeros(n, np.int64)
    npiv = 0
    gs = 0
    for i in range(n):
        if st[i]:
            gs = i
            npiv = 0
        j = i - 2                                     # pivot candidate confirmed by bar i
        if j - 2 >= gs:
            if l[j] < l[j - 1] and l[j] < l[j - 2] and l[j] < l[j + 1] and l[j] < l[j + 2]:
                piv[npiv] = j
                npiv += 1
        if npiv < 3:
            continue
        L1 = piv[npiv - 3]
        L2 = piv[npiv - 2]
        L3 = piv[npiv - 1]
        if i < L3 + 2 or i - L1 > 60:
            continue
        if not (l[L1] > l[L2] and l[L2] > l[L3]):
            continue
        tol = 1e-5 * c[i]
        if not (lod[i] >= l[L3] - tol):               # L3 is still the session low (incl. 09:30-09:45)
            continue
        # trigger: first close above the L3 bar high and EMA9, after L3
        if not (c[i] > h[L3] and c[i] > ema9[i]):
            continue
        first = True
        for t in range(L3 + 1, i):
            if c[t] > h[L3] and c[t] > ema9[t]:
                first = False
                break
        if not first:
            continue
        if not (vwd[i] < 0 and sfo[i] >= -1.0):
            continue
        # swing highs
        h1 = -1e18
        a1 = L1
        for t in range(L1 + 1, L2):
            if h[t] > h1:
                h1 = h[t]
                a1 = t
        h2 = -1e18
        a2 = L2
        for t in range(L2 + 1, L3):
            if h[t] > h2:
                h2 = h[t]
                a2 = t
        h0 = -1e18
        for t in range(max(gs, L1 - 12), L1):
            if h[t] > h0:
                h0 = h[t]
        if h1 < -1e17 or h2 < -1e17 or h0 < -1e17:
            continue
        if not ((h2 - l[L3]) <= 0.8 * (h1 - l[L2])):
            continue
        s2 = 0.0
        n2 = 0
        for t in range(a1 + 1, L2 + 1):
            s2 += vr[t]
            n2 += 1
        s3 = 0.0
        n3 = 0
        for t in range(a2 + 1, L3 + 1):
            s3 += vr[t]
            n3 += 1
        if n2 == 0 or n3 == 0 or not (s3 / n3 <= 0.85 * s2 / n2):
            continue
        if not (h0 - l[L3] >= 0.5 * atr[i]):
            continue
        sp = l[L3] - 0.05 * atr5[i]
        r = c[i] - sp
        if not (r > 0) or not (h2 - c[i] >= r):
            continue
        m[i] = True
        stop[i] = sp
        tgt[i] = h2
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c = b["k"], b["tod"], b["c"]
    sym = pd.factorize(df["symbol"].astype(str).to_numpy())[0]
    ema9 = pd.Series(c).groupby(sym).transform(lambda x: x.ewm(span=9, adjust=False).mean()).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        m, stop, tgt = _scan(_start(k), b["h"], b["l"], c, b["lod"], b["atr"], b["atr5"], _f(df, "volumeRatio"),
                             ema9, _f(df, "vwapDistPct"), _f(df, "spy_fo"))
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
