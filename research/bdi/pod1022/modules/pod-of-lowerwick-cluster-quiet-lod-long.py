"""pod-of-lowerwick-cluster-quiet-lod-long - Quiet-day defended LOD: three lower-wick tests of the low within 30
minutes, then a 6-bar-high break (LONG).

Source: order-flow and auction podcasts ('repeated tests with rejection tails = responsive buyer'), same family as
the orderflow round that produced pod-of-absorption-bar-level. Practitioner synthesis, not one single episode.
URL: https://traderfeed.blogspot.com/

VARIANT of pod-of-absorption-bar-level-long (a single absorption bar at a level). Stated change: a CLUSTER of >= 3
rejection-wick tests of the same LOD over 6 bars (a defended low, no level table needed), a quiet-market gate, and a
VWAP structural target.
Rules (plain English):
  Universe adv20 >= $50M. Decision bar i, bar close 11:00-14:30.
  1. |spy_fo| <= 0.40% and 0.35 <= breadth <= 0.65.
  2. Stock fromOpen between -2.5% and -0.5%, and vwapDistPct <= -0.3%.
  3. In the previous 6 bars (i-6..i-1), >= 3 bars have lower_wick >= 0.5 and a low within 0.10 x atr_d of the
     running LOD (as of that bar). No bar of the 6 has a low more than 0.10 x atr_d below the LOD as it stood just
     before the 6 bars.
  4. Mean volumeRatio of those test bars >= 1.0.
  5. Trigger: close above the max high of the previous 6 bars.
  Entry: close. Stop (GEOM S): LOD - 0.05 x atr_d. Target: session VWAP at entry if >= 1R away, otherwise 1R.
  Flat 15:55.
No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
MIN_ADV = 50e6
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["|spy_fo| <= 0.4, breadth 0.35-0.65", "fromOpen -2.5..-0.5, vwapDist <= -0.3",
          ">= 3 lower-wick (>= 0.5) tests within 0.10 ATR of LOD in 6 bars, no undercut > 0.10 ATR",
          "mean volumeRatio of tests >= 1.0", "close above the 6-bar high",
          "stop LOD - 0.05 ATR, target VWAP (>= 1R) else 1R"]

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df or "breadth" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr, lod = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"], b["lod"]
    lw, vr = _f(df, "lower_wick"), _f(df, "volumeRatio")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.abs(_f(df, "spy_fo")) <= 0.40
        br = _f(df, "breadth")
        m &= (br >= 0.35) & (br <= 0.65)                                              # (1)
        fo = _f(df, "fromOpen")
        m &= (fo >= -2.5) & (fo <= -0.5) & (_f(df, "vwapDistPct") <= -0.3)            # (2)
        test = ((lw >= 0.5) & (l <= lod + 0.10 * atr)).astype(float)
        lod0 = _lag(lod, k, 7)                                                         # LOD just before the 6 bars
        cnt = np.zeros(len(c))
        vsum = np.zeros(len(c))
        hmax = np.full(len(c), -np.inf)
        under = np.zeros(len(c), bool)
        for j in range(1, 7):
            tj = _lag(test, k, j)
            tj1 = np.nan_to_num(tj)
            cnt += tj1
            vsum += np.where(tj1 == 1, _lag(vr, k, j), 0.0)
            hmax = np.fmax(hmax, _lag(h, k, j))
            under |= _lag(l, k, j) < lod0 - 0.10 * atr
        m &= np.isfinite(lod0) & (cnt >= 3) & ~under                                   # (3)
        m &= (vsum / np.where(cnt > 0, cnt, np.nan)) >= 1.0                            # (4)
        m &= c > hmax                                                                  # (5)
        stop = lod - 0.05 * atr
        risk = c - stop
        vw = b["vwap"]
        tgt = np.where((vw - c) >= risk, vw, c + risk)
        m &= risk > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
