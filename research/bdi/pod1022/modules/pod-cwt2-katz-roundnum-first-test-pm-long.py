"""pod-cwt2-katz-roundnum-first-test-pm-long - Afternoon first test of a big whole-dollar level after a decline (LONG).

Source: Chat With Traders ep 173, Michael Katz; record ep173 'Large round-number bid: lean long on first test'.
URL: https://chatwithtraders.com

VARIANT of obos-levels (holdout_failed: RSI overbought/oversold fades at PDH/PDL/HOD/round numbers, any time) and
pod-wt-flat-top-roundnum-long (a BREAKOUT above a round number). Stated change: no oscillator level; FIRST touch only;
afternoon only; the decline into the level must be decelerating; long side only.

Rules (plain English):
  1. Level L = a whole-number level on the frame's dist_round_atr grid ($5 step at >= $100, $1 at >= $20, else $0.5,
     step chosen from the 12:30 close), below the 12:30 close, the highest grid level at or below this bar's
     low + 0.05 x atr_d. L was not touched earlier today: the low of day before this bar (including 09:30-09:45) is
     more than 0.05 x atr_d above L.
  2. Decline into L: the post-12:00 high (highest high of the bars after 12:00 up to this bar) minus this bar's low is
     >= 0.5 x atr_d.
  3. Fading momentum: momentum now > momentum 3 bars ago, rsiSlope > 0, and volumeRatio <= 1.2.
  4. This bar: low <= L + 0.05 x atr_d, close >= L, lower_wick >= 0.35.
  5. |spy_fo| <= 0.6 (no index trend day).
  Entry: that close, bar close 13:00-15:00. Stop (GEOM S): L - 0.15 x atr_d. Target: the nearer of entry + 1.5R and
  the post-12:00 high; flat 15:55. First signal per symbol-day.
Pre-declared choices: the decline is measured to this bar's low. No tweak used. No tuning on the valid period.
Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1300, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["first touch today of a whole-number level below the 12:30 price",
          "decline >= 0.5 ATR from the post-12:00 high", "momentum rising vs 3 bars ago, rsiSlope > 0, volumeRatio <= 1.2",
          "low within 0.05 ATR of L, close >= L, lower_wick >= 0.35", "|spy_fo| <= 0.6",
          "stop L - 0.15 ATR, target min(1.5R, post-12:00 high)", "13:00-15:00 ET"]

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcummax(x, k):
    s = pd.Series(np.asarray(x, float))
    return s.groupby(k).cummax().to_numpy()


def _at(x, k, tod, T):
    gv = np.full(int(k.max()) + 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, dtype=bool)
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - _f(df, "dist_lod_atr") * atr
        c1230 = _at(c, k, tod, 1230)
        step = np.where(c1230 >= 100, 5.0, np.where(c1230 >= 20, 1.0, 0.5))
        L = np.floor((l + 0.05 * atr) / step) * step
        m = (L < c1230) & (tod > 1230)
        m &= _lag(lod, k) > L + 0.05 * atr                    # first touch today
        hp = _gcummax(np.where(tod >= 1205, h, np.nan), k)     # post-12:00 high up to this bar
        m &= (hp - l) >= 0.5 * atr
        mom = _f(df, "momentum")
        m &= (mom > _lag(mom, k, 3)) & (_f(df, "rsiSlope") > 0) & (_f(df, "volumeRatio") <= 1.2)
        m &= (l <= L + 0.05 * atr) & (c >= L) & (_f(df, "lower_wick") >= 0.35)
        m &= np.abs(_f(df, "spy_fo")) <= 0.6
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = L - 0.15 * atr
        tgt = np.minimum(c + 1.5 * (c - stop), hp)
        m &= np.isfinite(stop) & (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)
