"""pod-raschke-daily-7close-below-5sma-intraday-reclaim-long-holdtr - holdtr companion of
pod-raschke-daily-7close-below-5sma-intraday-reclaim-long: same entries, GEOM holdtr (stop 1R = 0.25 x daily ATR,
then a 1R trail once the trade is +1R, flat 15:55).
Source: Linda Raschke 5-SMA / extended-run rule ('Raschke Trade Sheet (scanner)', TradingView).
URL: https://kr.tradingview.com/script/8MVLfKu4-Raschke-Trade-Sheet-scanner/
Rules: see the parent module; only the exit differs (the idea asked to also score a holdtr variant).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-raschke-daily-7close-below-5sma-intraday-reclaim-long.py"
_s = importlib.util.spec_from_file_location("_r37_d5sma_parent_holdtr", _p)
_m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
SIDE = "long"
GEOM = "holdtr"
WINDOW = _m.WINDOW
LAYERS = _m.LAYERS[:-1] + ["holdtr: stop 0.25 ATR, 1R trail after +1R, flat 15:55"]


def mask(df):
    return _m.mask(df)
