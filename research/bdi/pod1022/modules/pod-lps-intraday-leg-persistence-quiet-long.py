"""pod-lps-intraday-leg-persistence-quiet-long - Tug-of-war intraday clientele: past intraday winners keep winning
intraday (same-day leg).

Source: Lou, Polk & Skouras, 'A Tug of War: Overnight versus Intraday Expected Returns' (JFE 2019) - firm-level
intraday return continuation; discussed in the Top Traders Unplugged / Systematic Investor overnight-vs-intraday thread.
URL: https://personal.lse.ac.uk/polk/research/TugOfWar.pdf

VARIANT of backlog 'Overnight-minus-intraday return persistence, weekly top decile, 5-20d hold'. Stated change: only
the intraday leg is traded (enter after the open, flat at 15:55, no overnight exposure) and the signal is the stock's
own 20-day sum of open-to-close returns, not overnight-minus-intraday.

Rules (long, universe adv20 >= $50M):
  1) Rank: sum over the prior 20 completed sessions (D-20..D-1) of (close / open - 1); the stock is in the top decile
     of the adv20 >= $50M universe that day (rank computed per date from D-1 values only). Proxy: the daily table's
     16:00 close stands in for the 15:55 close.
  2) Bar closing 10:00-10:45: 0 <= fromOpen <= +0.6% and 0 <= vwapDistPct <= +0.4 (on plan, not extended).
  3) -0.2 <= spy_fo <= +0.6 (spy_fo >= -0.2 and |spy_fo| <= 0.6: quiet / balanced tape).
  4) sma20_slope_pct >= 0.
Entry: first qualifying bar's close. Exit: GEOM holdtr (stop 1R = 0.25 x atr_d, 1R trail once +1R), flat 15:55.
Costs per config/default.yaml (scorer). One trade per symbol-day. No tweak made.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r35_util as U  # noqa: E402

SIDE = "long"
GEOM = "holdtr"
WINDOW = (1000, 1045)
MIN_ADV = 50e6
CONTEXT = ["spy_fo"]


def mask(df) -> np.ndarray:
    if "spy_fo" not in df or len(df) == 0:
        return np.zeros(len(df), dtype=bool)
    k = U.key(df)
    d = U.map_daily(df, k, ["oc20_pct"])
    fo, vd, sp = U.f(df, "fromOpen"), U.f(df, "vwapDistPct"), U.f(df, "spy_fo")
    tod = df["tod"].to_numpy(np.int64)
    with np.errstate(invalid="ignore"):
        m = d["oc20_pct"] > 0.9
        m &= (fo >= 0) & (fo <= 0.6) & (vd >= 0) & (vd <= 0.4)
        m &= (sp >= -0.2) & (sp <= 0.6)
        m &= U.f(df, "sma20_slope_pct") >= 0
        m &= U.f(df, "adv20") >= MIN_ADV
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
