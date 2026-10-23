"""pod-redler-821-trend-weak-hour-dip-long - 8/21-EMA momentum-trend gate: buy the 10-11 'weak hour' dip on the index
(LONG).

Source: Scott Redler (T3 Live) on the 8/21-day EMA 'momentum trend' (The Compound and Friends podcast; Tradingsim
SimCast ep. 2); Market Chameleon SPY best / worst hour of trading (10:00-11:00 ET the weakest hour).
URL: https://podscripts.co/podcasts/the-compound-and-friends/what-long-term-investors-can-learn-from-traders-with-josh-and-scott-redler

VARIANT of ix-oe (SPY move-from-open dip-buy at time T) and pod-bbt-10am-reversal-spy-turn-long. Stated change: a
daily momentum-trend gate, the dip measured strictly over the 10:00-11:00 hour (not from the open), and an
opening-range-low hold.

Rules (plain English, LONG), SYMBOLS SPY, QQQ. Conditions 1-3 on SPY, 4 on the traded symbol:
  1. Daily gate (as of D-1's close, completed days): SPY close > EMA8 > EMA21, and both EMAs rising over 3 days
     (EMA8(D-1) > EMA8(D-4), EMA21(D-1) > EMA21(D-4)).
  2. SPY 10:00-11:00 return (close of the 10:55-11:00 bar / close of the 09:55-10:00 bar - 1) <= -0.20%.
  3. SPY has not traded below its 09:30-10:00 opening-range low by 11:00 (running low on the 11:00 bar >= that low)
     and its 11:00 close is >= the prior close - 0.30%.
  4. Bar close 11:05-12:00 ET: a 5m close above the prior 5m bar's high, and that close is above the symbol's 11:00
     close or above its session VWAP.
  Entry: that close (SPY / QQQ). Stop (GEOM S): the lowest low of the symbol's bars from 10:00 up to the entry bar
  - 0.05%. Harness deviation (no lookahead): the source's '10:00-11:30 low' is not known at an entry before 11:30, so
  the running low up to the entry bar is used. Exit 15:55; no target (afternoon drift).
Controls named by the source idea (no daily gate; gate + random 11:00-12:00 entry) are not separate modules here; the
scorer's same-time random-entry control covers the second. No tweak made.
Score (r3_12, open history): 0 trades - a 10:00-11:00 SPY drop of >= 0.20% almost always undercuts the 09:30-10:00
low, so conditions 2 and 3 did not co-occur on a gated day in the open history. Costs per config/default.yaml.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

import _r212_util as U
import _cwt3_bars as CB

SIDE = "long"
GEOM = "S"
WINDOW = (1105, 1200)
SYMBOLS = ["SPY", "QQQ"]
LAYERS = ["SPY close > EMA8 > EMA21 (D-1), both rising 3d", "SPY 10:00-11:00 return <= -0.20%",
          "SPY held the 09:30-10:00 low by 11:00 and >= prior close - 0.30%",
          "close > prior bar high and > 11:00 close or VWAP, 11:05-12:00", "stop 10:00..entry low - 0.05%, flat 15:55"]
_ST = {}
_DC = {}


def _ema_table():
    if "e" in _DC:
        return _DC["e"]
    d = CB.lib().daily()[["symbol", "date", "close"]].copy()
    d = d[d["symbol"].astype(str) == "SPY"].copy()
    d["date"] = d["date"].astype(str)
    d = d.sort_values("date").reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((dt - dt.shift()).dt.days > 7).cumsum()
    c = d["close"]
    e8 = c.groupby(g).transform(lambda s: s.ewm(span=8, adjust=False, min_periods=8).mean())
    e21 = c.groupby(g).transform(lambda s: s.ewm(span=21, adjust=False, min_periods=21).mean())
    sh = lambda s, n: s.groupby(g).shift(n)
    ok = (sh(c, 1) > sh(e8, 1)) & (sh(e8, 1) > sh(e21, 1)) & (sh(e8, 1) > sh(e8, 4)) & (sh(e21, 1) > sh(e21, 4))
    _DC["e"] = dict(zip(d["date"], ok.to_numpy(bool)))
    return _DC["e"]


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c = b["tod"], b["c"]
    ds = U.dstr(df)
    sym = df["symbol"].astype(str).to_numpy()
    gate = _ema_table()
    g1 = np.array([bool(gate.get(d, False)) for d in ds]) if n else np.zeros(0, bool)
    c10 = U.at_tod(c, k, tod, 1000)
    c11 = U.at_tod(c, k, tod, 1100)
    lod11 = U.at_tod(b["lod"], k, tod, 1100)
    drl = U.drive(df)["dr_l"]
    with np.errstate(invalid="ignore", divide="ignore"):
        ok = (c11 / c10 - 1 <= -0.002) & (lod11 >= drl - 1e-9 * c11) & (c11 >= b["pc"] * 0.997)
    s11 = (sym == "SPY") & (tod == 1100)
    spy_ok = dict(zip(ds[s11], ok[s11]))
    g23 = np.array([bool(spy_ok.get(d, False)) for d in ds]) if n else np.zeros(0, bool)
    # running low of bars closing 10:05 .. this bar (the 10:00-onward low)
    lw = np.where(tod >= 1005, b["l"], np.inf)
    rl = pd.Series(lw).groupby(k).cummin().to_numpy()
    with np.errstate(invalid="ignore"):
        m = g1 & g23 & (tod >= 1105) & (tod <= 1200)
        m &= c > U.lag(b["h"], k, 1)
        m &= (c > c11) | (c > b["vwap"])
        sp = rl * (1 - 0.0005)
        m &= np.isfinite(sp) & (sp < c)
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
