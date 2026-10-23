"""pod-zarattini-noise-lower-fail-quiet-long-ctrl-nonquiet - CONTROL for pod-zarattini-noise-lower-fail-quiet-long:
the same failed lower noise-band break reclaim (rules 2-4, same stop / VWAP target / window / symbols) on NON-quiet
days (|gap| > 0.30% or prior-day range > its 20-day median).
Source: Zarattini, Aziz, Barbon, 'Beat the Market' noise area, via Quantified Strategies.
URL: https://quantifiedstrategies.substack.com/p/systematic-intraday-trend-following
Control only, not a candidate. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent / "pod-zarattini-noise-lower-fail-quiet-long.py"
_s = importlib.util.spec_from_file_location("_zar_main_r39", _p)
_M = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_M)

SIDE, GEOM, WINDOW, SYMBOLS, CONTEXT = _M.SIDE, _M.GEOM, _M.WINDOW, _M.SYMBOLS, _M.CONTEXT
_ST = {}


def mask(df):
    m, s, t = _M.compute(df, quiet=False)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return m


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
