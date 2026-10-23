"""pod-raschke-daily-7close-below-5sma-intraday-reclaim-long-t15r - Exit B companion of
pod-raschke-daily-7close-below-5sma-intraday-reclaim-long: same entries and stop (LOD - 0.05 ATR), target = entry +
1.5R, else flat 15:55.
Source: Linda Raschke 5-SMA / extended-run rule ('Raschke Trade Sheet (scanner)', TradingView).
URL: https://kr.tradingview.com/script/8MVLfKu4-Raschke-Trade-Sheet-scanner/
Rules: see the parent module; only the exit differs (the idea asked for exit A 15:55 and exit B 1.5R).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-raschke-daily-7close-below-5sma-intraday-reclaim-long.py"
_s = importlib.util.spec_from_file_location("_r37_d5sma_parent_t15r", _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
_m.TMULT = 1.5
SIDE = "long"
GEOM = "S"
WINDOW = _m.WINDOW
LAYERS = _m.LAYERS[:-1] + ["stop LOD - 0.05 ATR, target 1.5R, else flat 15:55"]
mask, stop_price, target_price = _m.mask, _m.stop_price, _m.target_b
