"""win_geometry #1 -- afternoon fade of a gap-down stock that has rallied well above its 5-min SMA50.

Educational only -- not financial advice.
Train (40 sessions): n=875, 22.4/day, win 41.7%, exp +0.259R, PF 2.13 (lab halves +0.330 / +0.171).
Valid (15 sessions): n=166, 11.9/day, win 36.1%, exp +0.096R, PF 1.30 (baseline short t1s1 +0.020).
Breakeven: t1s1 needs ~52% wins if every trade hit target/stop; here most trades end on the 15:55 timed
exit, so the low win rate still nets positive R. Caveat: P&L is day-clustered (top 5 train days = 91% of
total; valid top 5 days > total). Passes the VIABLE bar on paper but it is mostly a regime bet on
afternoon selloffs.
"""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "Gapped down at the open (gap < -0.445%)",
    "Now stretched above the 5-min SMA50 (sma50_dist_pct > +2.19%)",
    "Bar close at or after 13:00 ET",
]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        m = (
            (df["gap"].to_numpy() < -0.445)
            & (df["sma50_dist_pct"].to_numpy() > 2.19)
            & (df["tod"].to_numpy() > 1299)
        )
    return np.asarray(m, dtype=bool)
