"""Layer features shared by setup discovery (mcf/discovery.py) and RuleStrategy (live + backtest).

A "layer" is one condition on a 5-minute bar, e.g. "RSI14 > 65" or "below 20 SMA". A rule is 1-3
layers ANDed together plus a direction. Discovery and trading call the SAME `layer_frame`, so a rule
means exactly the same thing in the miner, the backtester and the live runner.

Decisions are made at the CLOSE of a 5-minute bar; RSI/SMA warm up on the prior session's last 40
five-minute bars, VWAP/high/low of day reset each session.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import features as F

PRIOR_BARS = 40

LAYERS: dict[str, list[tuple[str, callable]]] = {
    "rsi": [("RSI14 < 35", lambda f: f.rsi < 35), ("RSI14 35-65", lambda f: (f.rsi >= 35) & (f.rsi <= 65)),
            ("RSI14 > 65", lambda f: f.rsi > 65)],
    "sma": [("above 20 SMA", lambda f: f.close > f.sma20), ("below 20 SMA", lambda f: f.close < f.sma20)],
    "vwap": [("above VWAP", lambda f: f.close > f.vwap), ("below VWAP", lambda f: f.close < f.vwap)],
    "rvol": [("rvol < 1", lambda f: f.rvol < 1), ("rvol 1-2", lambda f: (f.rvol >= 1) & (f.rvol < 2)),
             ("rvol >= 2", lambda f: f.rvol >= 2)],
    "gap": [("gap down > 2%", lambda f: f.gap < -2), ("gap within 2%", lambda f: f.gap.abs() <= 2),
            ("gap up > 2%", lambda f: f.gap > 2)],
    "day": [("down > 2% from open", lambda f: f.from_open < -2),
            ("within 2% of open", lambda f: f.from_open.abs() <= 2),
            ("up > 2% from open", lambda f: f.from_open > 2)],
    "time": [("09:50-11:00", lambda f: (f.tod >= 950) & (f.tod < 1100)),
             ("11:00-13:30", lambda f: (f.tod >= 1100) & (f.tod < 1330)),
             ("13:30-15:00", lambda f: (f.tod >= 1330) & (f.tod <= 1500))],
    "extreme": [("new high of day", lambda f: f.new_hod == 1), ("new low of day", lambda f: f.new_lod == 1)],
}
LABELS = {lab: fn for opts in LAYERS.values() for lab, fn in opts}


def layer_frame(today5: pd.DataFrame, prior5: pd.DataFrame | None, prev_close: float,
                rvol_end: np.ndarray | None) -> pd.DataFrame:
    """Features at the close of each of today's complete 5-minute bars.
    rvol_end[i] = cumulative volume / average cumulative volume at the end of bar i (None -> NaN)."""
    closes = today5["close"] if prior5 is None or prior5.empty else pd.concat([prior5["close"].tail(PRIOR_BARS), today5["close"]])
    n = len(today5)
    f = pd.DataFrame(index=today5.index)
    f["close"] = today5["close"]
    f["rsi"] = F.rsi(closes, 14).iloc[-n:].to_numpy() if len(closes) >= 15 else np.nan
    f["sma20"] = closes.rolling(20).mean().iloc[-n:].to_numpy()
    typ = today5[["high", "low", "close"]].mean(axis=1)
    f["vwap"] = (typ * today5["volume"]).cumsum() / today5["volume"].cumsum().replace(0, np.nan)
    o = float(today5["open"].iloc[0])
    f["gap"] = (o / prev_close - 1) * 100 if prev_close else np.nan
    f["from_open"] = (today5["close"] / o - 1) * 100
    end = today5.index + pd.Timedelta(minutes=5)
    f["tod"] = end.hour * 100 + end.minute
    f["rvol"] = np.nan if rvol_end is None else rvol_end
    hod, lod = today5["high"].cummax(), today5["low"].cummin()
    f["new_hod"] = (today5["high"] >= hod.shift(1)).astype(int)
    f["new_lod"] = (today5["low"] <= lod.shift(1)).astype(int)
    f.iloc[0, f.columns.get_indexer(["new_hod", "new_lod"])] = 0
    return f


def rule_mask(f: pd.DataFrame, layers: list[str]) -> np.ndarray:
    m = np.ones(len(f), bool)
    for lab in layers:
        m &= np.asarray(LABELS[lab](f).fillna(False), dtype=bool)
    return m
