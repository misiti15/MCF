"""pod-r3-elder-ray-bearpower-hook-long - Elder-Ray buy: EMA13 rising, Bear Power negative but hooking up, with a
30-minute EMA13 slope filter (LONG).

Source: Alexander Elder, Elder-Ray ('Trading for a Living'); MotiveWave Bear Power study description.
URL: https://motivewave.com/studies/elder_ray_bear_power.htm

Variant of pod-shannon-5dma-mtf-pullback-long: the trigger is Elder's bear-power hook (not an MA touch) and the
higher-timeframe filter is a 30-minute EMA13 slope (not the 5-day MA).
Rules (plain English):
  EMA13 on 5m closes, carried across the sessions in the frame (like sma20); Bear Power BP = low - EMA13.
  1. EMA13 now > EMA13 3 bars ago (rising).
  2. 30-minute EMA13 (5m closes sampled at the :00 / :30 bar closes = completed 30m bars, carried across sessions)
     is above its prior 30m value; the latest COMPLETED 30m bar is used at every 5m bar.
  3. BP < 0 on the prior bar AND BP now > BP prior bar AND the prior bar's BP is the lowest of the last 6 bars
     (a hook out of a trough).
  4. close > VWAP (vwapDistPct > 0) and spy_fo > 0.  5. fromOpen > 0.3%.
  Window 10:00-14:30. Entry at that bar's close. Stop (GEOM S): the trough-bar (prior bar) low - 0.05 x atr_d.
  No target; flat 15:55. Scorer control: hold.
Harness notes (pre-declared): the source's 'holdtr' exit (1R trail after +1R) cannot be combined with a structural
stop in this harness, so the structural stop (Elder's stop below the trough) is kept and the trade is held to 15:55.
The 6-bar trough look-back and the 3-bar EMA slope use bars of the same session only (min 3 prior bars available).
The 'next bar exceeds the hook-bar high' entry alternative is not run. No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r28_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["EMA13(5m) rising vs 3 bars ago", "30m EMA13 above its prior 30m value",
          "Bear Power hook: BP[-1] < 0, BP > BP[-1], BP[-1] = min of last 6", "vwapDistPct > 0, spy_fo > 0",
          "fromOpen > 0.3", "10:00-14:30", "stop trough low - 0.05 ATR, hold to 15:55"]
_ST = {}


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[i])


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not U.ctx_ok(df, ["spy_fo"]):
        _ST[id(df)] = np.full(n, np.nan)
        return np.zeros(n, bool)
    c, l, atr = U.f(df, "close"), U.f(df, "low"), U.f(df, "atr_d")
    tod = df["tod"].to_numpy(np.int64)
    sk = U.symkey(df)
    dk = U.daykey(df)
    e13 = U.ema(c, U.start(sk), 13)
    # 30m EMA13 on completed 30m bars (the :00 / :30 5m closes)
    is30 = (tod % 100 == 0) | (tod % 100 == 30)
    idx = np.flatnonzero(is30)
    e30 = np.full(n, np.nan)
    e30p = np.full(n, np.nan)
    if len(idx):
        sk30 = sk[idx]
        v = U.ema(c[idx], U.start(sk30), 13)
        e30[idx] = v
        e30p[idx] = U.lag(v, sk30, 1)
    e30 = pd.Series(e30).groupby(sk).ffill().to_numpy()
    e30p = pd.Series(e30p).groupby(sk).ffill().to_numpy()
    bp = l - e13
    bp1 = U.lag(bp, dk, 1)
    mins = pd.Series(bp1).groupby(dk).transform(lambda s: s.rolling(6, min_periods=3).min()).to_numpy()
    with np.errstate(invalid="ignore"):
        m = e13 > U.lag(e13, dk, 3)
        m &= e30 > e30p
        m &= (bp1 < 0) & (bp > bp1) & (bp1 <= mins + 1e-12)
        m &= (U.f(df, "vwapDistPct") > 0) & (U.f(df, "spy_fo") > 0)
        m &= U.f(df, "fromOpen") > 0.3
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = U.lag(l, dk, 1) - 0.05 * atr
    return np.asarray(m, bool)
