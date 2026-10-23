"""pod-gao-newsday-first30-hold-long - Macro-news-day first-half-hour momentum, held from 10:00 to the close (LONG).

Source: Gao, Han, Li and Zhou (2018 JFE), 'Market Intraday Momentum', summarised by Alpha Architect (the
first-half-hour return predicts the rest of the day; the effect is stronger on macro news release days and on
high-volume days).
URL: https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/

VARIANT of 'Intraday momentum' (backlog: Gao first half hour -> last half hour, all days). Stated change: macro
release days only (CPI / NFP / PPI at 08:30 ET, hardcoded calendar in _r212_util; FOMC is a 14:00 release and does not
inform the first half hour, so it is not in the gate), long only, entry at 10:00 instead of 15:30, held through the
afternoon with a structural stop.

Rules (plain English, LONG), SYMBOLS SPY, QQQ:
  1. Today is a CPI, NFP or PPI release day.
  2. SPY's return from the prior close to the close of the 09:55-10:00 bar is >= +0.30%.
  3. The symbol's 09:30-10:00 cumulative volume is >= 1.2x its 20-session same-window average (rvc at 10:00).
  4. At the 10:00 bar close, price is above the session VWAP and above the midpoint of the 09:30-10:00 range.
  Entry: that close (10:00). Stop: the 09:30-10:00 low, moved further down if needed so that the risk is at least
  0.3 x daily ATR14. Exits (GEOM S+ts2 with BE_AT_R = 1 and the bailout disabled, BAILOUT_BARS = 999): stop moves to
  break-even once the trade is +1R; otherwise flat at the 15:55 bar close.
Control (stated in the source idea): the same rule on non-release days, module pod-gao-newsday-first30-hold-long-ctrl-
nonrelease. Harness notes: the 2026 PPI dates after February are omitted rather than guessed (see _r212_util). Low
frequency (~3 releases a month x 2 symbols x the momentum gate). No tweak made. Costs per config/default.yaml (entry
before 10:30 carries the x1.4 cost multiplier). Educational only - not financial advice."""
import numpy as np

import _r212_util as U

SIDE = "long"
GEOM = "S+ts2"
BAILOUT_BARS = 999
BE_AT_R = 1.0
WINDOW = (1000, 1000)
SYMBOLS = ["SPY", "QQQ"]
RELEASE_DAYS = True
LAYERS = ["CPI/NFP/PPI release day", "SPY prior close -> 10:00 >= +0.30%", "09:30-10:00 rvol >= 1.2",
          "10:00 close > VWAP and > 09:30-10:00 midpoint", "stop 09:30-10:00 low (>= 0.3 ATR), BE at +1R, flat 15:55"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c = b["tod"], b["c"]
    ds = U.dstr(df)
    rel = np.isin(ds, U.RELEASE)
    day_ok = rel if RELEASE_DAYS else ~rel
    sym = df["symbol"].astype(str).to_numpy()
    spy10 = (sym == "SPY") & (tod == 1000)
    ret = {d: r for d, r in zip(ds[spy10], (c / b["pc"] - 1)[spy10] * 100)}
    sret = np.array([ret.get(d, np.nan) for d in ds]) if n else np.zeros(0)
    dr = U.drive(df)
    rv = U.rvc(df)
    mid = (dr["dr_h"] + dr["dr_l"]) / 2
    with np.errstate(invalid="ignore"):
        m = day_ok & (tod == 1000)                                       # (1)
        m &= sret >= 0.30                                                # (2)
        m &= rv >= 1.2                                                   # (3)
        m &= (c > b["vwap"]) & (c > mid)                                 # (4)
        sp = np.minimum(dr["dr_l"], c - 0.3 * b["atr"])
        m &= sp < c
    return np.asarray(m, bool), sp


def mask(df) -> np.ndarray:
    try:
        m, sp = _compute(df)
    except (KeyError, FileNotFoundError):
        m, sp = np.zeros(len(df), bool), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = sp
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
