"""regime_2: LONG only. midday+afternoon reversion heat (rev6).
Educational only - not financial advice.
weights (long orientation): {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1, 'trendHeat': -1, 'macdHeat': -1}
regime gates: tod 1105-1500 ET bar close; cost term k=0 (x 100*0.08/atr_d).
long when score >= LONG_AT. See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1, 'trendHeat': -1, 'macdHeat': -1}
LONG_AT = 73.0
SHORT_AT = None


def score(df):
    return regime_score(df, "long", W, 1105, 1500, gate=None, k_cost=0.0, use_heat=False)
