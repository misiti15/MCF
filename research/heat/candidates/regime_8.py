"""regime_8: LONG only. random-search winner, morning.
Educational only - not financial advice.
weights (long orientation): {'volumeHeat': 1, 'momentumHeat': 1, 'priceActionHeat': -1, 'trendHeat': -1, 'macdHeat': -0.5, 'vwapHeat': -0.5, 'fo': 0.5, 'gap': -0.5}
regime gates: tod 950-1100 ET bar close; cost term k=0 (x 100*0.08/atr_d).
long when score >= LONG_AT. See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {'volumeHeat': 1, 'momentumHeat': 1, 'priceActionHeat': -1, 'trendHeat': -1, 'macdHeat': -0.5, 'vwapHeat': -0.5, 'fo': 0.5, 'gap': -0.5}
LONG_AT = 46.7
SHORT_AT = None


def score(df):
    return regime_score(df, "long", W, 950, 1100, gate=None, k_cost=0.0, use_heat=False)
