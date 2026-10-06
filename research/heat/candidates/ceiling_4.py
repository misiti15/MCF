"""ceiling_4: SHORT. CONTROL, not heat-style: cost + early-session term only. Shows the distilled edge is mostly cost/time-of-day.
Educational only - not financial advice.
Short when short_points >= 9.25  (score() returns the negated points, so SHORT_AT = -9.25). See _ceiling_common.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ceiling_common import short_points

LONG_AT = None
SHORT_AT = -9.25


def score(df):
    return -short_points(df, "control", 1.0)
