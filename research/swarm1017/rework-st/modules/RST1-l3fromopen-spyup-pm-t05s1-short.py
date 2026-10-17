"""RST1-l3fromopen-spyup-pm-t05s1-short - swarm1017 rework of L3-gap-slope-fromopen(-FD) (research/swarm1017/rework-st, 2026-10-17).
Gap-down (<= -2.66%) name that has bounced > 3.46% off its open with a steep 5-min SMA20 slope, shorted late in the
day only when SPY itself is up > 0.5% from its open (strong-tape day: the bounce is market beta, not news).
Side short, exit t05s1 (R = 0.25 x daily ATR, exit by 15:55). Run with min_adv 0, window [1335, 1500] (bar close ET), prefilter
'gap_le:-2.6573517322540283' (as the parent).
Open 2-year history (train 2024-10 + 2025-03..12, valid 2026-01..2026-10-07; locked block never loaded; production costs):
n 1662 (train 1029 / valid 633), exp +0.176R (train +0.175 / valid +0.178), day-clustered t 4.70; regime up +0.171 /
down +0.322; walk-forward share 0.857; day-equal-weighted +0.104R (t 2.86); top-3 days carry 73% of total R;
10-trades/day cap: train +0.013 / valid +0.093. SPY-threshold neighbours (0.25/0.75/1.0) at 13:35-15:00 all positive
in train and valid; 13:00 start falls to +0.08.
LIVE CODE NEEDED: the live lab frame has no SPY fromOpen ('spy_fo'); without it this mask returns no trades.
Concentration: a few mass gap-down days (2025-04) carry most of the R.
NOT scored on any locked holdout. Below the lineage try-count bar (t 5.03, N_L3 ~ 316k). Research candidate only.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t05s1"
WINDOW = (1335, 1500)
LAYERS = ['gap <= -2.657', 'sma20_slope_pct > 0.3724', 'fromOpen > 3.46', 'SPY fromOpen > +0.5% (same bar) [live code needed]', 'bar close 13:35-15:00 ET']


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    if "spy_fo" not in df:          # live frame lacks SPY context: fail safe (no trades) until the code exists
        return np.zeros(len(df), dtype=bool)
    tod = c("tod")
    with np.errstate(invalid="ignore"):
        return ((c("gap") <= -2.6573517322540283) & (c("sma20_slope_pct") > 0.37244729995727527)
                & (c("fromOpen") > 3.460294628143309) & (c("spy_fo") > 0.5)
                & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
