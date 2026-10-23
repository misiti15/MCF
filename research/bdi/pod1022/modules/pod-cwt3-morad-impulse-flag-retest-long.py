"""pod-cwt3-morad-impulse-flag-retest-long - Impulse bar, shallow flag, continuation to retest the impulse high (LONG).

Source: Chat With Traders EP082, FuturesTrader71 / Morad (impulse then continuation, retest of the impulse extreme)
[~00:36:53].
URL: https://chatwithtraders.com/082

New trigger family (bar-anatomy impulse, not a level break).

Rules (plain English, LONG, 5-minute bars). SYMBOLS = SPY, QQQ + a fixed list of 30 liquid large caps
(_cwt3_bars.LARGE30). Raw 5m volume from frames_tf/5min; bar ranges from continuous full-session 5m bars.
  (a) Impulse bar I (bar close 09:55-14:25 ET, i.e. not in the first 20 minutes): range >= 2.0 x the average range of
      the 20 bars before it, volume >= 2.0 x its 20-bar average (volumeRatio), close in the top 25% of its range,
      close > session VWAP.
  (b) Flag: the next 1-6 bars retrace 30-70% of I's range (lowest flag low between I.high - 0.30 x range and
      I.high - 0.70 x range), no flag bar closes below I's low, and the flag bars' average volume < I's volume.
  (c) Continuation bar: the first bar after the flag that closes above the previous bar's high, with volume above the
      flag's average but below I's volume.
  Entry: the continuation bar's close, bar close 10:00-14:30. Stop (GEOM S): the flag low - 0.05%. Target: I's high
  (the modest target, as stated). Skip if the distance to I's high is < 1R or < 3 x the round-trip cost
  (config/default.yaml). Flat 15:55: the 60-minute time stop and the optional 50% runner cannot be modelled by the
  scorer (hold-to-target-or-stop instead). The win rate approximates the touch rate of I's high (guest: ~78%).
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
_L30 = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "NFLX", "JPM", "V", "MA", "COST",
        "LLY", "UNH", "WMT", "XOM", "ORCL", "CRM", "MU", "INTC", "PLTR", "TSM", "BAC", "GS", "CAT", "CVX", "JNJ", "AMAT"]
SYMBOLS = ["SPY", "QQQ"] + _L30
CONTEXT = []
LAYERS = ["impulse: range >= 2x avg20, volumeRatio >= 2, close top 25%, above VWAP, 09:55-14:25",
          "flag 1-6 bars: 30-70% retrace, no close below I low, lower volume",
          "continuation: close > prior high, flag vol < vol < I vol",
          "stop flag low - 0.05%, target I high (>= 1R and >= 3x RT cost)"]

_ST = {}


def _u():
    n = "_cwt3_bars"
    if n not in sys.modules:
        sp = importlib.util.spec_from_file_location(n, Path(__file__).resolve().parent / "_cwt3_bars.py")
        m = importlib.util.module_from_spec(sp)
        sys.modules[n] = m
        sp.loader.exec_module(m)
    return sys.modules[n]


def _compute(df):
    U = _u()
    n = len(df)
    m = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    if not n:
        return m, stop, tgt
    p = U.full_bars(df, SYMBOLS)
    t5 = U.tf5(df, SYMBOLS)
    if p is None or t5 is None:
        return m, stop, tgt
    p["rg"] = p["h"] - p["l"]
    p["ar20"] = p.groupby("symbol", sort=False)["rg"].transform(lambda x: x.shift(1).rolling(20, min_periods=20).mean())
    ar20 = U.map_rows(df, p, ["ar20"])["ar20"]
    vol = U.map_rows(df, t5, ["volume"])["volume"]
    b = U.base(df)
    k = U.key(df)
    c, h, l, tod = b["c"], b["h"], b["l"], b["tod"]
    rg = h - l
    vr = U.f(df, "volumeRatio")
    vd = U.f(df, "vwapDistPct")
    rtc = U.rt_cost(c, tod)
    with np.errstate(invalid="ignore", divide="ignore"):
        imp = (rg >= 2.0 * ar20) & (vr >= 2.0) & (c - l >= 0.75 * rg) & (vd > 0) & (rg > 0)
        imp &= (tod >= 955) & (tod <= 1425) & np.isfinite(vol)
    for t in np.flatnonzero(imp):
        hI, lI, rI, vI = h[t], l[t], rg[t], vol[t]
        fl_low, fl_vsum, nf = np.inf, 0.0, 0
        for j in range(t + 1, min(t + 8, n)):
            if k[j] != k[t]:
                break
            if nf >= 1:
                fav = fl_vsum / nf
                retr = (hI - fl_low) / rI
                if (0.30 <= retr <= 0.70 and fav < vI and c[j] > h[j - 1] and fav < vol[j] < vI
                        and WINDOW[0] <= tod[j] <= WINDOW[1]):
                    sp = fl_low * (1 - 0.0005)
                    R = c[j] - sp
                    if R > 0 and (hI - c[j]) >= R and (hI - c[j]) >= 3 * rtc[j] and not m[j]:
                        m[j], stop[j], tgt[j] = True, sp, hI
                    break
            if nf >= 6:
                break
            if c[j] < lI or not np.isfinite(vol[j]):           # flag bar closed below I's low: no setup
                break
            fl_low = min(fl_low, l[j])
            fl_vsum += vol[j]
            nf += 1
            if (hI - fl_low) / rI > 0.70:                       # retraced too deep
                break
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
