"""heat_fade_long-FD - FULL-DAY version of heat_fade_long (owner decision 2026-10-09; Testing account).
Source formula: research/heat/candidates/regime_5.py (copied; weights, threshold, gate, cost term unchanged).
Removed: the time-of-day gate of regime_score (1105, 1330) -> (950, 1500); the heat score itself carries the
window, so widening the YAML window alone would not widen the setup.
Run with type heat, sides long, gate gap+, min_adv 125000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json.
Source docstring (provenance only):
    regime_5: LONG only. midday reversion heat with fromOpen fade (revfo), gap-up names.
    Educational only - not financial advice.
    weights (long orientation): {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1, 'fo': -1}
    regime gates: tod 1105-1330 ET bar close, gap+; cost term k=4 (x 100*0.08/atr_d).
    long when score >= LONG_AT. See _regime_common.py.
Educational only - not financial advice."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'heat', 'candidates'))  # research/heat/candidates/_regime_common.py
from _regime_common import regime_score

W = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1, 'fo': -1}
LONG_AT = 57.5
SHORT_AT = None


def score(df):
    return regime_score(df, "long", W, 950, 1500, gate='gap+', k_cost=4.0, use_heat=False)
