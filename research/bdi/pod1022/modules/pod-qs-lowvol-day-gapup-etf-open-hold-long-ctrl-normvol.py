"""pod-qs-lowvol-day-gapup-etf-open-hold-long-ctrl-normvol - companion of pod-qs-lowvol-day-gapup-etf-open-hold-long: control on NORMAL-volume prior days (prior-day dollar volume > 0.80 x its 20-day average).
Source: Quantified Strategies, 'SPY volume strategy'.
URL: https://www.quantifiedstrategies.com/?p=1817
Rules: see the parent module; only the stated parameter differs (pre-declared companion in the idea, not tuned).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-qs-lowvol-day-gapup-etf-open-hold-long.py"
_s = importlib.util.spec_from_file_location("_r37_qs_parent_ctrl-normvol".replace("-", "_"), _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
_m.LOWVOL = False
SIDE = "long"
GEOM = "S"
WINDOW = _m.WINDOW
SYMBOLS = _m.SYMBOLS
CONTEXT = _m.CONTEXT
LAYERS = _m.LAYERS + ["companion: control on NORMAL-volume prior days (prior-day dollar volume > 0.80 x its 20-day average)."]
mask, stop_price = _m.mask, _m.stop_price
