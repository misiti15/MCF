"""RB2-vwap2sd-absorb-rsidiv-vwap-long - Reddit scout 2026-10-29 (research/bdi/reddit_1029/PLAN.md). VWAP -2SD extension, close back inside above the prior high, delta proxy A; stop below the 4-bar low; exit vwap.
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _rb_util as U  # noqa: E402
SIDE = "long"
GEOM = "S"
WINDOW = (1020, 1500)
MIN_ADV = 95e6


def mask(df):
    return U.vwap_absorb(df, "A")


def stop_price(f, i):
    return float(f["_rb_stop"].iloc[i])


def target_price(f, i, stop):
    return float(f["_rb_vwap"].iloc[i])
