"""pod-bst130-alvarez-regime-classified-etf-dip-long - ETF intraday dip only in a 'non-trending, low-vol' daily
market class.

Source: Better System Trader ep 133 (Cesar Alvarez, part 2: classify market conditions trending vs non-trending and by
volatility, then switch parameters).
URL: https://podwise.ai/podcasts/2840?page=10

VARIANT of pod-chop-etf-oversold-vwap-magnet-long. Stated change: the intraday chop gate (|spy_fo|, breadth band) is
replaced by a DAILY regime class known before the open, and the oversold trigger is deeper.

Rules (long, SYMBOLS = the 15-ETF list):
  1) Daily class from prior sessions (SPY daily closes ending D-1): 10-day efficiency ratio |C0 - C10| / sum|dC| <=
     0.30 (non-trending) AND 10-day realized vol (std of daily log returns) below the median of its prior 120
     available values (min 60; low vol).
  2) Bar closing 10:30-14:30: vwapDistPct <= -0.5 and dist_lod_atr <= 0.1 (at the day's low).
  3) lower_wick >= 0.4 on the bar (rejection) and rsi5 <= 20.
  4) SPY not at its own LOD: spy_fo > -0.6.
Entry: bar close. Stop: bar low - 0.05 x atr_d (GEOM S). Target: session VWAP (limit), else 15:55.
Costs per config/default.yaml. No tweak made.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r35_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = list(U.ETF15)
CONTEXT = ["spy_fo"]


def mask(df) -> np.ndarray:
    if "spy_fo" not in df or len(df) == 0:
        return np.zeros(len(df), dtype=bool)
    s = U.map_spy(df, ["er10", "rv10", "rv_med"])
    tod = df["tod"].to_numpy(np.int64)
    with np.errstate(invalid="ignore"):
        m = np.isin(df["symbol"].astype(str).to_numpy(), SYMBOLS)
        m &= (s["er10"] <= 0.30) & (s["rv10"] < s["rv_med"])
        m &= (U.f(df, "vwapDistPct") <= -0.5) & (U.f(df, "dist_lod_atr") <= 0.1)
        m &= (U.f(df, "lower_wick") >= 0.4) & (U.f(df, "rsi5") <= 20)
        m &= U.f(df, "spy_fo") > -0.6
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    return float(f["low"].iat[i]) - 0.05 * float(f["atr_d"].iat[i])


def target_price(f, i, stop):
    return float(f["close"].iat[i]) / (1 + float(f["vwapDistPct"].iat[i]) / 100)
