"""regime_7: LONG only. random-search winner, 11:05-15:00.
Educational only - not financial advice.
weights (long orientation): {'momentumHeat': -1, 'priceActionHeat': 0.5, 'trendHeat': -0.5, 'vwapHeat': -0.5}
regime gates: tod 1105-1500 ET bar close; cost term k=1 (x 100*0.08/atr_d).
long when score >= LONG_AT. See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {'momentumHeat': -1, 'priceActionHeat': 0.5, 'trendHeat': -0.5, 'vwapHeat': -0.5}
LONG_AT = 26.7
SHORT_AT = None


def score(df):
    return regime_score(df, "long", W, 1105, 1500, gate=None, k_cost=1.0, use_heat=False)
