"""RC1-volconfirm-ema8-vol-t2r-long - Reddit scout 2026-10-30 (research/bdi/reddit_1030/PLAN.md). RS stock pullback test of ema8, volume sequence on, exit t2r.
Educational only - not financial advice."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _rc_util as U  # noqa: E402
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1500)
MIN_ADV = 95e6


def stop_price(f, i):
    return float(f["_rc_stop"].iloc[i])


def mask(df):
    return U.volconfirm(df, "ema8", True)


def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + 2.0 * (px - stop)
