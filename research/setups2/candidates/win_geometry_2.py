"""win_geometry #2 -- short a bar with positive MACD and a 3-bar buying burst while still far below the prior-day high.

Educational only -- not financial advice.
Train: n=357, 9.4/day, win 49.9%, exp +0.224R, PF 1.74.  Valid: n=76 (below the 100 minimum), win 46.0%,
exp +0.186R, PF 1.56 (baseline short t1s1 +0.020). NOT viable (valid sample too small); kept as a near miss.
Breakeven win rate t1s1 ~52% (target/stop only). Day-clustered: top 5 train days = 85% of total.
"""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "MACD histogram positive (macdPct > 0.399)",
    "Close more than 0.95 daily ATR below the prior-day high",
    "Signed volume of the last 3 bars > +0.376 (short burst of buying)",
]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        m = (
            (df["macdPct"].to_numpy() > 0.399)
            & (df["dist_pdh_atr"].to_numpy() > 0.95)
            & (df["flow3"].to_numpy() > 0.376)
        )
    return np.asarray(m, dtype=bool)
