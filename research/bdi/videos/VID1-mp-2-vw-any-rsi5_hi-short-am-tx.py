"""VID1-mp-2-vw-any-rsi5_hi-short-am-tx - BDI video-digest finalist (2026-10-08), research/bdi/videos.
Ross Cameron micro-pullback: trend beyond VWAP and EMA9, a 1..2-bar pullback that touches the VWAP level and holds VWAP, entry on the first bar making a new low
Side short; exit STRUCTURAL tx: hold to 15:55, 2R hard stop; window 950-1130 ET.
Train (06-30..08-25): n 206, exp +0.1906R, day-t 2.35; valid (08-26..09-15): n 68, exp +0.3007R, day-t 2.09,
ex-best-day +0.2239R. After costs (production haircut / 1c+1bps per side +2c stops). Plateau positive.
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
    "Ross Cameron micro-pullback: trend beyond VWAP and EMA9, a 1..2-bar pullback that touches the VWAP level and holds VWAP, entry on the first bar making a new low",
    "RSI(5) >= 70",
    "bar close 950-1130 ET"
]
SPEC = {"fam": "MP", "var": {"kmax": 2, "touch": "vw", "vol": "any"}, "params": {"tol": 0.02, "vthr": 1.0}, "exit": "tx", "layers": ["rsi5_hi"], "window": [950, 1130]}
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
