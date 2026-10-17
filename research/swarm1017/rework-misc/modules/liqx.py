"""Liquidity-sweep signal machine for the swarm1017 rework-misc LIQ variants (lab modules in this folder).
Educational only - not financial advice.

Port of research/bdi/reddit1012liq/live/liq_live_lib.py (score.k_liq semantics), with two changes so the 2-year
history frames (rows from the 09:50 bar) and the live LabStrategy frame (rows from 09:35) give the same signals:
  * the machine runs only on rows with bar close >= 09:50 (live rows before 09:50 are ignored);
  * levels come from decision-time features: OR low/high = low/high of day at the 10:00 bar (close -/+ dist_lod/hod_atr
    x atr_d), PD low/high = prior-day low/high (close -/+ dist_pdl/pdh_atr x atr_d).
`flags(df, level, sweep, x, trig, k)` -> bool array (len(df)): True on the 5-minute row that closes the k-minute trigger
bar of a sweep-reversal. sweep 'low' = price trades x ATR below the level from above, then reclaims (long reversal);
'high' mirrors it. Uses only close / high / low / tod / atr_d / fromOpen / dist_* columns.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


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


def machine(h, l, c, O, L, avail, atr, new, W, x, trig):
    """score.k_liq short semantics on k-bars; trig 0 = 'lvl', 1 = 'open'. Returns int array of fire indices."""
    out = np.empty(len(c), np.int64)
    m = 0
    ins = False
    s = 0
    Ls = 0.0
    Os = 0.0
    prevc = 0.0
    for i in range(len(c)):
        if new[i]:
            ins = False
            prevc = O[i]
        if ins and i - s >= W:
            ins = False
        if ins:
            if trig == 0:
                fire = c[i] < Ls
            else:
                fire = c[i] < Os
            if fire:
                out[m] = i
                m += 1
                ins = False
        else:
            Li = L[i]
            if avail[i] and not math.isnan(Li) and prevc < Li and h[i] >= Li + x * atr[i]:
                ins, s, Ls, Os = True, i, Li, prevc
                if trig == 0 and c[i] < Ls:
                    out[m] = i
                    m += 1
                    ins = False
        prevc = c[i]
    return out[:m]


_MACHINE = machine


def use_numba():
    """Research only: JIT the same machine (identical source) for the 2-year scan."""
    global _MACHINE
    from numba import njit
    _MACHINE = njit(cache=False)(machine)


def flags(df: pd.DataFrame, level: str, sweep: str, x: float, trig: str, k: int) -> np.ndarray:
    n_all = len(df)
    out = np.zeros(n_all, bool)
    if not n_all:
        return out
    tod_all = df["tod"].to_numpy(np.int64)
    pos = np.flatnonzero(tod_all >= 950)
    if not len(pos):
        return out
    d = df.iloc[pos]
    new5, seg5 = _segments(d)
    tod = tod_all[pos]
    c5, h5, l5 = (d[k_].to_numpy(float) for k_ in ("close", "high", "low"))
    atr5 = d["atr_d"].to_numpy(float)
    atr = pd.Series(atr5).groupby(seg5).transform("first").to_numpy(float)
    dopen = pd.Series(c5 / (1 + d["fromOpen"].to_numpy(float) / 100)).groupby(seg5).transform("first").to_numpy(float)
    n = len(d)
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
    s = -1 if sweep == "high" else 1          # high sweep -> short semantics directly; low sweep -> negate
    if s < 0:
        hh, ll, cc = hk, lk, ck
    else:
        hh, ll, cc = -lk, -hk, -ck
    O = np.r_[np.nan, cc[:-1]]
    O = np.where(newk, dopen[r] * (-s), O)
    if level == "PD":
        if s < 0:
            v = c5 + d["dist_pdh_atr"].to_numpy(float) * atr5
        else:
            v = -(c5 - d["dist_pdl_atr"].to_numpy(float) * atr5)
        lev = pd.Series(v).groupby(seg5).transform("first").to_numpy(float)[r]
        avail = np.ones(len(r), bool)
    elif level == "OR":
        if s < 0:
            v = c5 + d["dist_hod_atr"].to_numpy(float) * atr5
        else:
            v = -(c5 - d["dist_lod_atr"].to_numpy(float) * atr5)
        lev = pd.Series(np.where(tod == 1000, v, np.nan)).groupby(seg5).transform("max").to_numpy(float)[r]
        avail = tod[r] >= 1005
    else:
        raise ValueError(level)
    j = _MACHINE(hh.astype(float), ll.astype(float), cc.astype(float), O.astype(float), lev.astype(float),
                 avail, atr[r].astype(float), newk, 60 // k, float(x), 1 if trig == "open" else 0)
    if len(j):
        j = j[ok[j]]
        out[pos[r[j]]] = True
    return out


def vwap(df):
    return df["close"].to_numpy(float) / (1 + df["vwapDistPct"].to_numpy(float) / 100)
