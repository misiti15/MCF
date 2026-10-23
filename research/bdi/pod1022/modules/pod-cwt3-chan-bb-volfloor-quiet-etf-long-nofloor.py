"""pod-cwt3-chan-bb-volfloor-quiet-etf-long-nofloor - CONTROL companion of pod-cwt3-chan-bb-volfloor-quiet-etf-long:
the same rules WITHOUT the volatility floor (z = (close - SMA20) / std20, stop entry - 2 x std20 or LOD - 0.05%).

Source: Chat With Traders EP052, Ernie Chan (Bollinger mean reversion with a minimum band width) [~00:39:00].
URL: https://chatwithtraders.com/052
Reported because the idea asks for the result with and without the floor (the guest's stated point is that the floor
cuts losses on volatility-jump days). Not a separate candidate. See the parent module for the full rules.
Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_sp = importlib.util.spec_from_file_location(
    "_cwt3_chan_parent_nofloor", Path(__file__).resolve().parent / "pod-cwt3-chan-bb-volfloor-quiet-etf-long.py")
_P = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(_P)
_P.FLOOR = False

SIDE, GEOM, WINDOW, SYMBOLS, CONTEXT = _P.SIDE, _P.GEOM, _P.WINDOW, _P.SYMBOLS, _P.CONTEXT
LAYERS = [x.replace("z(floored)", "z(plain std20)") for x in _P.LAYERS]
mask, stop_price, target_price = _P.mask, _P.stop_price, _P.target_price
