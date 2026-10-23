"""pod-raschke-5sma-7bar-run-first-dip-long-t15r - 1.5R-target companion of pod-raschke-5sma-7bar-run-first-dip-long:
same entries and stop (pullback low - 0.05 ATR), target = entry + 1.5R, flat 15:55.

Source: Linda Raschke 5 SMA Reversal [LuciTech] (TradingView); Raschke 'buy the first pullback after a new high'.
URL: https://it.tradingview.com/script/dyiN5wv3-Linda-Raschke-5-SMA-Reversal-LuciTech
Rules: see the parent module; only the target differs (the idea asked to also score 1R and 1.5R).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-raschke-5sma-7bar-run-first-dip-long.py"
_s = importlib.util.spec_from_file_location("_r5sma_parent_t15r", _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
_m.TMODE = 2

SIDE = "long"
GEOM = "S"
WINDOW = _m.WINDOW
LAYERS = _m.LAYERS[:-1] + ["stop pullback low - 0.05 ATR, target 1.5R"]
mask, stop_price, target_price = _m.mask, _m.stop_price, _m.target_price
