"""pod-r3-eod-loser-reversal-spy-newhod-long-t05s1 - the stated second geometry (t05s1) of
pod-r3-eod-loser-reversal-spy-newhod-long: same mask (SPY new session high > +0.2% after 14:00, stock fromOpen <=
-2%, gap > -6%, stabilised off a LOD set >= 6 bars ago, flow3 > 0, rsi 30..50), exit t05s1 (target 0.5R, stop 1R,
R = 0.25 x daily ATR, flat 15:55).

Source: Baltussen, Da & Soebhag, 'End-of-Day Reversal' (OptionMetrics research summary).
URL: https://optionmetrics.com/research/a-soebhag-g-baltussen-and-z-da-end-of-day-reversal/
Pre-declared second geometry from the idea text; not a tweak. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-r3-eod-loser-reversal-spy-newhod-long.py"
_spec = importlib.util.spec_from_file_location("_eod_spy_newhod_base", _p)
_B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_B)

SIDE = "long"
GEOM = "t05s1"
WINDOW = _B.WINDOW
CONTEXT = _B.CONTEXT
LAYERS = _B.LAYERS[:-1] + ["t05s1, flat 15:55"]


def mask(df):
    return _B.mask(df)
