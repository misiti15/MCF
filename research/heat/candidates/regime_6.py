"""regime_6: LONG only. midday reversion heat (rev4), below the open, cost-aware.
Educational only - not financial advice.
weights (long orientation): {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
regime gates: tod 1105-1330 ET bar close, fo-; cost term k=2 (x 100*0.08/atr_d).
long when score >= LONG_AT. See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
LONG_AT = 52.0
SHORT_AT = None


def score(df):
    return regime_score(df, "long", W, 1105, 1330, gate='fo-', k_cost=2.0, use_heat=False)
