"""pod-cwt4-gogolak-1000bar-sma-dip-vixrise-etf-long - Index ETF dip far below the 1000-bar (5-min) moving average
after a VIX jump, closed out the same day (LONG).

Source: Chat With Traders ep 276, William Gogolak ('Buy the dip: price 2-3% below the 1000-bar moving average');
repo extract research/bdi/cwt/extract (CATALOG family CWT21). CWT test C1 only tried the daily RSI(2)/RSI(3)
limit-entry version; this intraday-distance plus VIX-rise trigger is new.
URL: https://chatwithtraders.com/276

Rules (plain English). SYMBOLS: SPY, QQQ, IWM, DIA and the 11 SPDR sector ETFs (XLB/XLRE/XLC are not in the
5-min history, so 12 ETFs trade).
  1. SMA1000 = mean of the last 1000 continuous 5-min closes (09:35-15:55 bars, about 13 sessions; the previous open
     month is the warm-up, the series restarts after a > 7-day gap). dist = close / SMA1000 - 1 <= -2.0% on the
     decision bar (fixed -2.0%, the middle of the source's 2-3% range; no grid search, no ATR scaling).
  2. VIX close on D-1 vs its close 5 sessions earlier (D-6) >= +20% (prior-day data only).
  3. SPY daily close on D-1 > its SMA200 (last 200 open sessions).
  4. The decision 5-min bar closes up (close > its open; raw 5-min open from frames_tf, else close > prior close).
  Entry: the decision bar's close (the scorer's entry; the source's next-bar open), bar close 10:00-14:30 ET, one
  entry per symbol per day. Stop (GEOM S): entry - 1.0 x daily ATR(14). Target: entry + half the gap back to the
  SMA1000, or the session VWAP if VWAP is above the entry and nearer. Flat 15:55. No scaling-in.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Expect very few trades, clustered in selloffs. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt4_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
DIST = -0.020
VIX_UP = 0.20
LAYERS = ["close <= SMA1000(5m) x 0.98", "VIX D-1 vs D-6 >= +20%", "SPY D-1 close > SMA200", "bar closes up",
          "stop entry - 1 ATR, target half-way to SMA1000 or VWAP if nearer"]
_ST = {}


def _sma1000(df):
    fb = U.full_bars(df, symbols=SYMBOLS)
    if fb is None or not len(fb):
        return None
    fb = fb.copy()
    dt = pd.to_datetime(fb["date"])
    g = ((fb["symbol"] != fb["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    fb["sma1000"] = fb["c"].groupby(g).transform(lambda x: x.rolling(1000, min_periods=1000).mean())
    fb["pc5"] = fb["c"].groupby(g).shift(1)
    return fb


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    if n == 0:
        return z
    fb = _sma1000(df)
    if fb is None:
        return z
    k = U.key(df)
    b = U.base(df)
    s = U.map_rows(df, fb, ["sma1000", "pc5"])
    sma = s["sma1000"]
    t5 = U.tf5(df, SYMBOLS)
    opn5 = U.map_rows(df, t5, ["open"])["open"] if t5 is not None else np.full(n, np.nan)
    ds = U.dstr(df)
    vix = U.vix_rise()
    spy = U.spy_sma200_ok()
    vr = np.array([vix.get(x, np.nan) for x in ds], float)
    sp = np.array([spy.get(x, np.nan) for x in ds], float)
    c = b["c"]
    with np.errstate(invalid="ignore", divide="ignore"):
        dist = c / sma - 1
        up = np.where(np.isfinite(opn5), c > opn5, c > s["pc5"])
        m = (dist <= DIST) & (vr >= VIX_UP) & (sp == 1.0) & up
        stop = c - b["atr"]
        t1 = c + 0.5 * (sma - c)
        vw = b["vwap"]
        tgt = np.where((vw > c) & (vw < t1), vw, t1)
    m &= np.isfinite(stop) & np.isfinite(tgt) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def stop_price(f, i):
    return U.stash_get(_ST, f, mask, i, 0)


def target_price(f, i, stop):
    return U.stash_get(_ST, f, mask, i, 1)
