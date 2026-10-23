"""pod-moglen-pd-lasthour-undercut-open-reclaim-long-tB - target-B companion of
pod-moglen-pd-lasthour-undercut-open-reclaim-long: same entries and stop, target = the prior-day high (days where the
PDH is not above the entry are skipped), time exit 11:30.

Source: TraderLion - Richard Moglen, LEU case study (Sep 21 2025).
URL: https://traderlion.com/profile/richard-moglen/trade-opportunity-case-study-of-the-week-leu-range-breakout-and-reconfirmation-sep-21-2025/
Rules: see the parent module; only the target differs (the idea lists Target A 1.5R and Target B prior-day high).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-moglen-pd-lasthour-undercut-open-reclaim-long.py"
_s = importlib.util.spec_from_file_location("_moglen_parent_tb", _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
_m.TARGET = "B"

SIDE = "long"
GEOM = "S+x"
EXIT_TOD = 1130
WINDOW = _m.WINDOW
MIN_ADV = _m.MIN_ADV
LAYERS = _m.LAYERS[:-1] + ["target PDH, time exit 11:30"]
mask, stop_price, target_price = _m.mask, _m.stop_price, _m.target_price
