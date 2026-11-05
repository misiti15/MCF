"""The Hunch metric ladder (owner order, one metric active at a time; the owner moves it on, never the code).

Each metric is a yes/no question about the NEXT 3-min bar (b+1), asked at bar b's close:
  M1  next bar closes higher than this bar's close              (START HERE)
  M2  next bar closes lower than this close by > X_ATR x ATR      (X_ATR = 0.25)
  M3  next bar's volume is higher than this bar's volume
  M4  next bar's high is above this bar's high
  M5  next bar's low is below this bar's low
  M6  next bar's range (h - l) is above the median range of the last 20 bars (median known at b)
Left out on purpose: "next bar opens higher / lower than this close" - in continuous trading the next open is the
last trade of this bar give or take a tick, so it is near-trivial and says nothing about the move (TRIVIAL).

Baselines (same guess slots, point in time):
  coin       50% (scored as exactly 0.5 per guess)
  same_last  the answer this question would have had one bar ago (bar b-1 -> b), e.g. M1: did this bar close up
  base_rate  the majority answer over every earlier scored guess (pooled); for M1 that is "always up" when up > 50%
  always_yes always "yes" (M1: always up)
  mom20      M1 / M4: 20-bar price momentum sign (close_b > close_{b-20} -> yes); M2 / M5: the opposite sign;
             M3 / M6: the majority of this symbol's last 20 resolved answers (persistence of the metric itself)
Educational only - not financial advice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

X_ATR = 0.25

LADDER = ["M1", "M2", "M3", "M4", "M5", "M6"]
ACTIVE = "M1"
TRIVIAL = {"M0": "next bar opens higher than this close (near-trivial: next open ~ this close) - kept out"}
DESCRIBE = {
    "M1": "next 3-min bar closes higher than this bar's close",
    "M2": f"next bar closes lower than this close by > {X_ATR} ATR",
    "M3": "next bar's volume is higher than this bar's volume",
    "M4": "next bar's high is above this bar's high",
    "M5": "next bar's low is below this bar's low",
    "M6": "next bar's range is above the median range of the last 20 bars",
}
UP_TYPE = {"M1": 1, "M4": 1, "M2": -1, "M5": -1}


def _answer(metric: str, nxt: dict, cur: dict) -> np.ndarray:
    """The metric's yes/no for a (current bar, next bar) pair given column dicts."""
    if metric == "M1":
        return nxt["c"] > cur["c"]
    if metric == "M2":
        return nxt["c"] < cur["c"] - X_ATR * cur["atr"]
    if metric == "M3":
        return nxt["v"] > cur["v"]
    if metric == "M4":
        return nxt["h"] > cur["h"]
    if metric == "M5":
        return nxt["l"] < cur["l"]
    if metric == "M6":
        return (nxt["h"] - nxt["l"]) > cur["range_med20"]
    raise KeyError(metric)


def label(panel: pd.DataFrame, metric: str) -> np.ndarray:
    """Answer for bar b (needs bar b+1 of the same symbol-session). NaN where there is no next bar.
    This is the ONLY place that looks at bar b+1; features never do."""
    g = panel.groupby(["symbol", "date"], sort=False)
    cols = ["c", "v", "h", "l"]
    nxt = {k: g[k].shift(-1).to_numpy() for k in cols}
    cur = {k: panel[k].to_numpy() for k in cols + ["atr", "range_med20"]}
    y = _answer(metric, nxt, cur).astype(float)
    y[np.isnan(nxt["c"])] = np.nan
    return y


def same_last(panel: pd.DataFrame, metric: str) -> np.ndarray:
    """The answer the metric had for bar b-1 -> b (known at b's close)."""
    g = panel.groupby(["symbol", "date"], sort=False)
    cols = ["c", "v", "h", "l", "atr", "range_med20"]
    prv = {k: g[k].shift(1).to_numpy() for k in cols}
    cur = {k: panel[k].to_numpy() for k in ["c", "v", "h", "l"]}
    y = _answer(metric, cur, prv).astype(float)
    y[np.isnan(prv["c"])] = np.nan
    return y


def mom20(panel: pd.DataFrame, metric: str) -> np.ndarray:
    if metric in UP_TYPE:
        c = panel["c"]
        m = (c - panel.groupby("symbol", sort=False)["c"].shift(20)).to_numpy()
        return (UP_TYPE[metric] * m > 0).astype(float)
    sl = pd.Series(same_last(panel, metric))
    roll = sl.groupby(panel["symbol"].to_numpy()).transform(lambda s: s.rolling(20, min_periods=1).mean())
    return (roll.to_numpy() > 0.5).astype(float)
