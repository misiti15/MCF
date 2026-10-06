"""linear_model_6: LONG. Fade-the-drop + abs terms, 10:30-14:30.
Educational only - not financial advice.
score = 1 * [ridge heat-style score 'long_stretch_abs' (see _linear_model_common.MODELS)] + gates (-100 outside 1030-1430 ET or cost > 0.05 R).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _linear_model_common import raw_score, gates

LONG_AT = 45.0
SHORT_AT = None


def score(df):
    s = 1 * raw_score(df, "long_stretch_abs") + gates(df, 1030, 1430, 0.05)
    return s if LONG_AT is not None else -s
