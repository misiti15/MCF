"""Shared harness for the Reddit-hypothesis backtests (research/reddit_bt).

Same fills and costs as the backtester: mcf.backtest.engine.simulate + Costs (1c + 1 bps per side, +2c on stops,
3c per side on extended-tier names, i.e. 20-day ADV below universe.min_avg_dollar_volume). Next-bar or stop-order
entries, stop-first inside a bar, gaps through stops fill at the open. Flat by 15:55.

Splits by date (docs/RESEARCH_RULES.md):
  train  2026-07-15 .. 2026-08-25   (data/cache starts 2026-06-15; the first month is warm-up history)
  valid  2026-08-26 .. 2026-09-15
  test   2026-09-16 .. 2026-10-05   LOCKED
  q2     2026-04-01 .. 2026-06-30   LOCKED (data/cache_q2, warm-up from 2026-03-10)
  forward 2026-10-06 ..             sessions collected after the rules were frozen (mcf/research/backlog.py)
Locked splits raise unless MCF_RBT_ALLOW_HOLDOUT=1 (set only by the lead when scoring finalists once).

A strategy module exposes  signals(day: Day, variant: dict) -> list[Signal]  and is run with
    run(module, variant, split) -> metrics dict
Educational only — not financial advice.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date as Date
from functools import lru_cache

import numpy as np
import pandas as pd

from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.data.bars import resample
from mcf.data.store import BarStore
from mcf.strategies.base import Signal, t

CFG = load_config()
FLAT = t(CFG["session"]["flatten_by"])
COSTS = Costs.from_cfg(CFG["costs"])
COSTS_EXT = Costs(COSTS.bps, CFG["costs"].get("extended_slippage_per_share", 0.03), COSTS.stop_extra_per_share)
MIN_ADV = CFG["universe"]["min_avg_dollar_volume"]
SPLITS = {"train": ("2026-07-15", "2026-08-25", "data/cache"), "valid": ("2026-08-26", "2026-09-15", "data/cache"),
          "test": ("2026-09-16", "2026-10-05", "data/cache"), "q2": ("2026-04-01", "2026-06-30", "data/cache_q2"),
          "forward": ("2026-10-06", "9999-12-31", "data/cache")}
LOCKED = {"test", "q2"}


@dataclass
class Day:
    """One symbol-session. bars = 1-minute RTH bars of the day (index tz America/New_York).
    Prior-day fields use only data before `date` (no look-ahead)."""
    symbol: str
    date: Date
    bars: pd.DataFrame
    prev_close: float
    atr: float            # daily ATR(14) as of the prior close
    adv: float            # 20-day average dollar volume as of the prior close
    adv_shares: float     # 14-day average share volume
    open_vol_avg: float   # 14-day average volume 09:30-09:50 (for opening relative volume)
    daily: pd.DataFrame   # prior daily OHLCV rows (strictly before date)

    @property
    def b5(self) -> pd.DataFrame:
        return resample(self.bars, "5min")


@lru_cache(maxsize=400)
def _hist(cache: str, symbol: str):
    df = BarStore(cache).load(symbol)
    if df.empty:
        return None
    days = {d: g for d, g in df.groupby(df.index.date)}
    daily = pd.DataFrame({d: {"open": g["open"].iloc[0], "high": g["high"].max(), "low": g["low"].min(),
                              "close": g["close"].iloc[-1], "volume": g["volume"].sum(),
                              "ov": g.loc[g.index.time < t("09:50"), "volume"].sum()} for d, g in days.items()}).T
    daily = daily.astype(float)
    tr = pd.concat([daily.high - daily.low, (daily.high - daily.close.shift()).abs(),
                    (daily.low - daily.close.shift()).abs()], axis=1).max(axis=1)
    daily["atr"] = tr.rolling(14, min_periods=10).mean().shift(1)
    daily["adv"] = (daily.close * daily.volume).rolling(20, min_periods=10).mean().shift(1)
    daily["advs"] = daily.volume.rolling(14, min_periods=10).mean().shift(1)
    daily["ovavg"] = daily.ov.rolling(14, min_periods=10).mean().shift(1)
    daily["pc"] = daily.close.shift(1)
    return days, daily


def symbols(cache: str = "data/cache") -> list[str]:
    return BarStore(cache).symbols()


def day(symbol: str, d, cache: str = "data/cache") -> Day | None:
    h = _hist(cache, symbol)
    if h is None:
        return None
    days, daily = h
    d = pd.Timestamp(d).date()
    if d not in days or d not in daily.index:
        return None
    r = daily.loc[d]
    if not np.isfinite(r.atr) or not np.isfinite(r.adv):
        return None
    return Day(symbol, d, days[d], float(r.pc), float(r.atr), float(r.adv), float(r.advs), float(r.ovavg),
               daily.loc[daily.index < d, ["open", "high", "low", "close", "volume"]])


def sessions(split: str) -> list[Date]:
    lo, hi, cache = _split(split)
    h = _hist(cache, "SPY")
    return [d for d in h[0] if str(lo) <= str(d) <= str(hi)]


def _split(split: str):
    if split in LOCKED and not os.environ.get("MCF_RBT_ALLOW_HOLDOUT"):
        raise PermissionError(f"the {split} split is locked until the lead scores finalists once")
    return SPLITS[split]


def sim(sig: Signal, d: Day):
    return simulate(sig, d.bars, FLAT, COSTS_EXT if d.adv < MIN_ADV else COSTS)


def run(signals_fn, variant: dict, split: str, universe: list[str] | None = None, min_price: float = 5.0,
        min_adv: float | None = None) -> dict:
    """Run signals_fn(day, variant) over every symbol-session of the split; one position per symbol at a time
    (a new signal on the same symbol is skipped while a trade is open). Returns metrics + the trade rows."""
    lo, hi, cache = _split(split)
    syms = universe or symbols(cache)
    dates = sessions(split)
    rows = []
    for s in syms:
        for d in dates:
            dd = day(s, d, cache)
            if dd is None or dd.prev_close < min_price or (min_adv and dd.adv < min_adv):
                continue
            busy_until = None
            for sig in signals_fn(dd, variant) or []:
                if busy_until is not None and dd.bars.index[sig.bar_index] < busy_until:
                    continue
                tr = sim(sig, dd)
                if tr is None:
                    continue
                busy_until = tr.exit_time
                rows.append({"date": str(d), "symbol": s, "side": sig.side, "r": tr.r_multiple, "reason": tr.exit_reason,
                             "entry_time": tr.entry_time, "minutes": (tr.exit_time - tr.entry_time).total_seconds() / 60,
                             "extended": dd.adv < MIN_ADV})
    return metrics(pd.DataFrame(rows))


def metrics(df: pd.DataFrame) -> dict:
    if df is None or not len(df):
        return {"n": 0}
    r = df["r"].to_numpy(float)
    daily = df.groupby("date")["r"].agg(["sum", "size"])
    nd = len(daily)
    # day-clustered SE of the mean R: trades on the same day are correlated
    dm = (daily["sum"] - daily["size"] * r.mean()).to_numpy()
    se_cl = float(np.sqrt((dm ** 2).sum()) / len(r)) if nd > 1 else float("nan")
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    return {"n": int(len(r)), "days": nd, "win_rate": round(float((r > 0).mean()), 4), "exp_r": round(float(r.mean()), 4),
            "se_day_clustered": round(se_cl, 4), "t_day_clustered": round(float(r.mean() / se_cl), 2) if se_cl > 0 else None,
            "pf": round(float(gw / gl), 3) if gl > 0 else None, "green_days": round(float((daily["sum"] > 0).mean()), 3),
            "exp_r_ex_best_day": round(float((daily["sum"].sum() - daily["sum"].max()) / max(1, len(r) - daily.loc[daily["sum"].idxmax(), "size"])), 4),
            "best_day_share": round(float(daily["sum"].max() / daily["sum"].sum()), 3) if daily["sum"].sum() > 0 else None,
            "long_n": int((df.side > 0).sum()), "short_n": int((df.side < 0).sum()),
            "avg_minutes": round(float(df["minutes"].mean()), 1), "exit_reasons": df["reason"].value_counts().to_dict(),
            "_rows": df}


def random_baseline(df: pd.DataFrame, split: str, stop_atr: float, target_atr: float | None, seed: int = 0,
                    reps: int = 3) -> dict:
    """Same side, same days, same entry minutes, random symbols from the split's universe; stop/target as
    fractions of daily ATR. Compare a candidate's exp_r against this, not against zero."""
    lo, hi, cache = _split(split)
    rng = np.random.default_rng(seed)
    syms = symbols(cache)
    rows = []
    for _ in range(reps):
        for x in df.itertuples():
            for _try in range(5):
                dd = day(syms[rng.integers(len(syms))], x.date, cache)
                if dd is None or dd.prev_close < 5:
                    continue
                et = pd.Timestamp(x.entry_time).tz_convert(dd.bars.index.tz)
                k = dd.bars.index.searchsorted(et) - 1
                if k < 0 or k >= len(dd.bars) - 1:
                    continue
                px = float(dd.bars["close"].iloc[k])
                sig = Signal(dd.symbol, "random", int(x.side), k, px - x.side * stop_atr * dd.atr,
                             None if target_atr is None else px + x.side * target_atr * dd.atr)
                tr = sim(sig, dd)
                if tr is not None:
                    rows.append({"date": x.date, "side": x.side, "r": tr.r_multiple, "reason": tr.exit_reason,
                                 "minutes": (tr.exit_time - tr.entry_time).total_seconds() / 60})
                break
    m = metrics(pd.DataFrame(rows))
    m.pop("_rows", None)
    return m
