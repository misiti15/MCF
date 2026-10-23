"""pod-cwt-breitstein-same-price-ev-gate-holdtr - New-HOD break after a below-open dip and reclaim with a market
tailwind, scored with GEOM holdtr (stop 1R = 0.25 daily ATR, 1R trail once +1R, flat 15:55) as the idea's stated proxy
for its EMA9 close trail. Entries are those of pod-cwt-breitstein-same-price-ev-gate.py.
Source: Lance Breitstein, Chat With Traders 236. URL: https://chatwithtraders.com/228
Costs in. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("_pod_bs_ev_base",
                                               Path(__file__).with_name("pod-cwt-breitstein-same-price-ev-gate.py"))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)

SIDE = "long"
GEOM = "holdtr"
WINDOW = _b.WINDOW
CONTEXT = _b.CONTEXT
LAYERS = _b.LAYERS[:-1] + ["holdtr exit (proxy for the EMA9 close trail)"]
mask = _b.mask
