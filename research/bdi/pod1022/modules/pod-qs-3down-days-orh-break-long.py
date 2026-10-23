"""pod-qs-3down-days-orh-break-long - Three down days, then buy the break of the 30-min opening-range high (LONG).

Source: Quantified Strategies, '3 Days Down Overnight Trading Strategy' (SPY down three closes in a row has a
short-term mean-reversion edge).
URL: https://quantifiedstrategies.substack.com/p/3-days-down-overnight-trading-strategy-1db

NEW intraday translation (the daily '3 down' rule was never tested intraday here; it differs from
pod-qs-30m-lower-lows-etf-long, which counts 30-min bars inside the day).

Rules (plain English, LONG), SYMBOLS SPY, QQQ, IWM:
  1. The symbol closed lower three sessions in a row (close D-1 < D-2 < D-3 < D-4, close to close).
  2. D-1 close > daily SMA200.
  3. Today's open >= prior close - 0.5 x daily ATR14 (no crash gap).
  4. Between 10:00 and 13:00 ET (bar closes 10:05..13:00), a 5-min bar closes above the 09:30-10:00 high while the
     close is above the session VWAP. Entry: that close (the first such bar).
  Stop (GEOM S): the 09:30-10:00 low, or entry - 0.6 x ATR14 if that is nearer (the higher of the two).
  Target: entry + 2R, or the open of the third down day (D-1's open) when that is above the entry and nearer
  (pre-declared reading of the source's '2R, or the third down day's open': the first of the two to be reached).
  Flat at 15:55.
Control (stated in the source idea): the same trigger without the 3-down condition,
pod-qs-3down-days-orh-break-long-ctrl-no3down. Harness note: the open daily history restarts on 2025-03-03 (the
locked block is never bridged), so SMA200 uses min 100 sessions and the gate is live from about late July 2025. No
tweak made. Costs per config/default.yaml. Educational only - not financial advice."""
import numpy as np

import _r212_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1300)
SYMBOLS = ["SPY", "QQQ", "IWM"]
USE_3DOWN = True
LAYERS = ["3 lower daily closes", "D-1 close > SMA200", "open >= prior close - 0.5 ATR",
          "10:05-13:00 close > 09:30-10:00 high and > VWAP", "stop max(OR low, entry - 0.6 ATR), target min(2R, D-1 open)"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c = b["tod"], b["c"]
    dx = U.map_dx(df, k, ["c1", "c2", "c3", "c4", "o1", "sma200_1"])
    dr = U.drive(df)
    with np.errstate(invalid="ignore"):
        m = np.ones(n, bool)
        if USE_3DOWN:
            m &= (dx["c1"] < dx["c2"]) & (dx["c2"] < dx["c3"]) & (dx["c3"] < dx["c4"])    # (1)
        m &= dx["c1"] > dx["sma200_1"]                                                     # (2)
        m &= b["opn"] >= b["pc"] - 0.5 * b["atr"]                                          # (3)
        m &= (tod >= 1005) & (tod <= 1300) & (c > dr["dr_h"]) & (c > b["vwap"])           # (4)
        sp = np.maximum(dr["dr_l"], c - 0.6 * b["atr"])
        m &= sp < c
        t2 = c + 2 * (c - sp)
        o1 = dx["o1"]
        tg = np.where((o1 > c) & (o1 < t2), o1, t2)
    return np.asarray(m, bool), sp, tg


def mask(df) -> np.ndarray:
    try:
        m, sp, tg = _compute(df)
    except (KeyError, FileNotFoundError):
        m, sp, tg = np.zeros(len(df), bool), np.full(len(df), np.nan), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = (sp, tg)
    return m


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
