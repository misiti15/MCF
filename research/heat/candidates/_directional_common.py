"""Shared helpers for the 'directional' heat candidates (educational research only)."""
import numpy as np


def _c(df, col, lo=0.0, hi=3.0, sign=1.0):
    return np.clip(sign * np.nan_to_num(df[col].to_numpy(np.float64)), lo, hi)


def stretch(df, side, comp="eq"):
    """Stretch-from-mean heat: how far price is stretched DOWN (side='long', fade it by buying)
    or UP (side='short', fade it by shorting), from VWAP %, MACD %, EMA9-21 % and momentum %,
    each in units of a typical 'big' value. Each term is clipped to [0, 3] in raw % first."""
    s = -1.0 if side == "long" else 1.0
    v = _c(df, "vwapDistPct", sign=s) / 0.6
    m = _c(df, "macdPct", sign=s) / 0.35
    e = _c(df, "emaDiff", sign=s) / 0.3
    mo = _c(df, "momentum", sign=s) / 0.5
    if comp == "eq":
        return v + m + e + mo
    if comp == "vw":
        return 2 * v + m + e + 0.5 * mo
    if comp == "tr":       # trend-stretch heavy
        return v + 2 * m + 2 * e
    if comp == "eq_rsi":   # plus RSI(14) beyond 50 in the fade direction, 10 RSI points = 1
        r = (np.nan_to_num(df["rsi"].to_numpy(np.float64), nan=50.0) - 50) / 10 * s
        return v + m + e + mo + np.clip(r, 0, 5)
    raise ValueError(comp)


def gates(df, w0, w1, cmax):
    """Time-of-day term (bar close HHMM inside [w0, w1]) and cost term (round-trip cost
    2 x $0.01 / R <= cmax, with R = 0.25 x prior daily ATR). -100 when outside."""
    tod = df["tod"].to_numpy()
    cost = 0.08 / df["atr_d"].to_numpy(np.float64)
    bad = (tod < w0) | (tod > w1) | ~(cost <= cmax)
    return np.where(bad, -100.0, 0.0)
