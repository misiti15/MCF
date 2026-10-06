"""ceiling_3: SHORT. GBM-distilled core heat at a lower threshold (more trades); cost gate 0.04R. Not viable on train.
Educational only - not financial advice.
Short when short_points >= 7.69  (score() returns the negated points, so SHORT_AT = -7.69). See _ceiling_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ceiling_common import short_points

LONG_AT = None
SHORT_AT = -7.69


def score(df):
    return -short_points(df, "core", 0.04)
