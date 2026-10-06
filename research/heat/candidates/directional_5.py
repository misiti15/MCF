"""directional_5: LONG only. Fade-the-stretch heat (vw), bars 1100-1300 ET, cost <= 0.02R.
Educational only - not financial advice.
score = stretch_long(vw) + time/cost gate (-100 outside). Long when score >= LONG_AT.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _directional_common import stretch, gates

LONG_AT = 10.0
SHORT_AT = None


def score(df):
    return (stretch(df, "long", "vw") + gates(df, 1100, 1300, 0.02))
