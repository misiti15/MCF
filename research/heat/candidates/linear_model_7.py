"""linear_model_7: LONG. Fade-the-drop ridge heat, afternoon 13:00-14:30, cost <= 0.03R.
Educational only - not financial advice.
score = 1 * [ridge heat-style score 'long_stretch' (see _linear_model_common.MODELS)] + gates (-100 outside 1300-1430 ET or cost > 0.03 R).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _linear_model_common import raw_score, gates

LONG_AT = 35.0
SHORT_AT = None


def score(df):
    s = 1 * raw_score(df, "long_stretch") + gates(df, 1300, 1430, 0.03)
    return s if LONG_AT is not None else -s
