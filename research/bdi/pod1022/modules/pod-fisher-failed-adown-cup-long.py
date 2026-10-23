"""pod-fisher-failed-adown-cup-long - Failed 'A down', then 'C up' through the opening-range high (LONG).

Source: Mark Fisher, 'The Logical Trader' (failed A / C-up reversal). The URL was not re-checked this round.
URL: https://www.wiley.com/en-us/The+Logical+Trader%3A+Applying+a+Method+to+the+Madness-p-9780471215516

VARIANT of pod-dalton-open-rejection-reverse (level = today's open, morning only, held to PDH) and
pod-of-trapped-breakout-stall (short side, no full traverse). Stated change: the trap is a break of the OR LOW by
Fisher's A offset, the trigger is a complete move across to the OR HIGH, and the trade is held to the close.
Levels: OR = HOD / LOD as of the 09:50 bar (09:30-09:50); A_down = ORL - 0.15 x atr_d; C_up = ORH + 0.05 x atr_d.
Rules (plain English):
  1. Some bar closing 09:55-10:45 has a low <= A_down (A down reached).
  2. Later (after that bar) and with the bar close before 12:30, the first close >= C_up of the day.
  3. That bar: close > VWAP, flow3 > 0, spy_fo > -0.2%.
  4. |gap| <= 1.0%.
  Entry: that close. Stop (GEOM S): the OR midpoint, or LOD + 0.25 x (HOD - LOD) if that is tighter (higher).
  Exit: no target, flat 15:55 (Fisher holds failed-A trades for the day).
Pre-declared readings: 'the range' in the stop rule is read as the day range so far (HOD - LOD at the signal bar);
'first close >= C up' counts closes from 09:55 on (a close at/above C up before the A-down bar voids the day).
'before 12:30' = bar close <= 12:25. No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1225)
CONTEXT = ["spy_fo"]
LAYERS = ["low <= ORL - 0.15 ATR between 09:55 and 10:45", "then first close >= ORH + 0.05 ATR before 12:30",
          "close > VWAP, flow3 > 0, spy_fo > -0.2", "|gap| <= 1%", "stop max(OR mid, LOD + 0.25 range), hold to 15:55"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


@numba.njit(cache=False)
def _scan(st, tod, l, c, adn, cup):
    """True on the first close >= cup of the day (from 09:55), when it comes after an A-down bar (09:55-10:45)."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    seen_a = False
    done = False
    for i in range(n):
        if st[i]:
            seen_a = False
            done = False
        if done or tod[i] < 955:
            continue
        if c[i] >= cup[i]:
            if seen_a:
                m[i] = True
            done = True
            continue
        if tod[i] <= 1045 and l[i] <= adn[i]:
            seen_a = True
    return m


def _at(x, k, tod, T):
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        orh, orl = _at(hod, k, tod, 950), _at(lod, k, tod, 950)
        a0 = _at(atr, k, tod, 950)
        adn = np.where(np.isfinite(orl), orl - 0.15 * a0, -np.inf)
        cup = np.where(np.isfinite(orh), orh + 0.05 * a0, np.inf)
        m = _scan(_start(k), tod, _f(df, "low"), c, adn, cup)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        m &= (_f(df, "vwapDistPct") > 0) & (_f(df, "flow3") > 0) & (_f(df, "spy_fo") > -0.2)
        m &= np.abs(_f(df, "gap")) <= 1.0
        stop = np.maximum(0.5 * (orh + orl), lod + 0.25 * (hod - lod))
        m &= stop < c
    _ST[id(df)] = (stop,)
    return np.asarray(m & np.isfinite(stop), dtype=bool)
