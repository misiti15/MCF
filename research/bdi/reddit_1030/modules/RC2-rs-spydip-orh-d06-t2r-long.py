"""RC2-rs-spydip-orh-d06-t2r-long - Reddit scout 2026-10-30 (research/bdi/reddit_1030/PLAN.md). RS >= 1% vs SPY while SPY is >= 0.6% off its intraday high, close back above the 09:30-09:50 high with volume, exit t2r.
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
    return U.rs_spydip_orh(df, 0.6)


def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px + 2.0 * (px - stop)
