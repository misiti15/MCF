"""pod-williams-oops-etf-red-day-long - Larry Williams 'Oops': gap below the prior-day low after a red day, buy the
PDL reclaim (index / sector ETFs, LONG).

Source: Larry Williams 'Oops!' pattern (Long-Term Secrets to Short-Term Trading); TradingView 'Larry Williams Oops
Strategy' script (open below the prior low after a bearish candle, buy stop just above the prior low, trail the day's
low, flat at end of day).
URL: https://www.tradingview.com/script/7Gqs0Sqn-Larry-Williams-Oops-Strategy

VARIANT of the CWT14 failed-PDL-break long (single stocks, intraday undercut) and raschke-80-20. Stated changes: an
OPENING GAP below PDL after a red D-1 candle, ETFs only, Williams' exit (no target, stop trails the session low).

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLV, XLI, XLY, XLP, XLU, SMH, XBI, KRE.
  1. D-1 was a red candle: D-1 close < D-1 open (lib.daily(), completed day).
  2. Today's open < PDL - 0.05 x atr_d (opening gap below the prior-day low).
  3. The gap (prior close - open) is not over 1.5 x atr_d (news-shock filter).
  4. The FIRST 5-minute close of the session (from the 09:35 bar on, full-session bars) above PDL + 0.02 x atr_d,
     with that bar closing 09:35-12:00. Entry: that bar's close.
  Stop (GEOM S): session LOD (as of the entry bar) - 0.05 x atr_d. No target; flat 15:55.
Harness limits (declared, not tweaks): the frames start at the 09:50 bar, so a first reclaim at 09:35-09:45 cannot be
entered and is skipped (no later re-trigger, because it is no longer the first close above). The scorer cannot trail a
stop; the scorer number is the fixed-initial-stop version. The source's trail (raise the stop to the low of the last 6
completed 5-min bars, never lower) is re-simulated post hoc by the r2_5 run from the scorer's trades and reported
alongside. No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1200)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "SMH", "XBI", "KRE"]
TRAIL_BARS = 6
LAYERS = ["D-1 close < D-1 open", "open < PDL - 0.05 ATR", "prior close - open <= 1.5 ATR",
          "first close of the session > PDL + 0.02 ATR, 09:35-12:00", "stop LOD - 0.05 ATR, no target, flat 15:55"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r25_util as U  # noqa: E402

_ST = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    _ST[id(df)] = (stop,)
    if not n:
        return z
    b = U.base(df)
    k = U.key(df)
    d = U.map_daily(df, k, ["o1", "c1"])
    atr = b["atr"]
    trig = b["pdl"] + 0.02 * atr
    with np.errstate(invalid="ignore"):
        day_ok = (d["c1"] < d["o1"])                                   # (1)
        day_ok &= b["opn"] < b["pdl"] - 0.05 * atr                     # (2)
        day_ok &= (b["pc"] - b["opn"]) <= 1.5 * atr                    # (3)
    # (4) first full-session close above the trigger
    fb = U.full_bars(df, symbols=sorted(set(df["symbol"].astype(str))))
    if fb is None:
        return z
    st = U.start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].to_numpy()[st],
                      "trig": trig[st], "ok": day_ok[st]})
    u = u[u["ok"] & np.isfinite(u["trig"])]
    if not len(u):
        return z
    j = fb.merge(u[["symbol", "date", "trig"]], on=["symbol", "date"], how="inner")
    j = j[(j["tod"] >= 935) & (j["c"] > j["trig"])]
    first = j.groupby(["symbol", "date"], sort=False)["tod"].min().rename("ftod").reset_index()
    kk = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    ftod = kk.merge(first, on=["symbol", "date"], how="left")["ftod"].to_numpy(float)
    tod = b["tod"]
    with np.errstate(invalid="ignore"):
        m = day_ok & (tod == ftod) & (tod >= 950) & (tod <= 1200)
        stop[:] = b["lod"] - 0.05 * atr
        m &= stop < b["c"]
    _ST[id(df)] = (stop,)
    return np.asarray(m, bool)
