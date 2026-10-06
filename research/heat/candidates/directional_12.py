"""directional_12: SHORT only. Fade-the-stretch heat (tr), bars 1030-1500 ET, cost <= 0.02R.
Educational only - not financial advice.
score = stretch_short(tr) + time/cost gate (-100 outside). Score is NEGATED: short when score <= SHORT_AT.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _directional_common import stretch, gates

LONG_AT = None
SHORT_AT = -8.0


def score(df):
    return -(stretch(df, "short", "tr") + gates(df, 1030, 1500, 0.02))
