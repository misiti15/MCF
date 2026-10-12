"""Shared signal code for the Testing 1 "trade liquidity" setups (research/bdi/reddit1012liq/live/*.py).
Educational only - not financial advice.

Pure-Python port of the scored sweep machine (research/bdi/reddit1012liq/score.py: k_liq, Month._kbars,
Month.candidates, trade_params), written against the LIVE LabStrategy frame (mcf/strategies/setups.py: heat_frame +
extra_features rows for today's completed 5-minute bars from 09:35). Uses only close / high / low / tod / atr_d /
fromOpen / vwapDistPct / dist_pdh_atr / dist_pdl_atr.

`sweep(df, ...)` returns (flag, E): flag is True on the 5-minute row that closes a k-minute trigger bar of a valid
sweep-reversal (validity of the configuration's stop / target included); E is the sweep extreme through that bar.
LabStrategy takes the first True row in the YAML window (09:50-15:00), which is how the scored configurations took
attempt 1. A frame holding several symbol-days (the parity check, verify.py) is split on its symbol / date columns.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

NAN = float("nan")


def _segments(df):
    n = len(df)
    if "symbol" in df.columns and "date" in df.columns and n:
        sy, dt = df["symbol"].to_numpy(), df["date"].to_numpy()
        new = np.r_[True, (sy[1:] != sy[:-1]) | (dt[1:] != dt[:-1])]
    else:
        new = np.zeros(n, bool)
        if n:
            new[0] = True
    return new, np.cumsum(new) - 1


def _first(v, seg):
    return pd.Series(v).groupby(seg).transform("first").to_numpy(float)


def _machine(h, l, c, O, L, avail, atr, new, W, x, trig):
    """score.k_liq (short semantics): candidate k-bar indices, sweep extremes."""
    out_j, out_E = [], []
    ins = False
    s = 0
    Ls = Os = E = 0.0
    rlow = 1e18
    prevc = 0.0
    for i in range(len(c)):
        if new[i]:
            ins = False
            prevc = O[i]
        if ins and i - s >= W:
            ins = False
        if ins:
            E = max(E, h[i])
            if trig == "lvl":
                fire = c[i] < Ls
            elif trig == "open":
                fire = c[i] < Os
            else:
                fire = i >= s + 2 and c[i] < rlow and c[i] < Ls
            if fire:
                out_j.append(i)
                out_E.append(E)
                ins = False
            elif i > s:
                rlow = min(rlow, l[i])
        else:
            Li = L[i]
            if avail[i] and not math.isnan(Li) and prevc < Li and h[i] >= Li + x * atr[i]:
                ins, s, Ls, Os, E, rlow = True, i, Li, prevc, h[i], 1e18
                if trig == "lvl" and c[i] < Ls:
                    out_j.append(i)
                    out_E.append(E)
                    ins = False
        prevc = c[i]
    return np.array(out_j, np.int64), np.array(out_E, float)


def sweep(df: pd.DataFrame, level: str, side: str, x: float, trig: str, k: int):
    new5, seg5 = _segments(df)
    tod = df["tod"].to_numpy(np.int64)
    c5, h5, l5 = (df[k_].to_numpy(float) for k_ in ("close", "high", "low"))
    atr = _first(df["atr_d"].to_numpy(float), seg5)
    dopen = _first(c5 / (1 + df["fromOpen"].to_numpy(float) / 100), seg5)
    n = len(df)
    flag = np.zeros(n, bool)
    Eout = np.full(n, NAN)
    if not n:
        return flag, Eout
    # k-minute bars aligned to 09:30 (bar index from the bar-end time)
    mins = (tod // 100) * 60 + tod % 100
    b = (mins - 575) // 5
    if k == 5:
        r = np.arange(n)
        hk, lk, ck, newk = h5, l5, c5, new5
        ok = np.ones(n, bool)
    else:
        grp = seg5 * 1000 + b // (k // 5)
        newg = np.r_[True, grp[1:] != grp[:-1]]
        gid = np.cumsum(newg) - 1
        r = np.r_[np.flatnonzero(newg)[1:] - 1, n - 1]
        hk = pd.Series(h5).groupby(gid).max().to_numpy()
        lk = pd.Series(l5).groupby(gid).min().to_numpy()
        ck = c5[r]
        newk = new5[np.flatnonzero(newg)]
        end = 570 + k * (b[r] // (k // 5) + 1)
        ok = tod[r] == (end // 60) * 100 + end % 60
    s = -1 if side == "short" else 1
    if s < 0:
        hh, ll, cc = hk, lk, ck
    else:
        hh, ll, cc = -lk, -hk, -ck
    O = np.r_[NAN, cc[:-1]]
    O = np.where(newk, dopen[r] * (-s), O)      # short: +open, long: -open
    if level == "PD":
        if s < 0:
            lev = _first(c5 + df["dist_pdh_atr"].to_numpy(float) * df["atr_d"].to_numpy(float), seg5)[r]
        else:
            lev = -_first(c5 - df["dist_pdl_atr"].to_numpy(float) * df["atr_d"].to_numpy(float), seg5)[r]
        avail = np.ones(len(r), bool)
    elif level == "OR":
        if s < 0:
            v = pd.Series(np.where(tod <= 1000, h5, np.nan)).groupby(seg5).transform("max").to_numpy(float)
        else:
            v = -pd.Series(np.where(tod <= 1000, l5, np.nan)).groupby(seg5).transform("min").to_numpy(float)
        lev = v[r]
        avail = tod[r] >= 1005
    else:
        raise ValueError(level)
    j, E = _machine(hh, ll, cc, O, lev, avail, atr[r], newk, 60 // k, x, trig)
    if len(j):
        keep = ok[j]
        j, E = j[keep], E[keep]
        rows = r[j]
        flag[rows] = True
        Eout[rows] = E if s < 0 else -E
    return flag, Eout


def vwap(df):
    return df["close"].to_numpy(float) / (1 + df["vwapDistPct"].to_numpy(float) / 100)


def atr_row(df):
    _, seg = _segments(df)
    return _first(df["atr_d"].to_numpy(float), seg)
