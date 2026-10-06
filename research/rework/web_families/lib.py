"""Shared runner for the web_families rework (rule 18). Educational only - not financial advice.

- imports the locked-data guard first (safe.py): no cache_q2, no rows >= 2026-09-16, no unlock env vars
- reuses research/reddit_bt/common.py fills/costs/metrics (production costs, stop-first, flat 15:55)
- adds daily ATR(10)/ATR(20) next to ATR(14) so the "swap indicator lengths across all setups" check can switch
  every family's ATR at once (ATR_COL)
- run_multi: one pass over symbol-sessions, many variants, one position per symbol at a time per variant
- baseline: same side, same session, same entry minute, random symbol from the same universe, same stop/target
  distance in daily-ATR units and the same trade management (isolates the selection edge)
"""
from __future__ import annotations

import gc
from functools import lru_cache

import numpy as np
import pandas as pd

from research.rework.web_families import safe  # noqa: F401  (must come first)
from research.reddit_bt import common as C
from mcf.data.store import BarStore
from mcf.strategies.base import Signal, t

ATR_COL = "atr"   # "atr" = ATR14 (production), "atr10", "atr20"


@lru_cache(maxsize=420)
def _hist(cache: str, symbol: str):
    assert "cache_q2" not in cache
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
    daily["atr10"] = tr.rolling(10, min_periods=8).mean().shift(1)
    daily["atr20"] = tr.rolling(20, min_periods=14).mean().shift(1)
    daily["adv"] = (daily.close * daily.volume).rolling(20, min_periods=10).mean().shift(1)
    daily["advs"] = daily.volume.rolling(14, min_periods=10).mean().shift(1)
    daily["ovavg"] = daily.ov.rolling(14, min_periods=10).mean().shift(1)
    daily["pc"] = daily.close.shift(1)
    return days, daily


def _day(symbol, d, cache="data/cache"):
    h = _hist(cache, symbol)
    if h is None:
        return None
    days, daily = h
    d = pd.Timestamp(d).date()
    if d not in days or d not in daily.index:
        return None
    r = daily.loc[d]
    a = r[ATR_COL]
    if not np.isfinite(a) or not np.isfinite(r.adv) or not np.isfinite(r.atr):
        return None
    return C.Day(symbol, d, days[d], float(r.pc), float(a), float(r.adv), float(r.advs), float(r.ovavg),
                 daily.loc[daily.index < d, ["open", "high", "low", "close", "volume"]])


C._hist = _hist      # common.day / sessions / run now use the guarded loader
C.day = _day

ROOT_U = [s for s in open(__file__.rsplit("/", 4)[0] + "/research/reddit_bt/top300.txt").read().split() if s]
SPLITS = ("train", "valid")


def clear():
    _hist.cache_clear()
    gc.collect()


def row(sig: Signal, tr, dd) -> dict:
    ref = sig.entry_price if sig.entry_type == "stop" else float(dd.bars["close"].iloc[sig.bar_index])
    return {"date": str(dd.date), "symbol": dd.symbol, "side": sig.side, "r": tr.r_multiple, "reason": tr.exit_reason,
            "entry_time": tr.entry_time, "minutes": (tr.exit_time - tr.entry_time).total_seconds() / 60,
            "extended": dd.adv < C.MIN_ADV, "stop_atr": abs(ref - sig.stop) / dd.atr,
            "tgt_atr": None if sig.target is None else abs(sig.target - ref) / dd.atr,
            "exit_by": sig.exit_by, "be": sig.be_at_r, "trail": sig.trail_r, "trail_after": sig.trail_after_r,
            "ts": sig.time_stop_min, "ts_r": sig.time_stop_min_r}


def run_multi(signals_fn, variants: dict, split: str, universe, min_price: float = 5.0) -> dict:
    lo, hi, cache = C._split(split)
    dates = C.sessions(split)
    rows = {k: [] for k in variants}
    for s in universe:
        for d in dates:
            dd = C.day(s, d, cache)
            if dd is None or dd.prev_close < min_price:
                continue
            for name, v in variants.items():
                busy = None
                for sig in signals_fn(dd, v) or []:
                    if busy is not None and dd.bars.index[sig.bar_index] < busy:
                        continue
                    tr = C.sim(sig, dd)
                    if tr is None:
                        continue
                    busy = tr.exit_time
                    rows[name].append(row(sig, tr, dd))
    return {k: C.metrics(pd.DataFrame(r)) for k, r in rows.items()}


def baseline(df: pd.DataFrame, split: str, universe, seed: int = 0, reps: int = 5) -> dict:
    if df is None or not len(df):
        return {"n": 0}
    lo, hi, cache = C._split(split)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(reps):
        for x in df.itertuples():
            for _try in range(8):
                dd = C.day(universe[rng.integers(len(universe))], x.date, cache)
                if dd is None or dd.prev_close < 5 or dd.symbol == x.symbol:
                    continue
                et = pd.Timestamp(x.entry_time).tz_convert(dd.bars.index.tz)
                k = dd.bars.index.searchsorted(et) - 1
                if k < 0 or k >= len(dd.bars) - 1:
                    continue
                px = float(dd.bars["close"].iloc[k])
                tgt = None if x.tgt_atr is None or not np.isfinite(x.tgt_atr) else px + x.side * x.tgt_atr * dd.atr
                sig = Signal(dd.symbol, "random", int(x.side), int(k), px - x.side * x.stop_atr * dd.atr, tgt)
                sig.exit_by = x.exit_by if isinstance(x.exit_by, type(t("10:00"))) else None
                sig.be_at_r = x.be if x.be is not None and np.isfinite(x.be) else None
                if x.trail is not None and np.isfinite(x.trail):
                    sig.trail_r, sig.trail_after_r = x.trail, x.trail_after
                if x.ts is not None and np.isfinite(x.ts):
                    sig.time_stop_min, sig.time_stop_min_r = int(x.ts), x.ts_r
                tr = C.sim(sig, dd)
                if tr is not None:
                    out.append({"date": x.date, "side": x.side, "r": tr.r_multiple, "reason": tr.exit_reason,
                                "minutes": (tr.exit_time - tr.entry_time).total_seconds() / 60})
                break
    m = C.metrics(pd.DataFrame(out))
    m.pop("_rows", None)
    return m


def strip(m: dict) -> dict:
    return {k: v for k, v in m.items() if k != "_rows"}


def gate(tr: dict, va: dict, plateau_mean: float | None, base: dict | None) -> dict:
    g = {"train_pos": tr.get("exp_r", -1) > 0, "valid_pos": va.get("exp_r", -1) > 0, "valid_n30": va.get("n", 0) >= 30,
         "valid_t15": (va.get("t_day_clustered") or -9) >= 1.5,
         "plateau": plateau_mean is not None and plateau_mean > 0,
         "beats_baseline": base is not None and base.get("n", 0) > 0 and va.get("exp_r", -1) > base.get("exp_r", 9)}
    g["pass"] = all(g.values())
    return g
