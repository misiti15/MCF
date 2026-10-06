"""Prior-day statistics for the live universe, built once before the open.

The backtester derives these from weeks of 1-minute history (`SymbolHistory`). Doing that live for
~5,000 symbols means ~80M bars, so the live runner uses this compact equivalent instead:

  daily bars (30 sessions)       -> prev close/high/low, ATR(14), 20d ADV, avg share volume
  5-minute bars (14 sessions)    -> average cumulative volume by minute of session (rvol baseline),
                                    exact at every 5-minute boundary (incl. the 5-minute opening
                                    range used by ORB), linearly interpolated in between
  1-minute bars (index ETFs only)-> exact cumulative volume and the noise-band move profile

Everything uses sessions strictly before `day` (no look-ahead).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from .. import features as F
from .bars import TZ, normalize, rth

SESSION_MIN = 390


@dataclass
class Prior:
    prev_close: float
    prev_high: float
    prev_low: float
    atr: float
    adv: float
    avg_volume: float                 # 20d average shares/day
    avg_cum: np.ndarray | None        # len 390
    avg_move: np.ndarray | None       # len 390, index ETFs only
    tail5: pd.DataFrame | None = None  # prior sessions' last 40 five-minute bars (rule-layer warm-up)
    sma20: float = float("nan")        # 20-day SMA of daily closes through the prior session


def _client():
    from alpaca.data.historical import StockHistoricalDataClient

    return StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])


def _bars(dc, symbols, start, end, minutes: int | None, feed: str, batch: int = 100, workers: int = 8) -> pd.DataFrame:
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    from concurrent.futures import ThreadPoolExecutor

    tf = TimeFrame.Day if minutes is None else TimeFrame(minutes, TimeFrameUnit.Minute)

    def one(i):
        req = StockBarsRequest(symbol_or_symbols=symbols[i:i + batch], timeframe=tf, start=start, end=end,
                               adjustment=Adjustment.SPLIT, feed=DataFeed(feed))
        for attempt in range(3):
            try:
                return dc.get_stock_bars(req).df
            except Exception as e:  # transient API errors: retry, then give up on this batch only
                if attempt == 2:
                    print(f"bars batch {i} failed: {e}")
        return pd.DataFrame()

    with ThreadPoolExecutor(max_workers=workers) as ex:
        out = [df for df in ex.map(one, range(0, len(symbols), batch)) if not df.empty]
    return pd.concat(out) if out else pd.DataFrame()


def _daily_part(df: pd.DataFrame, day: date) -> dict[str, dict]:
    res = {}
    for sym, g in df.groupby(level=0):
        g = g.droplevel(0)
        g.index = pd.DatetimeIndex(g.index).tz_convert(TZ)
        g = g[g.index.date < day].tail(30)
        if len(g) < 15:
            continue
        a = F.atr(g.rename(columns=str.lower)).iloc[-1]
        last = g.iloc[-1]
        res[sym] = dict(prev_close=float(last["close"]), prev_high=float(last["high"]), prev_low=float(last["low"]),
                        atr=float(a), adv=float((g["close"] * g["volume"]).tail(20).mean()),
                        avg_volume=float(g["volume"].tail(20).mean()),
                        sma20=float(g["close"].tail(20).mean()))
    return res


def _profile(intraday: pd.DataFrame, step: int) -> np.ndarray | None:
    """Average cumulative volume per minute of session from `step`-minute bars."""
    prof = F.cum_volume_profile(intraday)          # columns = bar start minute
    if len(prof) < 5:
        return None
    avg = prof.tail(14).mean()
    # cum at a bar's start-minute column covers volume through minute col+step-1
    x = np.asarray(avg.index, dtype=float) + step - 1
    y = avg.to_numpy(dtype=float)
    grid = np.arange(SESSION_MIN, dtype=float)
    return np.interp(grid, np.concatenate([[-1.0], x]), np.concatenate([[0.0], y]))


def _move_profile(intraday: pd.DataFrame) -> np.ndarray | None:
    mos = F.minute_of_session(intraday.index)
    day_open = intraday.groupby(intraday.index.date)["open"].transform("first")
    mv = pd.DataFrame({"date": intraday.index.date, "mos": mos,
                       "m": (intraday["close"] / day_open - 1).abs().to_numpy()})
    mv = mv.pivot_table(index="date", columns="mos", values="m", aggfunc="last").tail(14)
    if len(mv) < 5:
        return None
    return mv.mean().reindex(range(SESSION_MIN)).ffill().bfill().to_numpy()


def _split(df: pd.DataFrame, day: date) -> dict[str, pd.DataFrame]:
    out = {}
    for sym, g in df.groupby(level=0):
        g = rth(normalize(g.droplevel(0)))
        out[sym] = g[g.index.date < day]
    return out


def build_priors(symbols: list[str], day: date, feed: str = "sip", exact_symbols: list[str] = (),
                 client=None, log=print) -> dict[str, Prior]:
    dc = client or _client()
    end = datetime.combine(day, datetime.min.time())
    t0 = datetime.now()
    daily = _daily_part(_bars(dc, symbols, end - timedelta(days=50), end, None, feed), day)
    log(f"priors: daily stats for {len(daily)}/{len(symbols)} symbols ({(datetime.now() - t0).seconds}s)")
    syms = [s for s in symbols if s in daily]
    t0 = datetime.now()
    five = _split(_bars(dc, syms, end - timedelta(days=24), end, 5, feed), day)
    log(f"priors: 5-min volume profiles for {len(five)} symbols ({(datetime.now() - t0).seconds}s)")
    exact = _split(_bars(dc, list(exact_symbols), end - timedelta(days=24), end, 1, feed), day) if exact_symbols else {}
    out = {}
    for s in syms:
        d = daily[s]
        if s in exact and not exact[s].empty:
            cum, move = _profile(exact[s], 1), _move_profile(exact[s])
        else:
            cum, move = (_profile(five[s], 5) if s in five and not five[s].empty else None), None
        tail = five[s].tail(40) if s in five else None
        out[s] = Prior(avg_cum=cum, avg_move=move, tail5=tail, **d)
    return out
