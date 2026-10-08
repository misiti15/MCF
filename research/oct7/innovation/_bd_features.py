"""Shared, causal features for the BD (business development) candidate modules.
Educational only - not financial advice.

Works on the lab frame (many symbol-days, columns `symbol` and `date`) and on the production frame
(mcf/strategies/setups.py LabStrategy: ONE symbol, today's 5-minute rows only). Every value at a bar
uses only that bar and earlier bars of the same session.

  rsiN          Wilder RSI(N) of 5-minute closes, restarted each session (N = 2, 3, 4). NaN for the
                first N bars of the session. The lab frame starts at the 09:50 bar; production starts at
                09:35, so values in the first ~6 bars after 09:50 differ slightly between the two.
  open_px       today's open        = close / (1 + fromOpen/100)
  pc_px         prior close         = open_px / (1 + gap/100)
  hod_px/lod_px high/low of day so far (from dist_hod_atr / dist_lod_atr, which include 09:30-09:50)
  up_run/dn_run (hod - open)/ATR and (open - lod)/ATR so far
  move_atr      (close - open)/ATR (signed)
  vwap_max/min  running max/min of vwapDistPct this session (lab frame from 09:50)
"""
import numpy as np
import pandas as pd


def _groups(df):
    if "symbol" in df.columns and "date" in df.columns:
        key = df["symbol"].astype(str).to_numpy()
        d = df["date"].astype(str).to_numpy()
        k = np.char.add(np.char.add(key.astype("U"), "|"), d.astype("U"))
        # rows of a symbol-day are contiguous and time-ordered in the lab frame
        starts = np.r_[True, k[1:] != k[:-1]]
    else:
        idx = df.index
        if isinstance(idx, pd.DatetimeIndex):
            dd = idx.date
            starts = np.r_[True, dd[1:] != dd[:-1]]
        else:
            starts = np.zeros(len(df), bool)
            if len(df):
                starts[0] = True
    gid = np.cumsum(starts) - 1
    return gid, np.flatnonzero(starts)


def rsi(df, n: int) -> np.ndarray:
    c = df["close"].to_numpy(dtype=np.float64)
    gid, st = _groups(df)
    out = np.full(len(c), np.nan)
    bounds = np.r_[st, len(c)]
    for a, b in zip(bounds[:-1], bounds[1:]):
        x = c[a:b]
        if len(x) <= n:
            continue
        d = np.diff(x)
        up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
        au, ad = up[:n].mean(), dn[:n].mean()
        r = np.full(len(x), np.nan)
        r[n] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
        for i in range(n, len(d)):
            au = (au * (n - 1) + up[i]) / n
            ad = (ad * (n - 1) + dn[i]) / n
            r[i + 1] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
        out[a:b] = r
    return out


def levels(df) -> dict:
    c = df["close"].to_numpy(dtype=np.float64)
    atr = df["atr_d"].to_numpy(dtype=np.float64)
    fo = df["fromOpen"].to_numpy(dtype=np.float64)
    gap = df["gap"].to_numpy(dtype=np.float64)
    open_px = c / (1 + fo / 100)
    pc_px = open_px / (1 + gap / 100)
    hod = c + df["dist_hod_atr"].to_numpy(dtype=np.float64) * atr
    lod = c - df["dist_lod_atr"].to_numpy(dtype=np.float64) * atr
    return {"open_px": open_px, "pc_px": pc_px, "hod_px": hod, "lod_px": lod,
            "up_run": (hod - open_px) / atr, "dn_run": (open_px - lod) / atr, "move_atr": (c - open_px) / atr,
            "atr": atr, "close": c}


def at_time(df, values: np.ndarray, tod_at: int) -> np.ndarray:
    """Broadcast the value of `values` at the bar closing at `tod_at` to the later bars of the same
    session (NaN before that bar, so the feature is causal)."""
    gid, _ = _groups(df)
    tod = df["tod"].to_numpy()
    s = pd.Series(np.where(tod == tod_at, values, np.nan))
    out = s.groupby(gid).ffill().to_numpy()
    return np.where(tod >= tod_at, out, np.nan)


def running(df, values: np.ndarray, how: str) -> np.ndarray:
    gid, _ = _groups(df)
    s = pd.Series(values)
    return (s.groupby(gid).cummax() if how == "max" else s.groupby(gid).cummin()).to_numpy()
