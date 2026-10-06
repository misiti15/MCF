"""regime_15: SHORT only. ORIGINAL heat short, 09:50-10:30, no cost term.
Educational only - not financial advice.
weights (long orientation, base = original MarcoFlow heat): heat
regime gates: tod 950-1030 ET bar close; cost term k=0 (x 100*0.08/atr_d).
short when score <= SHORT_AT (score is the negated short score). See _regime_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _regime_common import regime_score

W = {}
LONG_AT = None
SHORT_AT = -37.0


def score(df):
    return regime_score(df, "short", W, 950, 1030, gate=None, k_cost=0.0, use_heat=True)
