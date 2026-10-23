"""pod-tl-rvol-at-time-flat-stock-quiet-tape-ignition-long - Time-of-day relative-volume ignition in a flat stock on
a quiet tape (midday LONG).

Source: TraderLion 'Enhanced Volume' (TradingView: flags high relative-volume bars and alerts past a threshold);
'Relative Volume At Time' (RVOL vs the same time window on prior sessions, >= 1.5x pre-entry check).
URL: https://www.tradingview.com/script/yzjhAo0E-TraderLion-s-Enhanced-Volume

VARIANT of pod-chop-pop-volume-breakout-long. Stated change: the stock must be FLAT on the day (not a strong mover
near HOD), the volume test is normalized by time of day rather than by the day's average, and SPY must be quiet.
Rules (plain English; RVOL-at-time = 5m bar volume / mean volume of the same 5m slot over the 20 prior sessions):
  1. Quiet tape: SPY |fromOpen| <= 0.35% and SPY's range since 09:30 <= 0.5 x SPY atr_d at the bar.
  2. Stock |fromOpen| <= 0.8% and its day range so far <= 0.7 x atr_d.
  3. Ignition bar: RVOL-at-time >= 3.0, close in the top 25% of the bar, close > the highest high of the prior 12
     bars (60 minutes), close > session VWAP.
  4. The stock's RVOL-at-time over the previous 6 bars averages <= 1.2 (dormant).
  5. D-1 close > daily SMA20 (completed days).
  Entry: the ignition bar close, 11:00-14:30 ET, first signal only. Stop (GEOM S): ignition bar low - 0.05 x atr_d;
  skip when risk > 0.4 x atr_d. Target 2R, else flat 15:55.
Harness notes (pre-declared): bar volumes from the _r24_bars cache (1-minute vendor bars, locked block dropped; the
20-session baseline needs >= 10 prior sessions and restarts after the locked gap). 'First signal only' = the first
bar per symbol-day that meets rules 1-5 in the window; if its risk is > 0.4 x atr_d the day is skipped (no later
re-entry). No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r27_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["SPY |fromOpen| <= 0.35% and range <= 0.5 SPY ATR", "stock |fromOpen| <= 0.8%, day range <= 0.7 ATR",
          "RVOL-at-time >= 3, close top 25% of bar, > 60-min high, > VWAP", "prior 6 bars RVOL-at-time mean <= 1.2",
          "D-1 close > SMA20", "11:00-14:30 first signal", "stop bar low - 0.05 ATR (risk <= 0.4 ATR), target 2R"]
_ST = {}


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


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool)
    k = U.key(df)
    b = U.base(df)
    B = U.vol_bars(df)
    if B is None:
        return np.zeros(n, bool)
    rvt = U.map_bars(df, B, ["rvt"])["rvt"]
    D = U.map_daily(df, k, ["c1", "sma201"])
    S = U.map_spy(df, ["rng", "spy_atr"])
    c, h, l, atr, tod = b["c"], b["h"], b["l"], b["atr"], b["tod"]
    with np.errstate(invalid="ignore", divide="ignore"):
        hh = np.full(n, -np.inf)
        rs = np.zeros(n)
        cnt = np.zeros(n)
        for j in range(1, 13):
            hh = np.fmax(hh, U.lag(h, k, j))
        for j in range(1, 7):
            x = U.lag(rvt, k, j)
            rs += np.nan_to_num(x)
            cnt += np.isfinite(x)
        m = (np.abs(U.f(df, "spy_fo")) <= 0.35) & (S["rng"] <= 0.5 * S["spy_atr"])
        m &= (np.abs(U.f(df, "fromOpen")) <= 0.8) & ((b["hod"] - b["lod"]) <= 0.7 * atr)
        m &= (rvt >= 3.0) & (h > l) & ((c - l) / (h - l) >= 0.75) & np.isfinite(U.lag(h, k, 12)) & (c > hh)
        m &= c > b["vwap"]
        m &= (cnt == 6) & (rs / 6 <= 1.2)
        m &= D["c1"] > D["sma201"]
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        # first signal only per symbol-day
        first = m & (pd.Series(m.astype(int)).groupby(k).cumsum().to_numpy() == 1)
        stop = l - 0.05 * atr
        risk = c - stop
        tgt = c + 2 * risk
        m = first & (risk > 0) & (risk <= 0.4 * atr)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), bool)
