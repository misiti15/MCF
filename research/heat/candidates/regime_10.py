"""regime_10: SHORT only. rev6 short, below the open, 09:50-11:00.
Educational only - not financial advice.
weights (long orientation): {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1, 'trendHeat': -1, 'macdHeat': -1}
regime gates: tod 950-1100 ET bar close, fo-; cost term k=8 (x 100*0.08/atr_d).
short when score <= SHORT_AT (score is the negated short score). See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1, 'trendHeat': -1, 'macdHeat': -1}
LONG_AT = None
SHORT_AT = -21.7


def score(df):
    return regime_score(df, "short", W, 950, 1100, gate='fo-', k_cost=8.0, use_heat=False)
