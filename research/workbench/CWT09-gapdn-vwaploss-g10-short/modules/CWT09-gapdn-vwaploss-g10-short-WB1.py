# WORKBENCH VARIANT CWT09-gapdn-vwaploss-g10-short-WB1 (research only, not enabled in any account)
# parent: CWT09-gapdn-vwaploss-g10-short (research/bdi/cwt/live/CWT09-gapdn-vwaploss-g10-short.py); Mechanic 2026-11-16 (scratch label S4).
# Change: P9 sensor: + signal-bar close below today's open. Stop / exits unchanged (GEOM "S": stop at the 09:30-10:30 high, no target, flat 15:55).
# Educational only - not financial advice.
"""Gap-Down VWAP Loss Short (10% gap) — WB1: below the day open at the signal bar (fromOpen < 0).
Parent signal unchanged (cwt_live_lib.a7, gap 10, trig 1): 10:30-15:00, a stock that gapped down 10%+ (no earnings within
4 days) traded back above VWAP during 09:35-10:30; from 10:30 the first close back below VWAP; short."""
import sys as _sys
_sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[4] / 'research' / 'bdi' / 'cwt' / 'live'))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import cwt_live_lib as L  # noqa: E402

SIDE = "short"
GEOM = "S"
LAYERS = ["A7 gap<=-10 E=out T1 S guest", "WB1: below the day open at the signal bar (fromOpen < 0)"]


def mask(df):
    m = L.a7(df, gap=10, trig=1)
    x = L.arrays(df)
    with np.errstate(invalid="ignore"):
        m &= df["fromOpen"].to_numpy(float) < 0
    return m


def stop_price(f, i):
    return L.a7_stop(f, i)
