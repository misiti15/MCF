"""pod-cwt3-colkitt-letf-rebalance-close-long-short - pre-declared companion of pod-cwt3-colkitt-letf-rebalance-close-long
(SIDE = 'short'; all other rules identical - the short mirrors: return <= -THR, close < VWAP, within 2 x ATR5 of the LOD, stop
0.125 daily ATR above).

Source: Chat With Traders EP313, Doug Colkitt (front-running mechanical ETP end-of-day rebalancing) [~00:16:21].
URL: https://chatwithtraders.com/313
Reported as one of the configurations the source asks to test; not a separately picked candidate.
Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_sp = importlib.util.spec_from_file_location(
    "_cwt3_colkitt_short", Path(__file__).resolve().parent / "pod-cwt3-colkitt-letf-rebalance-close-long.py")
_P = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(_P)
_P.SIDE = 'short'

SIDE, GEOM, WINDOW, SYMBOLS, CONTEXT, LAYERS = _P.SIDE, _P.GEOM, _P.WINDOW, _P.SYMBOLS, _P.CONTEXT, _P.LAYERS
mask, stop_price = _P.mask, _P.stop_price
