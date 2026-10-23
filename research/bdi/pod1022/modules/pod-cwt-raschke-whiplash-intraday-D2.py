"""pod-cwt-raschke-whiplash-intraday-D2 - Gap below the prior-day low that recovers above VWAP, config D2 (SMB
Second-Day failure mirror, LONG): the prior day fell <= -5% or <= -2 x ATR% and closed in the bottom 25% of its range,
today opens below the PDL; 10:00-12:30 the first close above VWAP of the day (vwapReclaim == +1, no earlier close
above VWAP) with flow3 >= 0.3 and volumeRatio >= 1.3; spy_fo > -0.3%; stop max(LOD, entry - 0.6 ATR); target the
prior close capped at 2R; flat 15:55. All rules are in pod-cwt-raschke-whiplash-intraday.py.
Source: Linda Raschke 'Street Smarts' gap reversals; SMB Second-Day Play failure rule (opposite side).
URL: https://technical.traders.com/tradersonline/display.asp?art=2794
Costs in. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("_pod_whiplash_base",
                                               Path(__file__).with_name("pod-cwt-raschke-whiplash-intraday.py"))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)
_b.CFG = "D2"

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1230)
CONTEXT = _b.CONTEXT
LAYERS = _b.LAYERS
mask = _b.mask
stop_price = _b.stop_price
target_price = _b.target_price
