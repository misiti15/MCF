"""pod-cwt-breitstein-stock-multiday-flush-B - Multi-day stretched stock: intraday flush then snap-back, config B
(Breitstein: 3 red daily candles, 5-day return <= -3 ATR%, prior close >= 2.5 ATR below the 20-day SMA; climax bar
volumeRatio >= 3 making a fresh low of day with fromOpen <= -1% and vwapDistPct <= -1.5 ATR%; a pullback holds above
the climax low, then the first close above the bounce high within 6 bars of the climax; spy_fo > -1%; stop at the
climax low, target VWAP at entry, flat 15:55). All rules are in pod-cwt-breitstein-stock-multiday-flush.py.
Source: Lance Breitstein, Chat With Traders 228/229/236. URL: https://chatwithtraders.com/228
Costs in. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("_pod_bs_flush_base",
                                               Path(__file__).with_name("pod-cwt-breitstein-stock-multiday-flush.py"))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)
_b.CFG = "B"

SIDE = "long"
GEOM = "S"
WINDOW = _b.WINDOW
CONTEXT = _b.CONTEXT
LAYERS = _b.LAYERS
mask = _b.mask
stop_price = _b.stop_price
target_price = _b.target_price
