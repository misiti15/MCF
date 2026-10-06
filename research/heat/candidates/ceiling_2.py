"""ceiling_2: SHORT. GBM-distilled full heat (core + gap/fromOpen/daily-ATR% terms), no cost gate.
Educational only - not financial advice.
Short when short_points >= 7.23  (score() returns the negated points, so SHORT_AT = -7.23). See _ceiling_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ceiling_common import short_points

LONG_AT = None
SHORT_AT = -7.23


def score(df):
    return -short_points(df, "full", 1.0)
