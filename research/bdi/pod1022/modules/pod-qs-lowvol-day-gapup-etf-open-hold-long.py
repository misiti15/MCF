"""pod-qs-lowvol-day-gapup-etf-open-hold-long - Gap-up after a low-volume day, index ETF held to the close (LONG).

Source: Quantified Strategies, 'SPY volume strategy' (key takeaways: the only volume pattern with positive expectancy
was a large gap-up after a low-volume day, bought at the open and sold at the close).
URL: https://www.quantifiedstrategies.com/?p=1817

VARIANT of pod-edgeful-green-first15-open-hold-long. Stated change: no pullback-to-open trigger; the gate is the QS
volume-gap combination (low prior-session volume + a large gap up); ETFs only, held from 09:50 to the close.

Rules (plain English). SYMBOLS SPY, QQQ, IWM, DIA.
  1. Prior-day dollar volume (lib.daily, D-1) <= 0.80 x the mean of the 20 sessions before it (D-21..D-2 - stated
     reading so D-1 is not in its own baseline). Fallback when daily volume is missing: prior-day range <= 0.70 x
     atr_d.
  2. gap >= +0.50% and gap_atr = (open - prior close) / atr_d >= 0.30.
  3. On the entry bar: fromOpen >= 0 (the gap is not being sold) and close > session VWAP.
  4. spy_fo >= 0 on the same bar.
  Entry: close of the first qualifying bar closing 09:50-10:00 (the rules are written for the 09:50 bar; the 09:30
  open cannot be scored because frames start at 09:50), one per symbol-day. Stop (GEOM S): low of day so far - 0.05 x
  atr_d, floored at 0.25 x atr_d of risk. No target: flat 15:55 (QS rule is open-to-close).
Pre-declared companions (from the idea, not tuned): -g030 / -g075 (gap threshold +0.30% / +0.75%) and -ctrl-normvol
(prior-day volume > 0.80 x the average, i.e. normal-volume days). 4 configurations.
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r37_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1000)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = ["spy_fo"]
GAPMIN = 0.50
LOWVOL = True        # False = control on normal-volume prior days
LAYERS = ["SPY/QQQ/IWM/DIA", "prior-day $vol <= 0.8 x 20d avg (fallback range <= 0.7 ATR)",
          "gap >= 0.50% and >= 0.30 ATR", "fromOpen >= 0, close > VWAP, spy_fo >= 0 at 09:50-10:00",
          "stop LOD - 0.05 ATR (risk >= 0.25 ATR), flat 15:55"]
_ST = {}


def compute(df):
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan)
    b = U.base(df)
    d = U.map_daily(df, ["dvr1", "rng1"])
    c, a = b["c"], b["atr"]
    with np.errstate(invalid="ignore", divide="ignore"):
        dvr = d["dvr1"]
        low = np.where(np.isfinite(dvr), dvr <= 0.80, d["rng1"] <= 0.70 * a)
        known = np.isfinite(dvr) | np.isfinite(d["rng1"])
        m = known & (low if LOWVOL else ~low)
        gap = U.f(df, "gap")
        m &= (gap >= GAPMIN) & ((b["opn"] - b["pc"]) / a >= 0.30)
        m &= (U.f(df, "fromOpen") >= 0) & (c > b["vwap"]) & (U.f(df, "spy_fo") >= 0)
        m &= (b["tod"] >= WINDOW[0]) & (b["tod"] <= WINDOW[1])
        stop = np.fmin(b["lod"] - 0.05 * a, c - 0.25 * a)
        m &= (a > 0) & (stop < c)
    return np.asarray(m, bool), stop


def mask(df):
    m, s = compute(df)
    _ST.clear()
    _ST[id(df)] = s
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
