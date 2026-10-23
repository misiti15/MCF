"""pod-r3-davey-trend-aligned-3down-pullback-holdtr-long - Davey 'Euro Day' style: trend-aligned stock, enter after 3
consecutive lower 5m closes, let winners run (LONG).

Source: Kevin Davey, Building Winning Algorithmic Trading Systems (Euro Day system: trend aligned, mean-reversion
entries, larger winners), via the Financial Wisdom TV summary.
URL: https://www.financialwisdomtv.com/post/building-winning-algorithmic-trading-systems-kevin-davey-s-complete-framework-for-trading-success

VARIANT of bdi-tg-p-pullback-vwap-long (first pullback holding VWAP / EMA9, failed). Stated changes: a count-based
trigger (the 3rd consecutive lower 5m close), any pullback (not only the first), a multi-day trend filter and a
'larger winners' exit (holdtr) instead of t1s1.
Rules (plain English, LONG), bar close 10:00-14:00:
  1. Multi-day trend: sma50_dist_pct > 0.3 and sma20_slope_pct > 0 (5m SMAs that span prior days), and the stock is
     above the prior close ((1 + gap) x (1 + fromOpen) > 1).
  2. Mean-reversion entry: this bar is exactly the 3rd consecutive bar with close < the prior close (the bar 3 back
     did not itself close lower), and the 3-bar drop (close 3 bars ago - close) >= 0.15 x atr_d.
  3. Close still > VWAP - 0.1% (vwapDistPct > -0.1).
  4. spy_fo > 0.
  Entry at the 3rd down bar's close. Exit GEOM holdtr: R = 0.25 x atr_d, stop 1R, 1R trail once +1R, flat 15:55.
Pre-declared choice: the source idea offers a structural stop (3-bar low - 0.1 ATR) OR R = 0.25 ATR with holdtr; the
holdtr form is the one scored (the 'let winners run' exit the harness supports). No tweak made. Only bars up to the
decision bar are used (look-backs keyed by symbol-day). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "holdtr"
WINDOW = (1000, 1400)
CONTEXT = ["spy_fo"]
LAYERS = ["sma50_dist_pct > 0.3, sma20_slope_pct > 0, above prior close", "3rd consecutive lower close",
          "3-bar drop >= 0.15 ATR", "vwapDistPct > -0.1", "spy_fo > 0", "holdtr"]

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r29_util as U  # noqa: E402


def mask(df) -> np.ndarray:
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool)
    k = U.key(df)
    c = U.f(df, "close")
    atr = U.f(df, "atr_d")
    tod = df["tod"].to_numpy(np.int64)
    c1, c2, c3, c4 = (U.lag(c, k, j) for j in (1, 2, 3, 4))
    with np.errstate(invalid="ignore"):
        m = (U.f(df, "sma50_dist_pct") > 0.3) & (U.f(df, "sma20_slope_pct") > 0)
        m &= (1 + U.f(df, "gap") / 100) * (1 + U.f(df, "fromOpen") / 100) > 1
        m &= (c < c1) & (c1 < c2) & (c2 < c3) & ~(c3 < c4)
        m &= (c3 - c) >= 0.15 * atr
        m &= U.f(df, "vwapDistPct") > -0.1
        m &= U.f(df, "spy_fo") > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
