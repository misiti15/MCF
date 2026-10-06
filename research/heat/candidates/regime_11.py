"""regime_11: SHORT only. ORIGINAL heat short, 10:00-11:00, gap-down names, cost-aware.
Educational only - not financial advice.
weights (long orientation, base = original MarcoFlow heat): heat
regime gates: tod 1000-1100 ET bar close, gap-; cost term k=4 (x 100*0.08/atr_d).
short when score <= SHORT_AT (score is the negated short score). See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {}
LONG_AT = None
SHORT_AT = -28.5


def score(df):
    return regime_score(df, "short", W, 1000, 1100, gate='gap-', k_cost=4.0, use_heat=True)
