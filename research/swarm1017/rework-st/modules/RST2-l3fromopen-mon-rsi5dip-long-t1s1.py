"""RST2-l3fromopen-mon-rsi5dip-long-t1s1 - swarm1017 rework of L3-gap-slope-fromopen(-FD) (research/swarm1017/rework-st, 2026-10-17).
OPPOSITE SIDE. Monday gap-down (<= -2.66%, weekend gap) that has reversed > 3.46% above its open with a steep slope;
buy the first 5-min RSI(5) dip to <= 30 (continuation of the weekend-gap reversal).
Side long, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Run with min_adv 0, window [950, 1500] (bar close ET), prefilter
'gap_le:-2.6573517322540283' (as the parent).
Open 2-year history (train 2024-10 + 2025-03..12, valid 2026-01..2026-10-07; locked block never loaded; production costs):
n 836 (train 514 / valid 322), exp +0.163R (train +0.121 / valid +0.231), day-clustered t 4.56; regime up +0.187 /
down +0.011; walk-forward share 0.636; 65 Mondays; day-equal-weighted +0.121R (t 1.53; train +0.046, t 0.39).
RSI5 neighbours 20/40 positive in train and valid. The same rule on Tue-Fri is negative (-0.12..+0.11).
WEAK: 2025-04-07 alone holds 254 of 408 morning trades; top-3 days carry 78% of total R. Day-of-week filter with
only a weekend-gap story. Not recommended for live without the lead's locked-block score.
NOT scored on any locked holdout. Below the lineage try-count bar (t 5.03, N_L3 ~ 316k). Research candidate only.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t1s1"
WINDOW = (950, 1500)
LAYERS = ['gap <= -2.657', 'sma20_slope_pct > 0.3724', 'fromOpen > 3.46', 'RSI(5) <= 30', 'Monday', 'bar close 09:50-15:00 ET']


def _dow(df) -> np.ndarray:
    """Day of week (Mon=0) per row: offline frames carry `date`; the live lab frame has a DatetimeIndex."""
    if "date" in df:
        return pd.to_datetime(df["date"]).dt.dayofweek.to_numpy()
    return np.asarray(df.index.dayofweek)


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    tod = c("tod")
    with np.errstate(invalid="ignore"):
        return ((c("gap") <= -2.6573517322540283) & (c("sma20_slope_pct") > 0.37244729995727527)
                & (c("fromOpen") > 3.460294628143309) & (c("rsi5") <= 30) & (_dow(df) == 0)
                & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
