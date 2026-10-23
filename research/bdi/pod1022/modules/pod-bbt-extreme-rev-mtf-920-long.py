"""pod-bbt-extreme-rev-mtf-920-long - Stretched-below-VWAP reversal: EMA9 crosses EMA20 after an extended decline,
target VWAP (LONG). Config 920 (moderate stretch + fromOpen <= -1.5%; no reward/risk floor).

Source: Bear Bull Traders - Andrew Aziz 'Reversals' webinar (June 2023 deck: extreme reversals with multi-timeframe
confirmation; 9/20 reversal trades) + BBT article 'How to Trade Extreme Reversals and VWAP Reversals'. MERGED from
pod-bbt-extreme-rev-mtf-long and pod-bbt-920-countertrend-long.
URL: https://bearbulltraders.com/wp-content/uploads/2023/06/Reversal-Andrew-June-22-2023.pdf

VARIANT of CWT05 flush V (no climax / ATR-drop requirement here), heat_fade_long, R10 EMA cross (plain cross, failed),
ST4-emadn-long and wi-ema-cross (idea). Stated changes: only the EMA9-over-EMA20 up-cross that ENDS an extended
decline, while price is still well below VWAP, with oversold confirmation and a VWAP target.

Rules (plain English), every value from bars up to and including the decision bar i:
  1. The 5-minute EMA9 was below the EMA20 for >= 8 consecutive bars (counted inside the 09:50+ frame), then crossed
     above it on bar i or one of the 2 bars before. The frame's `emaDiff` = (EMA9 - EMA21) / EMA21 (continuous EMAs
     over many sessions) is used: EMA21 stands in for EMA20 (one bar of span; stated approximation).
  2. Config X: close_i <= session VWAP - 1.0 x daily ATR. (Config 920, separate file: VWAP - close_i >= 0.3 x daily
     ATR and fromOpen <= -1.5%.)
  3. The low of day was set inside the frame within the last 12 bars; the minimum RSI(14) over bars i-5..i is <= 30
     and RSI is rising (rsi_i > rsi_{i-1}).
  4. close_i > max(high of bars i-3..i-1) (a new 15-minute high) and close_i > close_{i-1} (green vs prior close).
  Entry: close_i, 10:15-14:30 bar close. Stop (GEOM S): low of day - 0.05 x daily ATR. Target: session VWAP at entry;
  config X requires (target - entry) >= 2 x (entry - stop). Flat 15:55. Costs in (scorer).
  No tweak used (all thresholds as written in the idea).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1430)
CONFIG = "920"
CONTEXT = []
LAYERS = ["EMA9 < EMA21 >= 8 bars then cross up within the last 3 bars", "config 920: VWAP - close >= 0.3 ATR and fromOpen <= -1.5%",
          "LOD within 12 bars; min RSI(14) last 6 bars <= 30 and rising", "close > 3-bar high and > prior close",
          "stop LOD - 0.05 ATR, target VWAP, RR >= 2 (X)", "10:15-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, lod, vw, ed, rsi, fo, atr, cfg, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        neg = 0            # consecutive bars with EMA9 < EMA21 before the latest cross
        lastx = -100       # bar of the latest qualifying up-cross
        jl = -100          # bar where the current low of day was set (inside the frame)
        for i in range(i0, i1):
            if i > i0:
                if l[i] <= lod[i] + 1e-9 * c[i] and lod[i] < lod[i - 1] - 1e-9 * c[i]:
                    jl = i
                if ed[i] > 0 and ed[i - 1] <= 0:
                    if neg >= 8:
                        lastx = i
                    neg = 0
                elif ed[i] < 0:
                    neg += 1
                else:
                    neg = 0
            else:
                neg = 1 if ed[i] < 0 else 0
                if l[i] <= lod[i] + 1e-9 * c[i]:
                    jl = i
            if tod[i] < w0 or tod[i] > w1 or i - i0 < 6:
                continue
            if i - lastx > 2 or ed[i] <= 0:
                continue
            a = atr[i]
            if cfg == 0:
                if not (c[i] <= vw[i] - 1.0 * a):
                    continue
            else:
                if not (vw[i] - c[i] >= 0.3 * a and fo[i] <= -1.5):
                    continue
            if i - jl > 12 or jl < i0:
                continue
            mr = 1e9
            for k in range(i - 5, i + 1):
                mr = min(mr, rsi[k])
            if not (mr <= 30 and rsi[i] > rsi[i - 1]):
                continue
            hh = max(h[i - 1], max(h[i - 2], h[i - 3]))
            if not (c[i] > hh and c[i] > c[i - 1]):
                continue
            sp = lod[i] - 0.05 * a
            tp = vw[i]
            if not (sp < c[i] and tp > c[i]):
                continue
            if cfg == 0 and (tp - c[i]) < 2.0 * (c[i] - sp):
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = tp
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - f("dist_lod_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, lod, vw, f("emaDiff"), f("rsi"), f("fromOpen"), atr,
                   0 if CONFIG == "X" else 1, WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
