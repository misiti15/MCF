"""RC1-volconfirm-vwap-vol-hold-long - Reddit scout 2026-10-30 (research/bdi/reddit_1030/PLAN.md). RS stock pullback test of vwap, volume sequence on, exit hold.
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
    return U.volconfirm(df, "vwap", True)
