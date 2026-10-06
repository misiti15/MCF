"""regime_9: SHORT only. fade the bounce: short stretched-up (rev4) names that are below the open, 09:50-10:30.
Educational only - not financial advice.
weights (long orientation): {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
regime gates: tod 950-1030 ET bar close, fo-; cost term k=8 (x 100*0.08/atr_d).
short when score <= SHORT_AT (score is the negated short score). See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
LONG_AT = None
SHORT_AT = -11.3


def score(df):
    return regime_score(df, "short", W, 950, 1030, gate='fo-', k_cost=8.0, use_heat=False)
