"""_r32_util - shared helpers for the pod r3_2 modules (Aziz-Zarattini index ORB, Warrior Trading pullback / first red
candle / late red-to-green / ABCD / gap-up shakeout ORB). Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry (all causal; the rule-19 locked block is never read - the r24
caches drop it at build time and every rolling series restarts after a > 10-day gap):
  * per (symbol, date): the 09:30 open, the 09:30-10:00 opening range high / low, the 10:00 close and the 09:30-09:45
    low (_r24_bars day table; used only on bars at or after 10:05, or 09:50 for the 09:45 low), and the OR width's
    median over the 20 PRIOR sessions.
  * per 5-minute bar: raw volume v, the previous 5m close (open proxy - the scorer frame has no open), the mean volume
    of the 6 bars before, the session EMA9 / EMA20 (seeded at the 09:35 close) and the cumulative relative volume
    rvol_day (_r24_bars / _r31_util).
  * SPY 5m ATR14 (simple mean of true range over the last 14 5m bars, continuous across days) and its percentile vs
    the same time-of-day slot over the 20 PRIOR sessions.
  * FOMC / CPI calendars (published in advance).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _r24_bars as R24  # noqa: E402
import _r25_util as R25  # noqa: E402
import _r27_util as U  # noqa: E402
import _r31_util as R31  # noqa: E402

FOMC = list(R25.FOMC)
CPI = list(R24.CPI_DATES)
_MEM = {}
f, key, start, lag, base = U.f, U.key, U.start, U.lag, U.base
segments = R31.segments


def day_tab():
    """Per (symbol, date): o935, dr_h, dr_l, or_l, c1000 and orw_med20 = median of (dr_h - dr_l) over the 20 prior
    sessions (min 15)."""
    if "day" in _MEM:
        return _MEM["day"]
    D = R24.day()[["symbol", "date", "o935", "or_l", "dr_h", "dr_l", "c1000"]].copy()
    D["symbol"] = D["symbol"].astype(str)
    D["date"] = D["date"].astype(str)
    D = D.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(D["date"])
    g = ((D["symbol"] != D["symbol"].shift()) | ((dt - dt.shift()).dt.days > 10)).cumsum()
    w = D["dr_h"] - D["dr_l"]
    D["orw_med20"] = w.groupby(g).transform(lambda x: x.shift(1).rolling(20, min_periods=15).median())
    _MEM["day"] = D
    return D


def map_day(df, cols):
    return R31.map_day(df, day_tab(), cols)


def bars(df):
    """Per df row: v (5m volume), cprev (previous 5m close of the same session; open proxy), v6 (mean volume of the 6
    bars before this one, same session), e9 / e20 (session EMAs), rvc (rvol_day)."""
    n = len(df)
    out = {}
    B = U.vol_bars(df)
    if B is None:
        for k in ("v", "cprev", "v6"):
            out[k] = np.full(n, np.nan)
    else:
        ck = ("b", id(B))
        if ck not in _MEM:
            for kk in [kk for kk in _MEM if isinstance(kk, tuple) and kk[0] == "b"]:
                del _MEM[kk]
            T = B[["symbol", "dn", "tod", "c", "v"]].copy()
            g = T.groupby(["symbol", "dn"], sort=False)
            T["cprev"] = g["c"].shift(1)
            T["v6"] = g["v"].transform(lambda x: x.shift(1).rolling(6, min_periods=6).mean())
            _MEM[ck] = T
        out.update(U.map_bars(df, _MEM[ck], ["v", "cprev", "v6"]))
    s = R31.sess_ind(df)
    out["e9"], out["e20"], out["rvc"] = s["e9"], s["e20"], s["rvc"]
    return out


def spy_atr_pct():
    """SPY per (date, tod): atr5 (ATR14 of 5m bars) and pct = 100 x share of the 20 prior sessions' same-slot atr5
    values strictly below today's (min 15 sessions)."""
    if "spy" in _MEM:
        return _MEM["spy"]
    S = R24.spy_bars()[["date", "tod", "h", "l", "c"]].copy()
    S["date"] = S["date"].astype(str)
    S = S.sort_values(["date", "tod"]).reset_index(drop=True)
    pc = S["c"].shift(1)
    tr = pd.concat([S["h"] - S["l"], (S["h"] - pc).abs(), (S["l"] - pc).abs()], axis=1).max(axis=1)
    S["atr5"] = tr.rolling(14, min_periods=14).mean()
    W = S.pivot(index="date", columns="tod", values="atr5").sort_index()
    dts = pd.to_datetime(pd.Series(W.index))
    seg = (dts.diff().dt.days > 10).cumsum().to_numpy()
    A = W.to_numpy(float)
    P = np.full(A.shape, np.nan)
    for i in range(A.shape[0]):
        j0 = i - 20
        if j0 < 0 or seg[j0] != seg[i]:
            continue
        prev = A[j0:i]
        ok = np.isfinite(prev)
        cnt = ok.sum(axis=0)
        below = np.where(ok, prev < A[i][None, :], False).sum(axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            P[i] = np.where((cnt >= 15) & np.isfinite(A[i]), 100.0 * below / cnt, np.nan)
    out = pd.DataFrame(P, index=W.index, columns=W.columns).stack(future_stack=True).rename("spy_atr_pct").reset_index()
    _MEM["spy"] = out
    return out


def map_spy_pct(df):
    S = spy_atr_pct()
    k = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64)})
    T = S.copy()
    T["tod"] = T["tod"].astype(np.int64)
    m = k.merge(T, on=["date", "tod"], how="left")
    assert len(m) == len(df)
    return m["spy_atr_pct"].to_numpy(float)
