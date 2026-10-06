"""linear_model_10: SHORT. Mirror of the long ridge heat, cost <= 0.02R, all session.
Educational only - not financial advice.
score = -1 * [ridge heat-style score 'long_stretch' (see _linear_model_common.MODELS)] + gates (-100 outside 950-1500 ET or cost > 0.02 R).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _linear_model_common import raw_score, gates

LONG_AT = None
SHORT_AT = -7.0


def score(df):
    s = -1 * raw_score(df, "long_stretch") + gates(df, 950, 1500, 0.02)
    return s if LONG_AT is not None else -s
