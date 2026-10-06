"""t7_noise_band — noise-area intraday momentum on SPY / QQQ (falsification test of a published result).

Source: Zarattini, Aziz & Barbon (2024), "Beat the Market: An Effective Intraday Momentum Strategy for the
S&P500 ETF (SPY)". Mechanised faithfully where the engine allows; a hypothesis on our data, not evidence.

Rules:
  sigma(t) = mean over the N prior sessions of |close(t) / open(session) - 1| at the same minute t
  upper(t) = max(open, prev_close) x (1 + sigma(t)), lower(t) = min(open, prev_close) x (1 - sigma(t))
  Checks at HH:00 and HH:30 from 10:00 to 15:30 (60-min variant: HH:00 from 10:00 to 15:00). "close(t)" at check
  time HH:MM is the close of the 1-min bar starting HH:MM-1 (bars are labelled by start time), which is the
  signal bar_index; entry at the next bar open (HH:MM). Same minute used for sigma on prior sessions.
  Long if close > upper; short if close < lower. Stop = the farther-in (closer to price) of the band and session
  VWAP at entry: long max(upper, VWAP), short min(lower, VWAP); skipped if that is on the wrong side of price.
  Risk floor: stop distance at least 0.05 x daily ATR (keeps R-multiples finite when price is just past the band;
  deviation from the paper, applied to every variant). No target; flat 15:55. Re-entries at later checks are
  allowed after an exit (the harness skips a signal while a trade is open, so an immediate reversal at the very
  check where a trade exits is not taken — a small deviation).
  Trailing stop: the paper re-evaluates the band/VWAP stop at every check. Two approximations:
    exit "check": the engine holds the entry-time stop intrabar, and the trade is also closed at the open after
      the first later check whose close is beyond the then-current band/VWAP stop (exit_by). Live-implementable:
      the exit decision at each check uses bars up to that check only (the signal function precomputes it).
    exit "trail": entry-time stop, then the engine's R-trail (trail 1R behind the best price once +1R).
    exit "faithful" (added after the first train pass showed the intrabar band stop is hit within minutes on most
      trades, which the paper never does): the band/VWAP stop is evaluated ONLY at checks (exit at the next open,
      as in "check"), with an intrabar disaster stop at 0.5 x daily ATR from the signal close; that distance is
      also the R unit, so R-multiples are returns in units of 0.5 daily ATR. Closest to the paper.
  Prior sessions come from the same bar cache as the day (data/cache; data/cache_q2 only for dates not in it).

Grid (pre-declared, full factorial = 24): check interval {30, 60} min x lookback N {10, 14, 20} x symbol {SPY, QQQ}
x exit {check, trail, faithful} (faithful added after the first train-only pass; 36 total). Educational only — not financial advice.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from mcf import features as F
from mcf.strategies.base import Signal

NAME = "t7_noise_band"
UNIVERSE = ["SPY", "QQQ"]


def _prior_days(day, n: int):
    from research.reddit_bt import common as C
    for cache in ("data/cache", "data/cache_q2"):     # q2 cache is only reached for dates absent from data/cache
        h = C._hist(cache, day.symbol)
        if h is None or day.date not in h[0]:
            continue
        prior = sorted(d for d in h[0] if d < day.date)[-n:]
        return [h[0][d] for d in prior] if len(prior) == n else None
    return None


def _move_at(g, minute: int) -> float:
    mins = g.index.hour * 60 + g.index.minute
    sel = np.nonzero(mins == minute - 1)[0]
    if not len(sel):
        return np.nan
    return abs(float(g["close"].iloc[sel[0]]) / float(g["open"].iloc[0]) - 1)


def signals(day, variant: dict) -> list[Signal]:
    if day.symbol != variant["symbol"]:
        return []
    b = day.bars
    if len(b) < 300:
        return []
    prior = _prior_days(day, variant["lookback"])
    if prior is None:
        return []
    mins = b.index.hour.to_numpy() * 60 + b.index.minute.to_numpy()
    c = b["close"].to_numpy(float)
    vw = F.vwap(b).to_numpy(float)
    op = float(b["open"].iloc[0])
    hi_ref, lo_ref = max(op, day.prev_close), min(op, day.prev_close)
    step = variant["interval"]
    checks = list(range(600, 930 + 1, step)) if step == 30 else list(range(600, 900 + 1, 60))
    lv = {}                                    # check minute -> (bar k, close, upper, lower, vwap)
    for m in checks:
        sel = np.nonzero(mins == m - 1)[0]
        if not len(sel):
            continue
        sig_m = np.nanmean([_move_at(g, m) for g in prior])
        if not np.isfinite(sig_m):
            continue
        k = int(sel[0])
        lv[m] = (k, c[k], hi_ref * (1 + sig_m), lo_ref * (1 - sig_m), vw[k])
    out = []
    floor = 0.05 * day.atr
    for m, (k, px, up, lo, v) in lv.items():
        side = 1 if px > up else -1 if px < lo else 0
        if side == 0 or k + 1 >= len(b):
            continue
        stop = max(up, v) if side > 0 else min(lo, v)
        if side * (px - stop) <= 0:
            continue
        if side * (px - stop) < floor:
            stop = px - side * floor
        if variant["exit"] == "faithful":           # no intrabar band stop: disaster stop only, R = 0.5 ATR
            stop = px - side * 0.5 * day.atr
        sig = Signal(day.symbol, NAME, side, k, stop, None)
        if variant["exit"] in ("check", "faithful"):
            for m2, (k2, px2, up2, lo2, v2) in lv.items():
                if m2 <= m:
                    continue
                st2 = max(up2, v2) if side > 0 else min(lo2, v2)
                if side * (px2 - st2) <= 0:
                    sig.exit_by = b.index[k2 + 1].time() if k2 + 1 < len(b) else None
                    break
        else:
            sig.trail_r, sig.trail_after_r = 1.0, 1.0
        out.append(sig)
    return out


VARIANTS = {}
for iv, lb, sym, ex in product((30, 60), (10, 14, 20), ("SPY", "QQQ"), ("check", "trail", "faithful")):
    VARIANTS[f"{sym}_i{iv}_n{lb}_{ex}"] = {"interval": iv, "lookback": lb, "symbol": sym, "exit": ex}

FINALISTS: list[str] = []
BASELINE = {"stop_atr": 0.15, "target_atr": None}
