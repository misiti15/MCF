"""directional_9: SHORT only. Fade-the-stretch heat (eq), bars 1300-1430 ET, cost <= 0.03R.
Educational only - not financial advice.
score = stretch_short(eq) + time/cost gate (-100 outside). Score is NEGATED: short when score <= SHORT_AT.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _directional_common import stretch, gates

LONG_AT = None
SHORT_AT = -10.0


def score(df):
    return -(stretch(df, "short", "eq") + gates(df, 1300, 1430, 0.03))
