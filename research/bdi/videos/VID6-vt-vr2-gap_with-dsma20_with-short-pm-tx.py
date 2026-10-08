"""VID6-vt-vr2-gap_with-dsma20_with-short-pm-tx - BDI video-digest finalist (2026-10-08), research/bdi/videos.
Ross Cameron volume top (short): new high of day, upper wick >= 0.5 of the range, volumeRatio >= 2
Side short; exit STRUCTURAL tx: hold to 15:55, 2R hard stop; window 1130-1500 ET.
Train (06-30..08-25): n 137, exp +0.1882R, day-t 2.01; valid (08-26..09-15): n 82, exp +0.3168R, day-t 1.78,
ex-best-day +0.2549R. After costs (production haircut / 1c+1bps per side +2c stops). Plateau positive.
STRUCTURAL EXIT: LabStrategy only runs fixed target/stop geometries; this exit needs new exit code (see NOTES.md section 7). GEOM is None.
LIVE NEEDS: LabStrategy.generate must join features.day_features(ctx.bars, <prior-session 1-minute bars>, ctx.prior5,
ctx.avg_cum_volume, ctx.atr) and features2.day_features2(ctx.bars, <1-minute history since the anchors>, <prior-session
1-minute bars>, ctx.atr, <anchors>, ctx.prev_close), and set d_sma20 = ctx.sma20, atr_b = ctx.atr. DayContext does not
carry prior-session / multi-day 1-minute bars today (prior-day profile, prior-day and multi-day anchors).
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from vid_rules import layer, trig  # noqa: E402  (the scanner's own rule code)

SIDE = "short"
GEOM = None
EXIT = "tx"
LAYERS = [
    "Ross Cameron volume top (short): new high of day, upper wick >= 0.5 of the range, volumeRatio >= 2",
    "gap >= 1% in the trade direction",
    "close beyond the daily SMA20 on the trade side",
    "bar close 1130-1500 ET"
]
SPEC = {"fam": "VT", "var": {"kind": "vr2"}, "params": {"w": 0.5, "vr": 2.0}, "exit": "tx", "layers": ["gap_with", "dsma20_with"], "window": [1130, 1500]}
REQUIRES = "features.day_features columns + lab frame columns (rsi5, buyPressure, gap, vwapDistPct, volumeRatio, dist_pdh_atr, dist_pdl_atr, atr_d)"


def mask(df) -> np.ndarray:
    D = {k: df[k].to_numpy() for k in df.columns if k not in ("symbol", "date")}
    if "atr_b" not in D:
        D["atr_b"] = D["atr_d"]
    s = 1 if SIDE == "long" else -1
    m = np.asarray(trig(D, SPEC["fam"], s, SPEC["var"], SPEC["params"], SPEC["exit"]), bool)
    for nm in SPEC["layers"]:
        m &= np.asarray(layer(D, nm, s), bool)
    tod = np.asarray(D["tod"], float)
    return m & (tod >= SPEC["window"][0]) & (tod <= SPEC["window"][1])
