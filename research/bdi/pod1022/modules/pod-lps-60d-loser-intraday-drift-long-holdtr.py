"""pod-lps-60d-loser-intraday-drift-long-holdtr - exit companion of pod-lps-60d-loser-intraday-drift-long (same
entries, GEOM holdtr: stop 1R = 0.25 x daily ATR, then a 1R trail once the trade is +1R; flat 15:55).

Source: Lou, Polk & Skouras (JFE 2019); Xu (2017) via CXO Advisory.
URL: https://www.cxoadvisory.com/momentum-investing/when-to-look-for-momentum-and-reversal-intraday/
Rules: identical to the parent (60d return bottom decile in the adv20 >= $100M / price >= $10 universe, gap <= 0,
10:00-11:00 close > VWAP with buyPressure > 0, spy_fo >= 0 or breadth >= 0.5); only the exit differs, as the idea
asked ('also score GEOM holdtr'). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-lps-60d-loser-intraday-drift-long.py"
_s = importlib.util.spec_from_file_location("_lps60_parent", _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)

SIDE = "long"
GEOM = "holdtr"
WINDOW = _m.WINDOW
MIN_ADV = _m.MIN_ADV
CONTEXT = _m.CONTEXT
LAYERS = _m.LAYERS[:-1] + ["holdtr exit"]
mask = _m.mask
