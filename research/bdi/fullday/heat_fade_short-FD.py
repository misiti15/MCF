"""heat_fade_short-FD - FULL-DAY version of heat_fade_short (owner decision 2026-10-09; Testing account).
Source formula: research/heat/candidates/regime_9.py (copied; weights, threshold, gate, cost term unchanged).
Removed: the time-of-day gate of regime_score (950, 1030) -> (950, 1500); the heat score itself carries the
window, so widening the YAML window alone would not widen the setup.
Run with type heat, sides short, gate fo-, min_adv 125000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json.
Source docstring (provenance only):
    regime_9: SHORT only. fade the bounce: short stretched-up (rev4) names that are below the open, 09:50-10:30.
    Educational only - not financial advice.
    weights (long orientation): {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
    regime gates: tod 950-1030 ET bar close, fo-; cost term k=8 (x 100*0.08/atr_d).
    short when score <= SHORT_AT (score is the negated short score). See _regime_common.py.
Educational only - not financial advice."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'heat', 'candidates'))  # research/heat/candidates/_regime_common.py
from _regime_common import regime_score

W = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
LONG_AT = None
SHORT_AT = -11.3


def score(df):
    return regime_score(df, "short", W, 950, 1500, gate='fo-', k_cost=8.0, use_heat=False)
