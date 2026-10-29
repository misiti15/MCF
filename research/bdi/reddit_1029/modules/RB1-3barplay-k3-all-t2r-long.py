"""RB1-3barplay-k3-all-t2r-long - Reddit scout 2026-10-29 (research/bdi/reddit_1029/PLAN.md). 3 Bar Play: igniting bar >= 3x 5m ATR, vol ratio >= 2, 1-2 resting bars in its upper half, buy the break; in-play filter off; exit t2r.
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _rb_util as U  # noqa: E402
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1500)
MIN_ADV = 95e6


def mask(df):
    return U.three_bar_play(df, 3, False)


def stop_price(f, i):
    return float(f["_rb_stop"].iloc[i])


def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + 2.0 * (px - stop)
