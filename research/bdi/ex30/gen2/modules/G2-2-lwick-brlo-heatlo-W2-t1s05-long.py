"""G2-2-lwick-brlo-heatlo-W2-t1s05-long - ex30/gen2 grammar-generated setup (BDI 2026-11-03, research/bdi/ex30/gen2).
Rule: LONG at the bar close when lower wick >= 60% of a bar >= 0.10 ATR; breadth <= 30%; heat <= -25; bar close 1130-1400 ET; exit t1s05
Found by the gen2 beam search (regime-maximin fitness on TRAIN only); see research/bdi/ex30/gen2/NOTES.md.
Needs lab context columns (YAML `context: ['breadth']`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate. Educational only - not financial advice."""
import numpy as np
import gen2_lib as L

SIDE = "long"
GEOM = "t1s05"
WINDOW = (1130, 1400)
CONTEXT = ['breadth']
RULE = ['lwick', 'br_lo', 'heat_lo']
LAYERS = ['lower wick >= 60% of a bar >= 0.10 ATR', 'breadth <= 30%', 'heat <= -25', 'bar close 11:30-14:00 ET']


def mask(df) -> np.ndarray:
    return L.mask_rule(df, RULE, WINDOW)
