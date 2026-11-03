"""G2-1-macdup-vrlo-vwup-W1-t1s1-short - ex30/gen2 grammar-generated setup (BDI 2026-11-03, research/bdi/ex30/gen2).
Rule: SHORT at the bar close when MACD % crosses above 0; bar volume <= 0.6x its 20-bar mean; >= 0.5 ATR above VWAP; bar close 1000-1130 ET; exit t1s1
Found by the gen2 beam search (regime-maximin fitness on TRAIN only); see research/bdi/ex30/gen2/NOTES.md.
Needs lab context columns (YAML `context: []`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate. Educational only - not financial advice."""
import numpy as np
import gen2_lib as L

SIDE = "short"
GEOM = "t1s1"
WINDOW = (1000, 1130)
CONTEXT = []
RULE = ['macdup', 'vr_lo', 'vw_up']
LAYERS = ['MACD % crosses above 0', 'bar volume <= 0.6x its 20-bar mean', '>= 0.5 ATR above VWAP', 'bar close 10:00-11:30 ET']


def mask(df) -> np.ndarray:
    return L.mask_rule(df, RULE, WINDOW)
