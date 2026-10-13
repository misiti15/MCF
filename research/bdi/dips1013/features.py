"""dips1013 features (PLAN.md sections 1-2) on the [day, 78] bar arrays. Educational only - not financial advice."""
from __future__ import annotations

import numpy as np

from engine import NB, Data


def shift(a, n, fill=np.nan):
    out = np.full_like(a, fill)
    out[:, n:] = a[:, :-n]
    return out


def rsi_simple_today(C, n):
    """heat._rsi_simple on today's closes only (first changes from the 09:40 bar)."""
    d = np.diff(C, axis=1)
    g, l = np.clip(d, 0, None), np.clip(-d, 0, None)
    cg, cl = np.cumsum(np.nan_to_num(g), 1), np.cumsum(np.nan_to_num(l), 1)
    out = np.full(C.shape, np.nan)
    sg = cg[:, n - 1:] - np.c_[np.zeros((C.shape[0], 1)), cg[:, :-n]]
    sl = cl[:, n - 1:] - np.c_[np.zeros((C.shape[0], 1)), cl[:, :-n]]
    with np.errstate(all="ignore"):
        rsi = np.where(sl == 0, 100.0, 100 - 100 / (1 + (sg / n) / (sl / n)))
    out[:, n:] = rsi
    return out


def ema_today(C, span=9):
    a = 2 / (span + 1)
    e = np.empty_like(C)
    e[:, 0] = C[:, 0]
    for k in range(1, C.shape[1]):
        e[:, k] = a * C[:, k] + (1 - a) * e[:, k - 1]
    return e


def streak_down(C):
    s = np.zeros(C.shape)
    for k in range(1, C.shape[1]):
        s[:, k] = np.where(C[:, k] < C[:, k - 1], s[:, k - 1] + 1, 0)
    return s


def part_a(D: Data):
    C, H, L, VW = D.C, D.H, D.L, D.VW
    atr = D.atr[:, None]
    b = D.b
    early = np.zeros((D.N, NB), bool)
    early[:, :3] = True                                    # frame features exist from the 09:50 bar
    rsi5 = np.where(early, np.nan, b["RSI5"].astype(float))
    rsi14 = np.where(early, np.nan, b["RSI14"].astype(float))
    sma20d = np.where(early, np.nan, b["SMA20D"].astype(float))
    rsi2 = rsi_simple_today(C, 2)
    with np.errstate(invalid="ignore"):
        sma = C / (1 + sma20d / 100)
        OS = {
            "rsi2-5": rsi2 <= 5, "rsi2-10": rsi2 <= 10,
            "rsi5-15": rsi5 <= 15, "rsi5-25": rsi5 <= 25,
            "rsi14-25": rsi14 <= 25, "rsi14-30": rsi14 <= 30,
            "vwap-0.5": (VW - C) / atr >= 0.5, "vwap-1.0": (VW - C) / atr >= 1.0,
            "sma20-0.5": (sma - C) / atr >= 0.5, "sma20-1.0": (sma - C) / atr >= 1.0,
            "bb-2.0": C < b["BB2"], "bb-2.5": C < b["BB25"],
            "streak-3": streak_down(C) >= 3, "streak-5": streak_down(C) >= 5,
            "dfh-1.0": (D.HOD - C) / atr >= 1.0, "dfh-1.5": (D.HOD - C) / atr >= 1.5,
        }
        e9 = ema_today(C)
        pc, pvw, pe = shift(C, 1), shift(VW, 1), shift(e9, 1)
        minl3 = np.fmin(np.fmin(shift(L, 1), shift(L, 2)), shift(L, 3))
        prsi5 = shift(rsi5, 1)
        T = {
            "PBH": C > shift(H, 1),
            "RSIX": (prsi5 < 30) & (rsi5 >= 30),
            "VWR": (C > VW) & (pc <= pvw),
            "EMAR": (C > e9) & (pc <= pe),
            "HL": (L > minl3) & (C > pc),
        }
    # lookbacks: L1 = O on t-1, L3 = O on any of t-3..t-1 (today)
    OSL = {}
    for nm, o in OS.items():
        o = np.asarray(o, bool)
        s1 = shift(o.astype(np.int8), 1, 0).astype(bool)
        s2 = shift(o.astype(np.int8), 2, 0).astype(bool)
        s3 = shift(o.astype(np.int8), 3, 0).astype(bool)
        OSL[(nm, "L1")] = s1
        OSL[(nm, "L3")] = s1 | s2 | s3
    return OSL, T


def spy_nl(D: Data, name="SPY"):
    """[sess, 78]: no new session low on bar k or k-1 (LOD_k == LOD_{k-2})."""
    lod = D.m[f"{name}_LOD"].astype(float)
    out = np.zeros(lod.shape, bool)
    out[:, 2:] = lod[:, 2:] >= lod[:, :-2] - 1e-9
    return out


def mkt_fo(D: Data, name):
    return D.m[f"{name}_C"].astype(float) / D.m[f"{name}_O"].astype(float)[:, None] - 1


def mkt_mid(D: Data, name):
    c, o, lod = D.m[f"{name}_C"].astype(float), D.m[f"{name}_O"].astype(float)[:, None], D.m[f"{name}_LOD"].astype(float)
    return c > (o + lod) / 2
