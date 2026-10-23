"""_r37_util - shared helpers for the pod r3_7 modules (Shannon max-volume-bar AVWAP, Raschke daily SMA5 down run,
Raschke compression 20-day channel, Moglen daily EMA21 pullback + PDH break, QS low-volume-day gap-up ETF).
Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry (all causal):
  * daily values as of D-1's close (lib.daily(), completed days only; the rule-19 locked block is not in lib.daily();
    every series restarts after a > 7-day gap so nothing bridges the block): SMA5 run counter (consecutive closes
    below the daily SMA5), the run's pre-run close, the sum of the last 4 closes (for today's live SMA5), SMA20 /
    SMA50 / SMA100 / EMA21, ATR14 / ATR5 / ATR20 (true-range means), the last 3 daily ranges, the 20-day high,
    the Moglen 2-5 day EMA21 pullback flag, and the prior-day dollar volume vs its 20 prior sessions.
  * full-session 5m bars 09:35..15:00 per symbol (h / l / c from _cwt3_bars.full_bars, volume from the _r24 cache),
    previous open month as warm-up; the bar open is not stored, so a bar's open = the previous bar's close (the
    09:35 bar uses the 09:30 open o935).
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
import _r24_bars as R24  # noqa: E402
import _r27_util as U27  # noqa: E402
import _r31_util as U31  # noqa: E402

_LOCKED = ("2024-11-01", "2025-02-28")
_MEM = {}
f, key, start, lag, base, segments, map_day, spy_rows = (U31.f, U31.key, U31.start, U31.lag, U31.base, U31.segments,
                                                         U31.map_day, U31.spy_rows)


@numba.njit(cache=False)
def _moglen(run, h, l, c, e21, atr):
    """Row t (a completed day): 1 when the highest high of t-9..t is on day t-5..t-2 (a 2-5 day pullback after it,
    ending at t), some low of the pullback days came within 0.3 x ATR of EMA21 and every pullback close stayed above
    EMA21 - 0.2 x ATR."""
    n = len(c)
    out = np.zeros(n)
    for t in range(n):
        if t < 9 or run[t - 9] != run[t]:
            continue
        jm = t - 9
        for j in range(t - 9, t + 1):
            if h[j] >= h[jm]:
                jm = j
        k = t - jm
        if k < 2 or k > 5:
            continue
        tag = False
        ok = True
        for j in range(jm + 1, t + 1):
            if not (e21[j] == e21[j] and atr[j] > 0):
                ok = False
                break
            if l[j] <= e21[j] + 0.3 * atr[j]:
                tag = True
            if c[j] < e21[j] - 0.2 * atr[j]:
                ok = False
        if ok and tag:
            out[t] = 1.0
    return out


def daily_tab():
    if "d" in _MEM:
        return _MEM["d"]
    d = C3.lib().daily()[["symbol", "date", "open", "high", "low", "close", "dollar_volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    assert not ((d["date"] >= _LOCKED[0]) & (d["date"] <= _LOCKED[1])).any()
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    h, l, c, dv = d["high"], d["low"], d["close"], d["dollar_volume"]
    gb = lambda s: s.groupby(g)
    roll = lambda s, w, fn="mean": gb(s).transform(lambda x: getattr(x.rolling(w, min_periods=w), fn)())
    pos = gb(c).cumcount()
    sma5 = roll(c, 5)
    below = (c < sma5).astype(float).where(sma5.notna())
    # consecutive closes below SMA5 ending at each day
    cnt = np.zeros(len(d))
    bl = below.to_numpy()
    gr = g.to_numpy()
    for i in range(len(d)):
        if bl[i] == 1.0:
            cnt[i] = (cnt[i - 1] if i > 0 and gr[i - 1] == gr[i] else 0) + 1
    cnt_s = pd.Series(cnt)
    idx = np.arange(len(d)) - cnt.astype(np.int64)
    okidx = (idx >= 0) & (gr[np.clip(idx, 0, None)] == gr)
    prerun = np.where(okidx & (cnt > 0), c.to_numpy()[np.clip(idx, 0, None)], np.nan)
    pcl = gb(c).shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    atr14, atr5, atr20 = roll(tr, 14), roll(tr, 5), roll(tr, 20)
    e21 = gb(c).transform(lambda x: x.ewm(span=21, adjust=False).mean()).where(pos >= 41)
    sma20, sma50, sma100 = roll(c, 20), roll(c, 50), roll(c, 100)
    hi20 = roll(h, 20, "max")
    mog = _moglen(gr.astype(np.int64), h.to_numpy(float), l.to_numpy(float), c.to_numpy(float),
                  e21.to_numpy(float), atr14.to_numpy(float))
    dvavg_prev = gb(dv).transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean())   # 20 sessions before
    cur = {"c": c, "h": h, "l": l, "rng": h - l, "sma5cnt": cnt_s, "prerun": pd.Series(prerun), "sma20": sma20,
           "sma50": sma50, "sma100": sma100, "e21": e21, "atr14": atr14, "atr5": atr5, "atr20": atr20, "hi20": hi20,
           "mog": pd.Series(mog), "dvr": dv / dvavg_prev, "sum4": roll(c, 4, "sum")}
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    for nm, s in cur.items():
        out[nm + "1"] = s.groupby(g.to_numpy()).shift(1).to_numpy()          # as of D-1 (row D)
    for nm in ("rng", "sma20", "e21", "sma50"):
        out[nm + "2"] = cur[nm].groupby(g.to_numpy()).shift(2).to_numpy()
        out[nm + "3"] = cur[nm].groupby(g.to_numpy()).shift(3).to_numpy()
        out[nm + "6"] = cur[nm].groupby(g.to_numpy()).shift(6).to_numpy()
    _MEM["d"] = out
    return out


def map_daily(df, cols):
    return map_day(df, daily_tab(), cols)


# ---------------------------------------------------------------- full-session bars with volume
def vbars(df):
    """Continuous 5m bars 09:35..15:00 (symbol, dn, tod, h, l, c, v, o = previous close / o935, atr = frame atr_d of
    the day, NaN on warm-up days) sorted by symbol, dn, tod. None when missing."""
    P = C3.full_bars(df)
    B = U27.vol_bars(df)
    if P is None or B is None:
        return None
    ck = ("vb", id(P), id(B))
    if ck in _MEM:
        return _MEM[ck]
    for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "vb"]:
        del _MEM[kk]
    P = P[P["tod"] <= 1500].copy()
    P["dn"] = pd.to_datetime(pd.Series(P["date"]).astype(str)).to_numpy("datetime64[D]").astype(np.int64)
    X = P.merge(B[["symbol", "dn", "tod", "v"]], on=["symbol", "dn", "tod"], how="inner")
    X = X.sort_values(["symbol", "dn", "tod"], kind="mergesort").reset_index(drop=True)
    X["date"] = pd.Series(X["date"]).astype(str).to_numpy()
    o9 = R24.day()[["symbol", "date", "o935"]].copy()
    o9["symbol"] = o9["symbol"].astype(str)
    o9["date"] = o9["date"].astype(str)
    X = X.merge(o9, on=["symbol", "date"], how="left")
    k = pd.factorize(X["symbol"].astype(str) + "|" + X["dn"].astype(str))[0]
    po = np.r_[np.nan, X["c"].to_numpy(float)[:-1]]
    st = np.r_[True, k[1:] != k[:-1]]
    po[st] = X["o935"].to_numpy(float)[st]
    X["o"] = po
    fa = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(),
                       "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                       "atr": f(df, "atr_d")}).drop_duplicates(["symbol", "date"])
    X = X.merge(fa, on=["symbol", "date"], how="left")
    X = X.sort_values(["symbol", "dn", "tod"], kind="mergesort").reset_index(drop=True)
    _MEM[ck] = X
    return X


def to_frame(df, X, cols):
    return U27.map_bars(df, X, cols)
