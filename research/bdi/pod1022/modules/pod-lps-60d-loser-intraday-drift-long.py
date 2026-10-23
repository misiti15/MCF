"""pod-lps-60d-loser-intraday-drift-long - Momentum losers earn their return intraday: a 60-day loser that gaps down
or flat and then holds above VWAP with buying pressure in the 10:00-11:00 hour, held to the close (LONG).

Source: Lou, Polk & Skouras (JFE 2019), 'A tug of war: overnight versus intraday expected returns' - momentum profits
accrue overnight and REVERSE intraday, so past losers rise during the session; Xu (2017) 'Reversal, Momentum and
Intraday Returns', summarized by CXO Advisory.
URL: https://www.cxoadvisory.com/momentum-investing/when-to-look-for-momentum-and-reversal-intraday/

NEW: a cross-sectional momentum rank used only for the intraday leg (the backlog momentum items are multi-week holds).

Rules (plain English). Universe: adv20 >= $100M and price >= $10 (both as of D-1).
  1. The 60-session close-to-close return (close D-1 / close D-61 - 1, completed days only) is in the bottom decile of
     that universe on the day (percentile rank per date from D-1 values only).
  2. Today's gap <= 0 (the overnight leg kept falling - the tug of war).
  3. A bar closing 10:00-11:00 with close > session VWAP and buyPressure > 0.
  4. spy_fo >= 0 or breadth >= 0.5.
  Entry: the first qualifying bar's close. Stop (GEOM S): low of day so far - 0.05 x daily ATR; no target, hold to
  15:55. A companion module (-holdtr) scores the same entries with GEOM holdtr.
No tweak made. 1 configuration (+ the holdtr exit companion). Costs per config/default.yaml (scorer).
Only bars up to the decision bar are used; daily values come from completed days.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r36_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1100)
MIN_ADV = 100e6
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["60d return bottom decile (adv20 >= 100M, price >= 10, D-1)", "gap <= 0",
          "10:00-11:00 close > VWAP and buyPressure > 0", "spy_fo >= 0 or breadth >= 0.5",
          "stop LOD - 0.05 ATR, hold to 15:55"]


def mask(df) -> np.ndarray:
    if "breadth" not in df or "spy_fo" not in df or len(df) == 0:
        return np.zeros(len(df), dtype=bool)
    d = U.map_day(df, U.ret60_tab(), ["r60_pct", "adv_1", "c_1"])
    tod = df["tod"].to_numpy(np.int64)
    with np.errstate(invalid="ignore"):
        m = (d["r60_pct"] <= 0.10) & (d["adv_1"] >= 100e6) & (d["c_1"] >= 10)
        m &= U.f(df, "gap") <= 0
        m &= (U.f(df, "vwapDistPct") > 0) & (U.f(df, "buyPressure") > 0)
        m &= (U.f(df, "spy_fo") >= 0) | (U.f(df, "breadth") >= 0.5)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    c = float(f["close"].iat[i])
    atr = float(f["atr_d"].iat[i])
    return c - float(f["dist_lod_atr"].iat[i]) * atr - 0.05 * atr
