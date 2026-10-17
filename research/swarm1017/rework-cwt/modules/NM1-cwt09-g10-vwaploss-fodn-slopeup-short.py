"""NM1 (rework-cwt near-miss, NOT a candidate): CWT09 gap-down VWAP-loss short, gap <= -10%, plus the stock below its
open (fromOpen < 0) and a rising 20-bar SMA (sma20_slope_pct > 0) at the signal bar.
Educational only - not financial advice. FAILED the try-count bar: open history n 241, +0.191R, day-clustered t 2.49
vs bar 4.80 (A7 lineage ~99k configurations); train +0.177 / valid +0.204; up +0.168 / down +0.263; walk-forward 1.00;
ex-best-day +0.154 (research/swarm1017/rework-cwt/verify.csv). Backlog hypothesis for forward data only.
Run with type: lab, min_adv 1000000, window [1030, 1500], GEOM t1s1 (R = 0.25 x daily ATR, flat 15:55).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "bdi" / "cwt" / "live"))
import cwt_live_lib as L  # noqa: E402

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["CWT09 a7 gap <= -10%, trig 1 (first close below VWAP from 10:30 after an above-VWAP bar 09:35-10:30)",
          "fromOpen < 0", "sma20_slope_pct > 0", "window 10:30-15:00"]


def mask(df):
    fo = df["fromOpen"].to_numpy(float)
    sl = df["sma20_slope_pct"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        return L.a7(df, 10, 1) & (fo < 0) & (sl > 0)
