"""Derived lab-frame columns used by the escalation finalists. Educational only - not financial advice."""
import numpy as np


def col(df, c):
    return df[c].to_numpy(dtype=float)


def atr_units(df, pct_col):
    """A percent-of-price column (fromOpen, vwapDistPct) expressed in daily ATRs."""
    return col(df, pct_col) * col(df, "close") / 100.0 / col(df, "atr_d")


def hod_above_open_atr(df):
    """How far today's high of day sits above today's open, in daily ATRs (fromOpen in ATR + distance to HOD)."""
    return atr_units(df, "fromOpen") + col(df, "dist_hod_atr")


def window(df, lo, hi):
    tod = col(df, "tod")
    return (tod >= lo) & (tod <= hi)
