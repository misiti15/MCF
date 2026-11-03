"""G2-3-uwick-brhi-d20hi-W2-t1s1-long - ex30/gen2 grammar-generated setup (BDI 2026-11-03, research/bdi/ex30/gen2).
Rule: LONG at the bar close when upper wick >= 60% of a bar >= 0.10 ATR; breadth (share above VWAP) >= 70%; >= 0.8% above the 20-bar SMA; bar close 1130-1400 ET; exit t1s1
Found by the gen2 beam search (regime-maximin fitness on TRAIN only); see research/bdi/ex30/gen2/NOTES.md.
Needs lab context columns (YAML `context: ['breadth']`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate. Educational only - not financial advice."""
import numpy as np
import gen2_lib as L

SIDE = "long"
GEOM = "t1s1"
WINDOW = (1130, 1400)
CONTEXT = ['breadth']
RULE = ['uwick', 'br_hi', 'd20_hi']
LAYERS = ['upper wick >= 60% of a bar >= 0.10 ATR', 'breadth (share above VWAP) >= 70%', '>= 0.8% above the 20-bar SMA', 'bar close 11:30-14:00 ET']


def mask(df) -> np.ndarray:
    return L.mask_rule(df, RULE, WINDOW)
