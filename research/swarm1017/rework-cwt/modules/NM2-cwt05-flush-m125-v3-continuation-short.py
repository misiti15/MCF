"""NM2 (rework-cwt near-miss, NOT a candidate): CWT05 panic-flush signal traded the OPPOSITE way (continuation short),
deep flush (>= 1.25 ATR in 6 bars to a new low of day with a >= 3x volume climax), first bar closing above the prior
high, 11:30-13:00 only.
Educational only - not financial advice. FAILED the try-count bar: open history n 226, +0.088R (t05s1 with half banked
at +0.25R, rest to breakeven), day-clustered t 2.43 vs bar 4.64 (B5 lineage ~47k configurations); train +0.107 /
valid +0.052; up +0.147 / down +0.140; walk-forward 0.71; ex-best-day +0.079 (research/swarm1017/rework-cwt/verify.csv).
Run with type: lab, min_adv 95000000, window [1130, 1300], GEOM t05s1, scale_out_r 0.25, live_scale_out: true.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "bdi" / "cwt" / "live"))
import cwt_live_lib as L  # noqa: E402

SIDE = "short"
GEOM = "t05s1"
LAYERS = ["CWT05 b5 m 1.25 ATR / 6 bars, vol_climax >= 3, then close > prior high", "side: short (continuation)",
          "window 11:30-13:00", "exit t05s1 + scale-out half at +0.25R (live_scale_out)"]


def mask(df):
    return L.b5(df, m=1.25, v=3)
