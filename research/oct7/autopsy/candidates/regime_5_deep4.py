"""regime_5_deep4: heat_fade_long (regime_5) taken ONLY when the stock is >= 4% below today's open at the signal bar.
Autopsy 2026-10-08 finalist (research/oct7/autopsy/NOTES.md). NOT LIVE - the lead scores it once on the locked holdouts.
Semantics = a filter on the setup's FIRST signal of the day (exactly what was tested): if the first bar where the
regime_5 score >= LONG_AT has fromOpen > -4%, the day is skipped (no later bar is searched).
Educational only - not financial advice.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "heat", "candidates"))
from _regime_common import regime_score

W = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1, 'fo': -1}
LONG_AT = 57.5
SHORT_AT = None
MAX_FROM_OPEN = -4.0


def score(df):
    s = regime_score(df, "long", W, 1105, 1330, gate='gap+', k_cost=4.0, use_heat=False)
    tod = df["tod"].to_numpy()
    hit = np.flatnonzero((s >= LONG_AT) & (tod >= 950) & (tod <= 1500))
    if len(hit) and not float(df["fromOpen"].to_numpy()[hit[0]]) <= MAX_FROM_OPEN:
        return np.full(len(s), np.nan)
    return s
