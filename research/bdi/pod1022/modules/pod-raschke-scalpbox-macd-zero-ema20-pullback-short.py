"""pod-raschke-scalpbox-macd-zero-ema20-pullback-short - SHORT mirror of
pod-raschke-scalpbox-macd-zero-ema20-pullback-long (Raschke scalping box): the MACD line < 0 for >= 12 bars, the bar
high rallies into EMA20 (by at most 0.15 x daily ATR above it), the first close below the prior bar's low within 3
bars with the MACD line < 0 throughout and the close below session VWAP; stop pullback high + 0.05 ATR, target 1.5R,
bar close 10:15-15:00, flat 15:55.

Source: TradingView 'Linda Raschke Scalping - Box Signal' (EMA 20 + MACD zero-line setup).
URL: https://de.tradingview.com/script/MRWtng3L-Linda-Raschke-Scalping-Box-Signal/
Rules: see the parent module (the idea asked for the two sides to be reported separately).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-raschke-scalpbox-macd-zero-ema20-pullback-long.py"
_s = importlib.util.spec_from_file_location("_scalpbox_parent_short", _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
_m.SIDE = "short"

SIDE = "short"
GEOM = "S"
WINDOW = _m.WINDOW
LAYERS = ["MACD line < 0 for >= 12 bars", "high rallies into EMA20 (<= 0.15 ATR above)",
          "close < prior bar low within 3 bars, MACD < 0 throughout", "close < VWAP", "10:15-15:00",
          "stop pullback high + 0.05 ATR, target 1.5R"]
mask, stop_price, target_price = _m.mask, _m.stop_price, _m.target_price
