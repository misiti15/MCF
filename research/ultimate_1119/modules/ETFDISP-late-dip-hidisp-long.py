# ETFDISP: ETF late dip after high-dispersion days (owner 2026-11-19 ~07:50 ET "Added to testing as a new setup for
# live sessions. We have the slots available currently."). Build: research/ultimate_1119/etfdisp/PLAN.md + RESULTS.md.
# Educational only - not financial advice.
"""ETFDISP-late-dip-hidisp-long - leg E of ULT-32 (exact, frozen; = the WB4 ETF late dip with ULT-32's intake, SPY
band skip, cost_r <= 0.10 and thin refire) traded ONLY after a high cross-sectional dispersion day.

Leg E (unchanged, from modules/ULT-32.py loaded as leg "E"): WB4 ETF list (124), ADV20 >= $95M (YAML min_adv),
bar close 14:00-15:00; ret3 <= -0.75%, di_diff7 >= -5, ret12 >= -1.0%, daily ATR >= 3.5967583179473883% of price;
cost_r <= 0.10; price >= $10, |gap| < 20%; skip while SPY is -0.30..-0.75% from its open and falling over 30 min;
max 2 per symbol-session, the 2nd >= 6 decision bars after the 1st. Exit t05s1 (+0.5R / -1R, R = 0.25 x daily ATR)
with a 45-minute time exit (YAML time_stop_min 45, time_stop_min_r 99), as frozen in round5/frozen.

Gate (round 6, closest miss): disp_prev >= DISP_MIN. disp_prev (mcf.strategies.lab_context, opt-in daily market
column) = std (ddof 1, %) of the PRIOR session's close-to-close returns (clipped +-50%) over the universe names with
ADV20 >= $95M, known before the open. DISP_MIN = 2.6438 = the median of the three round-6 rotation thresholds
(3.1274 / 2.5790 / 2.6438), declared in etfdisp/PLAN.md before scoring; never tuned.
Fail safe: no disp_prev column, or NaN -> no signal; no spy_fo -> no signal (ULT-32).

LIVE YAML (one entry): type lab, module this file, symbols: module, min_adv 95000000, window [1400, 1500],
geom t05s1, context [spy_fo, disp_prev], refire true, refire_cooldown 0, time_stop_min 45, time_stop_min_r 99."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

_p = Path(__file__).resolve().parent / "ULT-32.py"
_spec = importlib.util.spec_from_file_location("lab_ult32_for_etfdisp-E", _p)   # name ends "-E" -> leg E only
U32 = importlib.util.module_from_spec(_spec)
sys.modules.setdefault(_spec.name, U32)
_spec.loader.exec_module(U32)
assert U32.LEG == "E"

SIDE = "long"
GEOM = "t05s1"
DISP_MIN = 2.6438          # % ; PLAN.md: median of the round-6 rotation thresholds (frozen)
SYMBOLS = U32.W
LAYERS = [U32.LAYERS[0], U32.LAYERS[3], U32.LAYERS[4],
          f"gate: prior-session cross-sectional dispersion (ADV20 >= $95M names) >= {DISP_MIN}%",
          "45-min time exit"]


def gate(df) -> np.ndarray:
    """Per-row dispersion gate (constant within a session); False when the column is missing or NaN."""
    if "disp_prev" not in getattr(df, "columns", ()):
        return np.zeros(len(df), bool)
    d = df["disp_prev"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return d >= DISP_MIN


def mask(df) -> np.ndarray:
    g = gate(df)
    if not g.any():
        return g
    return np.asarray(U32.mask(df), dtype=bool) & g
