"""linear_model_5: LONG. Fade-the-drop ridge heat, 10:00-15:00, threshold 50.
Educational only - not financial advice.
score = 1 * [ridge heat-style score 'long_stretch' (see _linear_model_common.MODELS)] + gates (-100 outside 1000-1500 ET or cost > 0.05 R).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _linear_model_common import raw_score, gates

LONG_AT = 50.0
SHORT_AT = None


def score(df):
    s = 1 * raw_score(df, "long_stretch") + gates(df, 1000, 1500, 0.05)
    return s if LONG_AT is not None else -s
