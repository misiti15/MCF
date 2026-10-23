"""pod-cwt-breitstein-etf-capitulation-rightV-3x - Market-wide capitulation, right side of the V: 3x index ETF config.

Source: Lance Breitstein, Chat With Traders 228/229/236 (right side of the V, capitulation reversals).
URL: https://chatwithtraders.com/228
Rules: identical to pod-cwt-breitstein-etf-capitulation-rightV.py (daily >= 3 of 4 down closes and prior close >= 2
ATR below the 10-day SMA; low bar with fromOpen <= -1.2 ATR%, a volumeRatio >= 2.5 bar in the last 6, breadth in its
point-in-time bottom decile; first higher-high + higher-low bar closing in its upper half; stop LOD - 0.05 ATR, target
VWAP at entry, flat 15:55), on the 3x ETFs TQQQ, UPRO, SPXL, TNA (the idea's 'separate config'). The ATR thresholds
use each ETF's own daily ATR. Costs in. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("_pod_bs_etf_base",
                                               Path(__file__).with_name("pod-cwt-breitstein-etf-capitulation-rightV.py"))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)

SIDE = "long"
GEOM = "S"
WINDOW = _b.WINDOW
SYMBOLS = ["TQQQ", "UPRO", "SPXL", "TNA"]
CONTEXT = _b.CONTEXT
LAYERS = _b.LAYERS + ["3x ETFs TQQQ / UPRO / SPXL / TNA"]
mask = _b.mask
stop_price = _b.stop_price
target_price = _b.target_price
