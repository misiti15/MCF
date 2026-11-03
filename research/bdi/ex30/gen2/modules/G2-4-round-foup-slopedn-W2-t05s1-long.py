"""G2-4-round-foup-slopedn-W2-t05s1-long - ex30/gen2 grammar-generated setup (BDI 2026-11-03, research/bdi/ex30/gen2).
Rule: LONG at the bar close when close within 0.02 ATR of a round number; up >= 0.5 ATR from today's open; 20-bar SMA falling >= 0.3% over 5 bars; bar close 1130-1400 ET; exit t05s1
Found by the gen2 beam search (regime-maximin fitness on TRAIN only); see research/bdi/ex30/gen2/NOTES.md.
Needs lab context columns (YAML `context: []`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate. Educational only - not financial advice."""
import numpy as np
import gen2_lib as L

SIDE = "long"
GEOM = "t05s1"
WINDOW = (1130, 1400)
CONTEXT = []
RULE = ['round', 'fo_up', 'slope_dn']
LAYERS = ['close within 0.02 ATR of a round number', "up >= 0.5 ATR from today's open", '20-bar SMA falling >= 0.3% over 5 bars', 'bar close 11:30-14:00 ET']


def mask(df) -> np.ndarray:
    return L.mask_rule(df, RULE, WINDOW)
