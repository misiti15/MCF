"""pod-qr-gao-first-and-penult-volgate-close-long-ctrl-short - CONTROL: the mirror short - prior close -> 10:00 and 14:30 -> 15:00 both negative, 15:00 close below VWAP, same volatility gate, stop entry + 0.15 ATR, flat 15:55.
Source: QuantRocket, 'First Half Hour Predicts Last Half Hour' (after Gao, Han, Li and Zhou).
URL: https://www.quantrocket.com/codeload/first-last/first_last/Introduction.ipynb.html
Control only, not a candidate. Symbols SPY, QQQ; entry the 15:00 bar close. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-qr-gao-first-and-penult-volgate-close-long.py"
_s = importlib.util.spec_from_file_location("_qrgao_main_r39_short", _p)
_M = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_M)

SIDE = "short"
GEOM, WINDOW, SYMBOLS = _M.GEOM, _M.WINDOW, _M.SYMBOLS
_ST = {}


def mask(df):
    m, s = _M.compute(df, -1, True)
    _ST.clear()
    _ST[id(df)] = s
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
