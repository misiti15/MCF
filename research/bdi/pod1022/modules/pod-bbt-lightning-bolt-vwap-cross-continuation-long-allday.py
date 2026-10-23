"""pod-bbt-lightning-bolt-vwap-cross-continuation-long-allday - Lightning Bolt (LONG), the declared second config:
bar close 09:50-15:00 (the source's full 9:40-15:00 window, clipped to the scorer's 09:50 start). All rules are in
pod-bbt-lightning-bolt-vwap-cross-continuation-long.py (leg >= 0.3 / 0.6 ATR into VWAP, first close above VWAP after
>= 4 below, pullback <= 50% with volume >= 0.8x, break of the cross-bar high, stop at the last below-VWAP close /
pullback low - 0.02 ATR, target 2R, flat 15:55).
Source: Bear Bull Traders - Peter Donnelly, 'Strategy 6: Lightning Bolt'.
URL: https://bearbulltraders.com/wp-content/uploads/2023/06/2023-05-Lightning-Bolt-Pattern-vfinal.pdf
Costs in. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("_pod_bbt_lbolt_base",
                                               Path(__file__).with_name("pod-bbt-lightning-bolt-vwap-cross-continuation-long.py"))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)
_b.WINDOW = (950, 1500)

SIDE = "long"
GEOM = "S"
WINDOW = _b.WINDOW
CONTEXT = _b.CONTEXT
LAYERS = _b.LAYERS[:-1] + ["09:50-15:00", _b.LAYERS[-1]]
mask = _b.mask
stop_price = _b.stop_price
target_price = _b.target_price
