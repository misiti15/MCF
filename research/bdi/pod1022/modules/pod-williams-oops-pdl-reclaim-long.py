"""pod-williams-oops-pdl-reclaim-long - Larry Williams 'Oops': gap below the prior-day low, buy the reclaim of the
prior-day low (index ETFs + core-tier stocks, LONG).

Source: Unger Academy, 'We Tested Larry Williams' Oops Pattern'; LuxAlgo, Classic Bar Setups (Oops = gap-failure
trade).
URL: https://ungeracademy.com/?p=7737

VARIANT of the gap-fill family (Reddit R05 gap fill), pod-smb-gapdown-opening-print-reclaim-long and
pod-williams-oops-etf-red-day-long. Stated change: the trigger level is the prior-day LOW (PDL), the open must be
>= 0.25 ATR below PDL, the daily trend filter (close > SMA50) replaces the red-candle filter, stocks are included,
and the target is the prior close (full gap fill) or 2R.

Universe: the scorer's core universe (adv20 >= $20M, includes SPY / QQQ / IWM / DIA), with the earnings blackout
(4 trading days either side of a report) already removed by the scorer.
Rules (plain English, LONG):
  1. Open <= PDL - 0.25 x ATR14 (atr_d, daily ATR as of the prior close).
  2. Yesterday's daily close > daily SMA50 (lib.daily(), completed days).
  3. Gap (prior close - open) <= 1.5 x ATR14 (no news collapse).
  4. Entry on the FIRST 5-min bar closing 09:35-11:30 ET whose close is above PDL (full-session bars); one trade per
     symbol-day. Entry: that bar's close.
  Stop (GEOM S): session low (as of the entry bar) - 0.05 x ATR14, with the stop distance floored at 0.3 x ATR14.
  Target: the prior close, or entry + 2R if that is nearer. Flat 15:55.
Harness limit (declared, not a tweak): frames start at the 09:50 bar, so when the first close above PDL is at
09:35-09:45 the day is skipped (no later re-trigger, as it is no longer the first reclaim).
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1130)
LAYERS = ["open <= PDL - 0.25 ATR", "D-1 close > SMA50", "prior close - open <= 1.5 ATR",
          "first full-session close > PDL, 09:35-11:30 (09:50+ tradable)",
          "stop min(LOD - 0.05 ATR, entry - 0.3 ATR), target min(prior close, 2R)"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt3_bars as CB  # noqa: E402

_ST = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n:
        return z
    b = CB.base(df)
    k = CB.key(df)
    atr, c = b["atr"], b["c"]
    d = CB.map_daily(df, k, ["d_close_1", "sma50_1"])
    with np.errstate(invalid="ignore"):
        day_ok = b["opn"] <= b["pdl"] - 0.25 * atr                     # (1)
        day_ok &= d["d_close_1"] > d["sma50_1"]                        # (2)
        day_ok &= (b["pc"] - b["opn"]) <= 1.5 * atr                    # (3)
    st = CB.start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].to_numpy()[st],
                      "trig": b["pdl"][st], "ok": day_ok[st]})
    u = u[u["ok"] & np.isfinite(u["trig"])]
    if not len(u):
        return z
    fb = CB.full_bars(df, symbols=sorted(set(u["symbol"])))
    if fb is None:
        return z
    j = fb.merge(u[["symbol", "date", "trig"]], on=["symbol", "date"], how="inner")
    j = j[(j["tod"] >= 935) & (j["c"] > j["trig"])]
    first = j.groupby(["symbol", "date"], sort=False)["tod"].min().rename("ftod").reset_index()
    kk = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    ftod = kk.merge(first, on=["symbol", "date"], how="left")["ftod"].to_numpy(float)
    tod = b["tod"]
    with np.errstate(invalid="ignore"):
        m = day_ok & (tod == ftod) & (tod >= 950) & (tod <= 1130)    # (4)
        stop[:] = np.minimum(b["lod"] - 0.05 * atr, c - 0.3 * atr)
        r = c - stop
        tgt[:] = np.minimum(b["pc"], c + 2 * r)
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
