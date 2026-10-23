"""pod-r3-williams-smash-day-pdh-reversal-long-t1s1 - t1s1 comparison config of
pod-r3-williams-smash-day-pdh-reversal-long (Larry Williams Smash Day buy: yesterday closed below the day-before's low,
today reclaims yesterday's high) (LONG).

Source: Larry Williams Smash Day reversal (Oxford Strategies backtest rules; RoboForex summary).
URL: https://roboforex.com/blog/education/catch-your-smash-day-with-larry-williams/
Rules: identical entry to the parent module (smash D-1, 10-session trend filter, first close above PDH with
volumeRatio >= 1.2, spy_fo > -0.3, 10:00-13:30); exit GEOM t1s1 (R = 0.25 x atr_d, target 1R, stop 1R, flat 15:55),
as the idea's 'compare with t1s1' asks. Counted as the 2nd configuration of the idea. No tweak made.
Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-r3-williams-smash-day-pdh-reversal-long.py"
_s = importlib.util.spec_from_file_location("_r29_smash_parent", _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)

SIDE = "long"
GEOM = "t1s1"
WINDOW = _m.WINDOW
CONTEXT = _m.CONTEXT
LAYERS = _m.LAYERS[:-1] + ["t1s1"]
mask = _m.mask
