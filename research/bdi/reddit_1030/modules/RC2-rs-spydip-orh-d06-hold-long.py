"""RC2-rs-spydip-orh-d06-hold-long - Reddit scout 2026-10-30 (research/bdi/reddit_1030/PLAN.md). RS >= 1% vs SPY while SPY is >= 0.6% off its intraday high, close back above the 09:30-09:50 high with volume, exit hold.
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
