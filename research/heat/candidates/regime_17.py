"""regime_17: SHORT only. random-search winner, gap-up names, morning.
Educational only - not financial advice.
weights (long orientation): {'volumeHeat': -0.5, 'rsiHeat': 0.5, 'momentumHeat': 0.5, 'vwapHeat': -1, 'fo': 1, 'gap': -1}
regime gates: tod 950-1100 ET bar close, gap+; cost term k=4 (x 100*0.08/atr_d).
short when score <= SHORT_AT (score is the negated short score). See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {'volumeHeat': -0.5, 'rsiHeat': 0.5, 'momentumHeat': 0.5, 'vwapHeat': -1, 'fo': 1, 'gap': -1}
LONG_AT = None
SHORT_AT = -17.7


def score(df):
    return regime_score(df, "short", W, 950, 1100, gate='gap+', k_cost=4.0, use_heat=False)
