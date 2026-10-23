"""_r39_util - shared helpers for the pod r3_9 modules (Zarattini noise-band failed break, QuantRocket/Gao first +
penultimate half hour, VSA effort-vs-result, absorption box, Wyckoff low-volume spring, Valentini second failed IB
probe). Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry (all causal):
  * full-session 5m bars 09:35..15:00 with volume (_r37_util.vbars: h / l / c from the history frames + head table,
    volume from the _r24 cache, open = previous bar's close / the 09:30 open for 09:35; previous open month as
    warm-up, the rule-19 locked block is never read).
  * daily values as of D-1's close (lib.daily(), completed days only, every series restarts after a > 7-day gap so
    nothing bridges the locked block): D-1 range, the median of the 20 daily ranges D-20..D-1, and the 10-day average
    daily range (% of close) vs the median of that series over D-60..D-1.
  * the Zarattini noise sigma per (symbol, date D, tod): mean over the 14 PRIOR sessions of |close at tod / that
    day's 09:30 open - 1|.
Callers use a bar's values only on that bar or later. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as C3  # noqa: E402
import _r37_util as U37  # noqa: E402

_LOCKED = ("2024-11-01", "2025-02-28")
_MEM = {}
f, key, start, lag, base, map_day, spy_rows = U37.f, U37.key, U37.start, U37.lag, U37.base, U37.map_day, U37.spy_rows
vbars, to_frame = U37.vbars, U37.to_frame


def daily_tab():
    if "d" in _MEM:
        return _MEM["d"]
    d = C3.lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    assert not ((d["date"] >= _LOCKED[0]) & (d["date"] <= _LOCKED[1])).any()
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum().to_numpy()
    rng = d["high"] - d["low"]
    rngp = rng / d["close"] * 100.0
    gb = lambda s: s.groupby(g)
    med20 = gb(rng).transform(lambda x: x.rolling(20, min_periods=20).median())
    avg10p = gb(rngp).transform(lambda x: x.rolling(10, min_periods=10).mean())
    med60_avg10p = gb(avg10p).transform(lambda x: x.rolling(60, min_periods=60).median())
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    for nm, s in {"rng": rng, "rngmed20": med20, "avg10p": avg10p, "avg10p_med60": med60_avg10p,
                  "high": d["high"], "low": d["low"]}.items():
        out[nm + "1"] = s.groupby(g).shift(1).to_numpy()        # as of D-1 (row D)
    _MEM["d"] = out
    return out


def map_daily(df, cols):
    return map_day(df, daily_tab(), cols)


def flags(X):
    """newday per vbars row: 2 = new symbol, 1 = new day of the same symbol, 0 = continuation."""
    sym = X["symbol"].to_numpy()
    dn = X["dn"].to_numpy(np.int64)
    nd = np.zeros(len(X), np.int64)
    if len(X):
        nd[0] = 2
        nd[1:] = np.where(sym[1:] != sym[:-1], 2, np.where(dn[1:] != dn[:-1], 1, 0))
    return nd


def noise_sigma(df):
    """Per frame row: sigma at this bar's tod = mean |c_tod / o935 - 1| over the 14 prior sessions (NaN if < 14)."""
    X = vbars(df)
    if X is None or not len(X):
        return np.full(len(df), np.nan)
    ck = ("sig", id(X))
    if ck not in _MEM:
        for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "sig"]:
            del _MEM[kk]
        T = X[["symbol", "dn", "tod"]].copy()
        T["mv"] = (X["c"].to_numpy(float) / X["o935"].to_numpy(float) - 1.0).__abs__()
        T = T.sort_values(["symbol", "tod", "dn"], kind="mergesort")
        T["sig"] = T.groupby(["symbol", "tod"])["mv"].transform(
            lambda s: s.shift(1).rolling(14, min_periods=14).mean())
        _MEM[ck] = T
    return to_frame(df, _MEM[ck], ["sig"])["sig"]


import numba  # noqa: E402


@numba.njit(cache=False)
def _prior_mean(newg, x, nwin):
    """Mean of x over the nwin PRIOR rows of the same group (rows sorted by group, then time); NaN if fewer than
    nwin finite values."""
    n = len(x)
    out = np.full(n, np.nan)
    g0 = 0
    for i in range(n):
        if newg[i]:
            g0 = i
        s = 0.0
        cnt = 0
        j = i - 1
        while j >= g0 and cnt < nwin:
            if x[j] == x[j]:
                s += x[j]
                cnt += 1
            j -= 1
        if cnt == nwin:
            out[i] = s / nwin
    return out


def same_tod_prior_mean(X, col, nwin=20):
    """Per vbars row: mean of X[col] at the same (symbol, tod) over the nwin prior sessions."""
    T = X[["symbol", "dn", "tod"]].copy()
    T["x"] = X[col].to_numpy(float)
    T["_r"] = np.arange(len(T))
    T = T.sort_values(["symbol", "tod", "dn"], kind="mergesort")
    sym = T["symbol"].to_numpy()
    td = T["tod"].to_numpy(np.int64)
    newg = np.r_[True, (sym[1:] != sym[:-1]) | (td[1:] != td[:-1])] if len(T) else np.zeros(0, bool)
    o = np.full(len(T), np.nan)
    o[T["_r"].to_numpy()] = _prior_mean(newg, T["x"].to_numpy(float), nwin)
    return o


def spy_first_hour(df):
    """Per frame row: SPY close at this (date, tod), and SPY's 09:30-10:30 high / low (bars closing 09:35..10:30;
    use only on rows with tod >= 1030)."""
    import _r24_bars as R24
    if "spyfh" not in _MEM:
        S = R24.spy_bars().copy()
        S["date"] = S["date"].astype(str)
        fh = S[S["tod"] <= 1030].groupby("date").agg(fh_h=("h", "max"), fh_l=("l", "min"), nfh=("h", "size"))
        S = S.merge(fh.reset_index(), on="date", how="left")
        S.loc[S["nfh"] < 12, ["fh_h", "fh_l"]] = np.nan
        S["tod"] = S["tod"].astype(np.int64)
        _MEM["spyfh"] = S[["date", "tod", "c", "fh_h", "fh_l"]]
    k = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64)})
    m = k.merge(_MEM["spyfh"], on=["date", "tod"], how="left")
    return {c: m[c].to_numpy(float) for c in ("c", "fh_h", "fh_l")}


def run_kernel(df, kern, extra=(), cols=("m", "s", "t")):
    """Run a numba kernel over vbars (nd, tod, o, h, l, c, v, atr, *extra arrays) and map its outputs to frame rows."""
    n = len(df)
    X = vbars(df)
    if X is None or not len(X):
        return {c: (np.zeros(n) if c == "m" else np.full(n, np.nan)) for c in cols}
    g = lambda c: X[c].to_numpy(float)
    ex = [e(X) if callable(e) else e for e in extra]
    outs = kern(flags(X), X["tod"].to_numpy(np.int64), g("o"), g("h"), g("l"), g("c"), g("v"), g("atr"), *ex)
    T = X[["symbol", "dn", "tod"]].copy()
    for c, a in zip(cols, outs):
        T[c] = np.asarray(a, float)
    r = to_frame(df, T, list(cols))
    r["m"] = np.nan_to_num(r["m"]) == 1.0
    return r
