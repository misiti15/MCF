"""directional_8: SHORT only. Fade-the-stretch heat (vw), bars 1300-1430 ET, cost <= 0.05R.
Educational only - not financial advice.
score = stretch_short(vw) + time/cost gate (-100 outside). Score is NEGATED: short when score <= SHORT_AT.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _directional_common import stretch, gates

LONG_AT = None
SHORT_AT = -12.0


def score(df):
    return -(stretch(df, "short", "vw") + gates(df, 1300, 1430, 0.05))
