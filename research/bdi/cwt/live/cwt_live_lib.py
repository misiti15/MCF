"""Shared signal code for the Testing 2 CWT setups (research/bdi/cwt/live/*.py). Educational only - not financial advice.

Pure-Python/numpy ports of the package B kernels in research/bdi/cwt/test_b/score.py (and of the package A rule A7 in
research/bdi/cwt/test_a/families.py), written against the LIVE LabStrategy frame
(mcf/strategies/setups.py: heat_frame + extra_features rows for today's completed 5-minute bars, 09:35 onwards).

Every function returns a boolean array: True on the bar where the scored configuration's signal fires. LabStrategy
then takes the first True bar inside the YAML window (decision bars 09:50-15:00), enters at that bar's close and
exits with the module's GEOM (R = 0.25 x daily ATR, flat 15:55), which is how the scored t1s1 / t05s1 / t1s05
exits were simulated.

Faithfulness notes
- Session state (high/low of day, VWAP, breakdowns, excursions) runs over every bar of the day from 09:35, as in
  package B, whose 09:35-09:45 rows were rebuilt from the 1-minute cache.
- Package B's 09:35-09:45 rows carried no volumeRatio / vol_climax (NaN, treated as "no"). Live frames do carry them,
  so `arrays` blanks those two columns before 09:50 to reproduce the scored version exactly.
- A frame holding several symbol-days (the parity check, research/bdi/cwt/live/verify.py) is split on its
  `symbol` / `date` columns; a live frame is one symbol-day.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

NAN = float("nan")


# ------------------------------------------------------------------------------------------------ frame -> arrays
class A:
    pass


def _seg_first(v: np.ndarray, seg: np.ndarray) -> np.ndarray:
    return pd.Series(v).groupby(seg).transform("first").to_numpy(float)


def arrays(df: pd.DataFrame) -> A:
    x = A()
    n = len(df)
    x.n = n
    if "symbol" in df.columns and "date" in df.columns and n:
        sy, dt = df["symbol"].to_numpy(), df["date"].to_numpy()
        new = np.r_[True, (sy[1:] != sy[:-1]) | (dt[1:] != dt[:-1])]
    else:
        new = np.zeros(n, bool)
        if n:
            new[0] = True
    x.new = new
    seg = np.cumsum(new) - 1
    x.seg = seg
    x.tod = df["tod"].to_numpy(np.int64)
    c = df["close"].to_numpy(float)
    x.c, x.h, x.l = c, df["high"].to_numpy(float), df["low"].to_numpy(float)
    atr_row = df["atr_d"].to_numpy(float)
    x.atr = _seg_first(atr_row, seg)
    x.gap = _seg_first(df["gap"].to_numpy(float), seg)
    x.open_d = _seg_first(c / (1 + df["fromOpen"].to_numpy(float) / 100), seg)
    x.pdh = _seg_first(c + df["dist_pdh_atr"].to_numpy(float) * atr_row, seg)
    x.pdl = _seg_first(c - df["dist_pdl_atr"].to_numpy(float) * atr_row, seg)
    x.pc = x.open_d / (1 + x.gap / 100)
    x.vwap = c / (1 + df["vwapDistPct"].to_numpy(float) / 100)
    early = x.tod < 950
    x.vr = np.where(early, NAN, df["volumeRatio"].to_numpy(float))
    x.vc = np.where(early, NAN, df["vol_climax"].to_numpy(float))
    x.hod = pd.Series(x.h).groupby(seg).cummax().to_numpy(float)
    x.lod = pd.Series(x.l).groupby(seg).cummin().to_numpy(float)
    return x


def prev(x: A, v, k: int = 1) -> np.ndarray:
    """v k bars back within the same symbol-day (NaN when that crosses the day start)."""
    v = np.asarray(v, float)
    out = np.full(len(v), NAN)
    if k < len(v):
        out[k:] = v[:-k] if k else v
    pos = np.arange(len(v)) - pd.Series(np.arange(len(v))).groupby(x.seg).transform("first").to_numpy()
    out[pos < k] = NAN
    return out


# ------------------------------------------------------------------------------------------------ B1 CWT04 backside
def b1(df: pd.DataFrame, a: float, trig: int) -> np.ndarray:
    """Backside lower-high short (k_b1). trig 1 = bar high reaches VWAP - 0.05 ATR and closes below VWAP;
    trig 2 = bounce retraces 38-62% of the drop and the bar closes below the prior bar's low."""
    x = arrays(df)
    c, h, l, vwap, open_d, atr, new = x.c, x.h, x.l, x.vwap, x.open_d, x.atr, x.new
    flag = np.zeros(x.n, bool)
    hod = -1e18
    bd = False
    bdrow = -1
    bdhi = -1e18
    Lmin = 1e18
    Bmax = -1e18
    for i in range(x.n):
        if new[i]:
            hod = -1e18
            bd = False
            bdhi = -1e18
            Lmin = 1e18
            Bmax = -1e18
        if h[i] > hod:
            hod = h[i]
            bd = False
            Lmin = 1e18
            Bmax = -1e18
            continue
        if bd:
            bdhi = max(bdhi, h[i])
            if i > bdrow:
                ok = False
                if trig == 1:
                    ok = h[i] >= vwap[i] - 0.05 * atr[i] and c[i] < vwap[i]
                elif Lmin < 1e17 and Bmax > -1e17 and hod > Lmin:
                    rt = (Bmax - Lmin) / (hod - Lmin)
                    ok = 0.38 <= rt <= 0.62 and c[i] < l[i - 1]
                if ok and bdhi > c[i]:
                    flag[i] = True
        if l[i] < Lmin:
            Lmin = l[i]
            Bmax = -1e18
        else:
            Bmax = max(Bmax, h[i])
        if not bd and atr[i] > 0 and hod > open_d[i]:
            run = (hod - open_d[i]) / atr[i]
            drop = (hod - c[i]) / (hod - open_d[i])
            if run >= a and drop >= 0.4 and c[i] < vwap[i]:
                bd = True
                bdrow = i
                bdhi = h[i]
    return flag


# ------------------------------------------------------------------------------------------------ B2 CWT13 VWAP stretch
def b2(df: pd.DataFrame, z: float, side: str) -> np.ndarray:
    """Stretched-from-VWAP fade: the prior bar closed within 0.05 ATR of the session extreme, >= z ATR from VWAP,
    with >= 0.4 ATR of range used; this bar makes a lower high (short) / higher low (long)."""
    x = arrays(df)
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = (x.hod - x.lod) / x.atr
        if side == "short":
            ext = ((x.hod - x.c) / x.atr <= 0.05) & ((x.c - x.vwap) >= z * x.atr) & (rng >= 0.4)
            return (prev(x, ext.astype(float)) == 1) & (x.h < prev(x, x.h))
        ext = ((x.c - x.lod) / x.atr <= 0.05) & ((x.vwap - x.c) >= z * x.atr) & (rng >= 0.4)
        return (prev(x, ext.astype(float)) == 1) & (x.l > prev(x, x.l))


# ------------------------------------------------------------------------------------------------ B3 CWT14 failed break
def b3(df: pd.DataFrame, level: str, p: float, lowvol: bool, side: str) -> np.ndarray:
    """Failed breakout / stop-run reversal (k_b3): price trades >= p ATR beyond the level (prior-day high/low, or the
    09:30-10:00 range from the 10:05 bar), then closes back inside within 3 bars; lowvol = the poke bar's
    volumeRatio < 1."""
    x = arrays(df)
    upper = side == "short"
    if level == "PD":
        L = x.pdh if upper else x.pdl
        lo_ok = np.ones(x.n, bool)
    else:
        at10 = np.where(x.tod == 1000, x.hod if upper else x.lod, NAN)
        L = pd.Series(at10).groupby(x.seg).ffill().to_numpy(float)
        lo_ok = x.tod >= 1005
    c, h, l, vr, atr, new = x.c, x.h, x.l, x.vr, x.atr, x.new
    flag = np.zeros(x.n, bool)
    inexc = stale = False
    st = 0
    v0 = NAN
    for i in range(x.n):
        if new[i]:
            inexc = stale = False
        if not lo_ok[i] or math.isnan(L[i]):
            continue
        beyond = (h[i] >= L[i] + p * atr[i]) if upper else (l[i] <= L[i] - p * atr[i])
        inside = (c[i] < L[i]) if upper else (c[i] > L[i])
        if not inexc and not stale and beyond:
            inexc = True
            st = i
            v0 = vr[i]
        if inexc:
            if inside:
                if i - st <= 3 and (not lowvol or v0 < 1):
                    flag[i] = True
                inexc = False
            elif i - st > 3:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return flag


# ------------------------------------------------------------------------------------------------ B4 CWT12 coil / flag
def b4a(df: pd.DataFrame, nco: int) -> np.ndarray:
    """Coil under resistance (k_b4a): high of day touched >= 3 times (bar highs within 0.1 ATR), the last nco bars
    each narrower than half the mean range of up to 20 earlier session bars and closing within 0.25 ATR below it."""
    x = arrays(df)
    c, h, l, hod, atr, new = x.c, x.h, x.l, x.hod, x.atr, x.new
    flag = np.zeros(x.n, bool)
    s0 = 0
    for i in range(x.n):
        if new[i]:
            s0 = i
        if i - s0 + 1 < nco + 6:
            continue
        thr = hod[i] - 0.1 * atr[i]
        touches = int((h[s0:i + 1] >= thr).sum())
        if touches < 3:
            continue
        a = i - nco + 1
        m0 = max(s0, a - 20)
        mr = float((h[m0:a] - l[m0:a]).sum()) / (a - m0)
        ok = True
        lo = 1e18
        for k in range(a, i + 1):
            if not (h[k] - l[k] < 0.5 * mr and c[k] <= hod[i] and hod[i] - c[k] <= 0.25 * atr[i]):
                ok = False
                break
            lo = min(lo, l[k])
        if ok and lo < c[i]:
            flag[i] = True
    return flag


def b4b(df: pd.DataFrame, s: float) -> np.ndarray:
    """Spike-pullback-breakout (k_b4b): push from the open >= s ATR, pullback of 30-50% of the push with every low
    above VWAP, then the first close above the push high."""
    x = arrays(df)
    c, h, l, vwap, open_d, atr, new = x.c, x.h, x.l, x.vwap, x.open_d, x.atr, x.new
    flag = np.zeros(x.n, bool)
    hod = -1e18
    L = 1e18
    above = True
    nb = 0
    for i in range(x.n):
        if new[i]:
            hod = -1e18
            L = 1e18
            above = True
            nb = 0
        if nb > 0 and hod > open_d[i] and atr[i] > 0 and (hod - open_d[i]) >= s * atr[i] and above and c[i] > hod:
            d = (hod - L) / (hod - open_d[i])
            if 0.3 <= d <= 0.5 and L < c[i]:
                flag[i] = True
        if h[i] > hod:
            hod = h[i]
            L = 1e18
            above = True
            nb = 0
        else:
            L = min(L, l[i])
            above = above and l[i] > vwap[i]
            nb += 1
    return flag


# ------------------------------------------------------------------------------------------------ B5 CWT05 panic flush
def b5(df: pd.DataFrame, m: float, v: float) -> np.ndarray:
    """Panic flush V-reversal long (k_b5): the close fell >= m ATR over 6 bars to below the prior low of day with a
    volume climax >= v on one of the last 3 bars; then the first bar closing above the prior bar's high."""
    x = arrays(df)
    c6 = prev(x, x.c, 6)
    lodp = np.nan_to_num(prev(x, x.lod, 1), nan=-1e18)
    vc = np.nan_to_num(x.vc, nan=0.0)
    vc3 = np.fmax(np.fmax(vc, np.nan_to_num(prev(x, vc, 1))), np.nan_to_num(prev(x, vc, 2)))
    c, h, atr, new = x.c, x.h, x.atr, x.new
    flag = np.zeros(x.n, bool)
    fl = False
    for i in range(x.n):
        if new[i]:
            fl = False
        if fl and i > 0 and not new[i] and c[i] > h[i - 1]:
            flag[i] = True
        if not fl and atr[i] > 0 and not math.isnan(c6[i]) and (c6[i] - c[i]) >= m * atr[i] and c[i] < lodp[i] \
                and vc3[i] >= v:
            fl = True
    return flag


# ------------------------------------------------------------------------------------------------ A7 CWT09 gap-down bounce
def a7(df: pd.DataFrame, gap: float, trig: int) -> np.ndarray:
    """Bad-news gap-down bounce short (package A, families.a7; outside the earnings blackout = the live blackout).
    Day: gap <= -gap %. Condition: a 5-minute bar high above VWAP at some bar closing 09:35-10:30.
    trig 1 (Sidial): a close below VWAP at or after the 10:30 bar.
    trig 2 (Humbled): a bounce bar reaching VWAP (or, from the 10:05 bar, the 09:30-10:00 high) that closes in the
    lower half of its range. Decision bars from 10:30 (the YAML window)."""
    x = arrays(df)
    tod, c, h, l, vw = x.tod, x.c, x.h, x.l, x.vwap
    with np.errstate(invalid="ignore"):
        above = (h > vw) & (tod <= 1030)
        cond = pd.Series(above).groupby(x.seg).cummax().to_numpy(bool)
        if trig == 1:
            m = cond & (tod >= 1030) & (c < vw)
        else:
            or30h = pd.Series(np.where(tod <= 1000, h, np.nan)).groupby(x.seg).transform("max").to_numpy(float)
            reach = (h >= vw) | ((tod >= 1005) & (h >= or30h))
            lowerhalf = (c - l) < 0.5 * (h - l)
            m = (cond | (h > vw)) & reach & lowerhalf
        return m & (x.gap <= -gap)


def a7_stop(df: pd.DataFrame, i: int) -> float:
    """A7 structural stop: the first-hour high (bars closing through 10:30) for signals at or after 10:30, else the
    session high so far."""
    tod = df["tod"].to_numpy(np.int64)
    h = df["high"].to_numpy(float)
    if tod[i] >= 1030:
        return float(np.nanmax(h[tod <= 1030]))
    return float(np.nanmax(h[: i + 1]))
