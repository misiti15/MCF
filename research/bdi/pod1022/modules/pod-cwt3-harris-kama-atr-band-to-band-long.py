"""pod-cwt3-harris-kama-atr-band-to-band-long - Adaptive-MA ATR band, band-to-band reversal long (Sunny Bands proxy).

Source: Chat With Traders EP250, Sunny Harris (methodical day trader; Sunny Bands band-to-band)
[~00:21:30-00:39:00].
URL: https://chatwithtraders.com/250

VARIANT of pod-cwt3-chan-bb-volfloor-quiet-etf-long (same mean-reversion family). Stated changes: the centre is a
speed-adaptive MA (KAMA 10/2/30) instead of SMA20, the band is ATR-based not std-based, entry needs a down-to-up candle
turn, and the target is the OPPOSITE band (not the mean). Sunny Bands themselves are proprietary; KAMA + 2 x ATR is the
stated proxy.

Rules (plain English, LONG, 5-minute bars). SYMBOLS = SPY, QQQ, IWM, DIA + a fixed list of 30 liquid large caps
(_cwt3_bars.LARGE30; fixed list, not re-ranked in hindsight per day).
  KAMA(10, 2, 30) on continuous full-session 5m closes (09:35-15:55, across days, previous open month as warm-up).
  ATR14(5m) = the frame's atrPct x close. Lower band = KAMA - 2 x ATR14(5m), upper = KAMA + 2 x ATR14(5m).
  (a) bar close 10:00-15:00 ET;
  (b) band width (upper - lower) / close >= 0.6% for the ETFs, >= 1.0% for stocks (band must cover costs);
  (c) previous bar red (close < open, raw 5m open from frames_tf) and its low <= its lower band;
  (d) current bar green (close > open) and closes above the previous bar's high (down-to-up turn).
  Entry: the signal bar's close (the scorer's entry; proxy for the next bar open). Stop (GEOM S): the low of the two-bar
  turn - 0.25 x ATR14(5m) (the guest uses stop-and-reverse; long only here). Target: the upper band at entry, full size
  (the 50% scale-out at KAMA cannot be modelled by the scorer). Flat 15:55. Skip if the target is < 3 x the round-trip
  cost (config/default.yaml).
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1500)
_ETF4 = ["SPY", "QQQ", "IWM", "DIA"]
_L30 = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX", "JPM", "V", "MA", "COST",
        "LLY", "UNH", "WMT", "XOM", "ORCL", "CRM", "MU", "INTC", "PLTR", "TSM", "BAC", "GS", "CAT", "CVX", "JNJ", "AMAT"]
SYMBOLS = _ETF4 + _L30
CONTEXT = []
LAYERS = ["10:00-15:00 ET", "KAMA(10,2,30) +/- 2 ATR14(5m) band width >= 0.6% ETF / 1.0% stock",
          "previous bar red with low <= lower band", "current bar green, close > previous high",
          "stop turn low - 0.25 ATR5, target upper band >= 3x RT cost"]

_ST = {}


def _u():
    n = "_cwt3_bars"
    if n not in sys.modules:
        sp = importlib.util.spec_from_file_location(n, Path(__file__).resolve().parent / "_cwt3_bars.py")
        m = importlib.util.module_from_spec(sp)
        sys.modules[n] = m
        sp.loader.exec_module(m)
    return sys.modules[n]


def _kama(c, n=10, fast=2, slow=30):
    out = np.full(len(c), np.nan)
    if len(c) <= n:
        return out
    fs, ss = 2.0 / (fast + 1), 2.0 / (slow + 1)
    ad = np.abs(np.diff(c))
    k = c[n - 1]
    for t in range(n, len(c)):
        vol = ad[t - n:t].sum()
        er = abs(c[t] - c[t - n]) / vol if vol > 0 else 0.0
        sc = (er * (fs - ss) + ss) ** 2
        k = k + sc * (c[t] - k)
        if t >= 3 * n:                         # short warm-up so the seed value does not dominate
            out[t] = k
    return out


def _compute(df):
    U = _u()
    n = len(df)
    z0 = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n:
        return z0
    p = U.full_bars(df, SYMBOLS)
    if p is None or not len(p):
        return z0
    sy = p["symbol"].to_numpy()
    c_all = p["c"].to_numpy(float)
    ka = np.full(len(p), np.nan)
    b0 = np.flatnonzero(np.r_[True, sy[1:] != sy[:-1]])
    b1 = np.r_[b0[1:], len(p)]
    for a, z in zip(b0, b1):
        ka[a:z] = _kama(c_all[a:z])
    p["kama"] = ka
    kama = U.map_rows(df, p, ["kama"])["kama"]
    t5 = U.tf5(df, SYMBOLS)
    if t5 is None:
        return z0
    op = U.map_rows(df, t5, ["open"])["open"]
    b = U.base(df)
    k = U.key(df)
    c, h, l, tod, a5 = b["c"], b["h"], b["l"], b["tod"], b["atr5"]
    etf = np.isin(df["symbol"].astype(str).to_numpy(), _ETF4)
    with np.errstate(invalid="ignore", divide="ignore"):
        lo = kama - 2 * a5
        up = kama + 2 * a5
        m = (tod >= WINDOW[0]) & (tod <= WINDOW[1])                                   # (a)
        m &= (up - lo) / c * 100 >= np.where(etf, 0.6, 1.0)                           # (b)
        c1, o1, l1, h1, lo1 = (U.lag(x, k) for x in (c, op, l, h, lo))
        m &= (c1 < o1) & (l1 <= lo1)                                                  # (c)
        m &= (c > op) & (c > h1)                                                      # (d)
        stop = np.fmin(l, l1) - 0.25 * a5
        tgt = up
        m &= (tgt - c) >= 3 * U.rt_cost(c, tod)
        m &= np.isfinite(stop) & np.isfinite(tgt) & (stop < c) & (tgt > c)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        n = len(df)
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


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
