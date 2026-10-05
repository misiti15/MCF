"""Strategy interface shared by the backtester and the live/paper runner.

A strategy sees ONE symbol-day at a time through a DayContext containing bars up to "now".
In backtests `now` is the end of the day and the strategy must only use bars <= the signal
bar when deciding (all helpers in mcf.features are causal). In live trading the same code
is run every minute on the bars so far, and only signals on the latest bar are acted on.
Keeping one code path is the main defence against backtest/live drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any, ClassVar

import numpy as np
import pandas as pd

from .. import features as F


@dataclass
class Signal:
    symbol: str
    strategy: str
    side: int                    # +1 long, -1 short
    bar_index: int               # bar on which the signal is known (at its close)
    stop: float                  # protective stop price
    target: float | None = None  # take-profit price; None = hold to exit_by / flatten
    entry_type: str = "market"   # "market" = next bar open; "stop" = stop order at entry_price
    entry_price: float | None = None
    entry_valid_bars: int = 30   # for stop entries: bars the order stays working
    exit_by: time | None = None  # time-based exit (default = session flatten time)
    scale_out_r: float | None = None  # take scale_out_frac off at this many R, then stop -> breakeven
    scale_out_frac: float = 0.5
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class DayContext:
    symbol: str
    date: date
    bars: pd.DataFrame           # RTH bars for this session so far (1-minute)
    prev_close: float
    prev_high: float
    prev_low: float
    atr: float                   # daily ATR(14) as of prior close
    avg_dollar_volume: float     # 20d average as of prior close
    avg_cum_volume: np.ndarray | None = None  # avg cumulative volume by minute-of-session (prior 14d)
    avg_move: np.ndarray | None = None        # avg |close/open-1| by minute-of-session (prior 14d)
    rank_rvol: int | None = None # rank among the day's universe by opening relative volume (1 = highest)
    _cache: dict = field(default_factory=dict, repr=False)

    @property
    def gap_pct(self) -> float:
        return (self.bars["open"].iloc[0] / self.prev_close - 1) * 100

    def vwap(self) -> pd.Series:
        if "vwap" not in self._cache:
            self._cache["vwap"] = F.vwap(self.bars)
        return self._cache["vwap"]

    def vwap_std(self) -> pd.Series:
        if "vwap_std" not in self._cache:
            self._cache["vwap_std"] = F.vwap_std(self.bars, self.vwap())
        return self._cache["vwap_std"]

    def rvol(self) -> pd.Series:
        """Cumulative volume / average cumulative volume at the same minute of session."""
        if "rvol" not in self._cache:
            cum = self.bars["volume"].cumsum().to_numpy()
            mos = np.clip(F.minute_of_session(self.bars.index), 0, None)
            if self.avg_cum_volume is None or len(self.avg_cum_volume) == 0:
                r = np.full(len(cum), np.nan)
            else:
                ref = self.avg_cum_volume[np.clip(mos, 0, len(self.avg_cum_volume) - 1)]
                r = np.where(ref > 0, cum / np.where(ref > 0, ref, 1), np.nan)
            self._cache["rvol"] = pd.Series(r, index=self.bars.index)
        return self._cache["rvol"]

    def times(self) -> np.ndarray:
        if "times" not in self._cache:
            self._cache["times"] = np.array(self.bars.index.time)
        return self._cache["times"]


class Strategy:
    name: ClassVar[str] = "base"
    max_signals_per_day: int = 1

    def __init__(self, **params):
        self.params = params
        for k, v in params.items():
            setattr(self, k, v)

    def generate(self, ctx: DayContext) -> list[Signal]:
        raise NotImplementedError

    def signals(self, ctx: DayContext) -> list[Signal]:
        """generate() plus exit settings shared by every setup (from config), capped per day.
        Both the backtester and the live runner call this, never generate() directly."""
        out = self.generate(ctx)[: self.max_signals_per_day]
        so = self.params.get("scale_out_r")
        for sig in out:
            if so and sig.scale_out_r is None:
                sig.scale_out_r = so
                sig.scale_out_frac = self.params.get("scale_out_frac", 0.5)
        return out

    def eligible(self, ctx: DayContext) -> bool:
        """Cheap universe filter evaluated before generate()."""
        return True


def t(s: str | time | None) -> time | None:
    if s is None or isinstance(s, time):
        return s
    return pd.Timestamp(s).time()
