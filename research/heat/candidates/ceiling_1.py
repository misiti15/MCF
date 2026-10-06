"""ceiling_1: SHORT. GBM-distilled core heat (cheap-to-trade, early session, calm 5-min ATR, above VWAP, MACD up); cost gate 0.04R.
Educational only - not financial advice.
Short when short_points >= 8.16  (score() returns the negated points, so SHORT_AT = -8.16). See _ceiling_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ceiling_common import short_points

LONG_AT = None
SHORT_AT = -8.16


def score(df):
    return -short_points(df, "core", 0.04)
