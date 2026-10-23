"""_r310_util - shared helpers for the pod r3_10 modules (order-flow batch 4b: Valentini imbalance LVN pullback,
trapped high-volume breakdown, SPY PDL stop-run reclaim, open-drive dry-up pullback, iceberg-floor touches,
intraday A/D divergence). Not a setup (no SIDE / mask).

Builds on _r39_util / _r37_util (full-session 5m bars 09:35..15:00 with real volume, daily values as of D-1's close,
the rule-19 locked block never read). Adds, all causal:
  * atr5(X): ATR(5m) = simple mean of the 14 latest 5m true ranges (this bar included), within one symbol.
  * vavg20(X): mean volume of the 20 bars BEFORE this bar (same symbol, may span the prior session).
  * vwap(X): session VWAP from 09:30 through this bar (typical price x volume).
  * spy_day(): SPY prior-day low / high (D-1) and the mean of SPY's 20 daily ranges D-20..D-1.
Callers use a bar's values only on that bar or later. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as C3  # noqa: E402
import _r39_util as U39  # noqa: E402

_LOCKED = ("2024-11-01", "2025-02-28")
_MEM = {}
f, vbars, to_frame, flags, run_kernel, _prior_mean = U39.f, U39.vbars, U39.to_frame, U39.flags, U39.run_kernel, \
    U39._prior_mean
spy_first_hour = U39.spy_first_hour


@numba.njit(cache=False)
def _atr5(nd, h, l, c):
    n = len(c)
    tr = np.empty(n)
    out = np.full(n, np.nan)
    s0 = 0
    for i in range(n):
        if nd[i] == 2:
            s0 = i
        if i == s0:
            tr[i] = h[i] - l[i]
        else:
            tr[i] = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        if i - 13 >= s0:
            s = 0.0
            for j in range(i - 13, i + 1):
                s += tr[j]
            out[i] = s / 14.0
    return out


@numba.njit(cache=False)
def _vavg20(nd, v):
    n = len(v)
    out = np.full(n, np.nan)
    s0 = 0
    for i in range(n):
        if nd[i] == 2:
            s0 = i
        if i - 20 >= s0:
            s = 0.0
            cnt = 0
            for j in range(i - 20, i):
                if v[j] == v[j]:
                    s += v[j]
                    cnt += 1
            if cnt == 20:
                out[i] = s / 20.0
    return out


@numba.njit(cache=False)
def _vwap(nd, h, l, c, v):
    n = len(c)
    out = np.full(n, np.nan)
    pv = 0.0
    vv = 0.0
    for i in range(n):
        if nd[i] >= 1:
            pv = 0.0
            vv = 0.0
        if v[i] == v[i] and v[i] > 0:
            pv += (h[i] + l[i] + c[i]) / 3.0 * v[i]
            vv += v[i]
        if vv > 0:
            out[i] = pv / vv
    return out


def _g(X, c):
    return X[c].to_numpy(float)


def atr5(X):
    return _atr5(flags(X), _g(X, "h"), _g(X, "l"), _g(X, "c"))


def vavg20(X):
    return _vavg20(flags(X), _g(X, "v"))


def vwap(X):
    return _vwap(flags(X), _g(X, "h"), _g(X, "l"), _g(X, "c"), _g(X, "v"))


def spy_day():
    """Per date str: SPY low1 / high1 (D-1) and rng20m1 = mean of the 20 daily ranges D-20..D-1 (completed days)."""
    if "spyd" in _MEM:
        return _MEM["spyd"]
    d = C3.lib().daily()
    d = d[d["symbol"].astype(str) == "SPY"][["date", "high", "low"]].copy()
    d["date"] = d["date"].astype(str)
    d = d.sort_values("date").reset_index(drop=True)
    assert not ((d["date"] >= _LOCKED[0]) & (d["date"] <= _LOCKED[1])).any()
    dt = pd.to_datetime(d["date"])
    g = ((dt - dt.shift()).dt.days > 7).cumsum()
    rng = d["high"] - d["low"]
    out = pd.DataFrame({"date": d["date"]})
    out["spy_low1"] = d["low"].groupby(g).shift(1).to_numpy()
    out["spy_high1"] = d["high"].groupby(g).shift(1).to_numpy()
    out["spy_rng20m1"] = rng.groupby(g).transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean()).to_numpy()
    _MEM["spyd"] = out
    return out


def daily_x(X, cols):
    """Per vbars row: the U39 / U37 daily D-1 columns (cols from _r37_util.daily_tab)."""
    import _r37_util as U37
    t = U37.daily_tab()[["symbol", "date"] + list(cols)]
    K = X[["symbol", "date"]].merge(t, on=["symbol", "date"], how="left")
    assert len(K) == len(X)
    return {c: K[c].to_numpy(float) for c in cols}

