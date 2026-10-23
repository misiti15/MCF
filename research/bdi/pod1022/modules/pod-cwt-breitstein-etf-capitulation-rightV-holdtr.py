"""pod-cwt-breitstein-etf-capitulation-rightV-holdtr - Market-wide capitulation, right side of the V: holdtr exit proxy.

Source: Lance Breitstein, Chat With Traders 228/229/236 (right side of the V, capitulation reversals).
URL: https://chatwithtraders.com/228
Rules: the entries of pod-cwt-breitstein-etf-capitulation-rightV.py (SPY, QQQ, IWM), scored with GEOM holdtr (stop 1R =
0.25 daily ATR, then a 1R trail once +1R, flat 15:55) as the idea's stated proxy for its prior-bar-low trail.
Costs in. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("_pod_bs_etf_base_h",
                                               Path(__file__).with_name("pod-cwt-breitstein-etf-capitulation-rightV.py"))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)

SIDE = "long"
GEOM = "holdtr"
WINDOW = _b.WINDOW
SYMBOLS = _b.SYMBOLS
CONTEXT = _b.CONTEXT
LAYERS = _b.LAYERS[:-1] + ["holdtr exit (proxy for the prior-bar-low trail)"]
mask = _b.mask
