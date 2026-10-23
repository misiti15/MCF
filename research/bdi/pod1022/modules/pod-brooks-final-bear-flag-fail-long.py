"""pod-brooks-final-bear-flag-fail-long - Brooks 'final flag': a late tight bear flag breaks to a new LOD, fails, and
price reverses up (LONG).

Source: Al Brooks, Brooks Trading Course ('final flag' reversal in a late trend). A new setup from a channel already
mined (the existing Brooks ids are h2-second-entry and range-day-edge-fade). Written from memory, URL not re-checked.
URL: https://www.brookstradingcourse.com/

VARIANT of pod-of-trapped-breakout-stall-short (mirrored to the long side and with Brooks' late-trend / tight-flag
structure) and the CWT14 failed-breakdown longs. Stated change against CWT14: the level is the intraday flag low, not
PDL or the opening-range low, and a late (>= 11:00) established downtrend must come first.
Rules (plain English):
  Universe adv20 >= $50M.
  1. Late trend: at the first flag bar, fromOpen <= -1.5% and sma20_slope_pct < 0, and the flag starts at or after
     11:00 (first flag bar's start time).
  2. Flag: the 6-12 bars right after the last bar that printed the running LOD. Flag height (max high - min low)
     <= 0.30 x atr_d; by construction no flag bar makes a new LOD (so no close does either).
  3. Breakdown: the bar after the flag makes a new LOD, and its low is no more than 0.15 x atr_d below the flag low.
  4. Within the next 3 bars, the first close above the flag high (with no low under the breakdown low before it) is
     the trigger, bar close 11:30-14:45.
  Entry: trigger close. Stop (GEOM S): breakdown low - 0.05 x atr_d. Target: session VWAP if it is >= 1R away,
  otherwise 1R. Flat 15:55.
No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import numba
import numpy as np

SIDE = "long"
GEOM = "S"
WINDOW = (1130, 1445)
MIN_ADV = 50e6
CONTEXT = []
LAYERS = ["fromOpen <= -1.5 and sma20 slope < 0 at flag start, flag starts >= 11:00",
          "6-12 bar flag after the last LOD bar, height <= 0.30 ATR",
          "breakdown bar: new LOD, <= 0.15 ATR under the flag low",
          "close above the flag high within 3 bars", "stop breakdown low - 0.05 ATR, target VWAP (>= 1R) else 1R"]

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
def _scan(st, tod, h, l, c, lod, fo, slope, atr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    lastlod = -1            # index of the last bar at the running LOD (same day)
    gs = 0
    bd_ok = np.zeros(n, np.bool_)
    fh = np.full(n, np.nan)  # flag high of a valid breakdown bar
    for i in range(n):
        if st[i]:
            lastlod = -1
            gs = i
        tol = 1e-5 * c[i]
        at_lod = l[i] <= lod[i] + tol
        newlod = at_lod and i > gs and l[i] < lod[i - 1] - tol
        if newlod and lastlod >= gs:
            p = lastlod
            L = i - p - 1
            if 6 <= L <= 12:
                f0 = p + 1
                fhi = -1e18
                flo = 1e18
                for j in range(f0, i):
                    if h[j] > fhi:
                        fhi = h[j]
                    if l[j] < flo:
                        flo = l[j]
                a = atr[i]
                ok = tod[f0] >= 1105 and fo[f0] <= -1.5 and slope[f0] < 0
                ok = ok and (fhi - flo) <= 0.30 * a and l[i] < flo and l[i] >= flo - 0.15 * a
                if ok:
                    bd_ok[i] = True
                    fh[i] = fhi
        if at_lod:
            lastlod = i
        # trigger: first close above the flag high within 3 bars of a valid breakdown
        for d in range(1, 4):
            b = i - d
            if b < gs:
                break
            if not bd_ok[b]:
                continue
            good = c[i] > fh[b]
            for j in range(b + 1, i + 1):
                if l[j] < l[b]:
                    good = False
            for j in range(b + 1, i):
                if c[j] > fh[b]:
                    good = False
            if good:
                m[i] = True
                stop[i] = l[b] - 0.05 * atr[i]
                break
    return m, stop


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    with np.errstate(invalid="ignore", divide="ignore"):
        m, stop = _scan(_start(k), tod.astype(np.int64), b["h"], b["l"], c, b["lod"], _f(df, "fromOpen"),
                        _f(df, "sma20_slope_pct"), atr)
        risk = c - stop
        vw = b["vwap"]
        tgt = np.where((vw - c) >= risk, vw, c + risk)
        m &= risk > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
