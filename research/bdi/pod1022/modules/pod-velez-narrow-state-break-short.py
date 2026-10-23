"""pod-velez-narrow-state-break-short - Velez narrow state: SMA20 and SMA50 pinched with price on them, then an
expansion bar (SHORT).

Source: Oliver Velez 'Narrow State' concept (Pristine-style teaching; podcast / YouTube guest appearances);
TradingView 'MA Narrow State Scanner'.
URL: https://www.tradingview.com/script/5wikBNTa-MA-Narrow-State-Scanner

VARIANT of CWT12 coil breakout (failed), t3-rvol-cons (retired) and the Bollinger squeeze rework idea. Stated
change: compression is measured by moving-average convergence (SMA20 ~ SMA50 with price hugging both), not by bar
range or band width. Velez uses SMA20 / SMA200; SMA50 is the longest frame column. Side: SHORT (this file; the exact mirror of pod-velez-narrow-state-break-long); the LONG
is pod-velez-narrow-state-break-long.

Values: SMA20 = close / (1 + sma20_dist_pct%), SMA50 = close / (1 + sma50_dist_pct%) (5m, span previous days);
5m ATR = atrPct% x close.
Rules (plain English; long shown, short = exact mirror):
  1. Narrow state: |sma20_dist_pct - sma50_dist_pct| <= 0.10 on each of the 6 bars before this bar (same day).
  2. Price on the averages: |sma20_dist_pct| <= 0.25 on those 6 bars.
  3. Expansion bar: close > max(SMA20, SMA50) + 0.5 x 5m ATR, volumeRatio >= 1.5.
  4. SMA20 slope turns up: sma20_slope_pct > 0 now and <= 0 on at least one of the 6 narrow-state bars.
  Entry: that close, bar close 10:30-14:30. Stop (GEOM S): min(SMA20, SMA50) - 0.05 x atr_d. No target: held to
  15:55 (flat). Costs per config/default.yaml (scorer).
Pre-declared choices: 'slope turns > 0' is read as > 0 now after a non-positive reading inside the narrow state.
Deviation, declared: the source's holdtr (1R trail) is not available with a structural stop, so the trade holds to
15:55 with the structural stop. No tweak used. No tuning on valid.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = []
LAYERS = ["|sma20_dist - sma50_dist| <= 0.10 on the prior 6 bars", "|sma20_dist| <= 0.25 on the prior 6 bars",
          "close beyond max/min(SMA20, SMA50) +- 0.5 x 5m ATR, volumeRatio >= 1.5", "SMA20 slope turns",
          "stop other side of the averages - 0.05 ATR, hold to 15:55", "10:30-14:30 ET"]

N = 6

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def mask(df) -> np.ndarray:
    _ST.clear()
    if not len(df):
        return np.zeros(len(df), dtype=bool)
    sg = 1.0 if SIDE == "long" else -1.0
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    d20, d50, sl = _f(df, "sma20_dist_pct"), _f(df, "sma50_dist_pct"), _f(df, "sma20_slope_pct")
    with np.errstate(invalid="ignore", divide="ignore"):
        s20, s50 = c / (1 + d20 / 100), c / (1 + d50 / 100)
        narrow = (np.abs(d20 - d50) <= 0.10) & (np.abs(d20) <= 0.25)
        m = np.ones(len(df), bool)
        flat = np.zeros(len(df), bool)
        for j in range(1, N + 1):
            m &= _lag(narrow, k, j) == 1
            flat |= sg * _lag(sl, k, j) <= 0
        m &= flat & (sg * sl > 0) & (_f(df, "volumeRatio") >= 1.5)
        a5 = _f(df, "atrPct") / 100 * c
        if SIDE == "long":
            m &= c > np.maximum(s20, s50) + 0.5 * a5
            stop = np.minimum(s20, s50) - 0.05 * atr
        else:
            m &= c < np.minimum(s20, s50) - 0.5 * a5
            stop = np.maximum(s20, s50) + 0.05 * atr
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop,)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")
