"""pod-cwt2-berry-quiet-staircase-grind-long - Quiet-midday steady grinder: join a time-sliced buyer's staircase
(LONG).

Source: Chat With Traders ep 326, Jason Berry; record ep326 'Ride a detectable recurring algorithmic order
(time-sliced buyer)'.
URL: https://chatwithtraders.com

NEW (no backlog match for a TWAP/algorithmic staircase). Different from pod-shannon-midday-vwap-base-quiet-long (a
flat base) and pod-tosind-lunch-compression-index-break (an index range break). Bar proxy for a time-sliced buyer
(the source reads 10-30 s child orders, which the 5-minute frame cannot see; stated proxy).

Rules (plain English), bars up to the decision bar i only:
  1. Index quiet: |spy_fo| <= 0.4 and SPY's last 6 bars (i-5..i) range (max high - min low) <= 0.25 x SPY atr_d.
  2. Staircase: each of the last 6 bars (i-5..i) has low >= the previous bar's low and close >= the previous close -
     0.02 x atr_d, and the stock gained 0.3-0.8 x atr_d over them (close_i - close_{i-6}).
  3. Small, even bars: each of the 6 bars has range <= 1.0 x the 5-minute ATR (atrPct% x close of that bar), and
     volumeRatio stays within 0.6-1.6 on all 6 (steady participation, no spike).
  4. buyPressure >= 0.3 and close > the session VWAP.
  Entry: that close, bar close 11:30-14:30. Stop (GEOM S): the low of bar i-2 - 0.05 x atr_d (a broken staircase =
  the program stopped). Target: none, flat 15:55. Scorer limit (stated): the source's holdtr-style 1R trail cannot be
  combined with a structural stop in this harness (GEOM S has no trail), so the trade holds to 15:55 unless stopped.
  Information line: the hit rate by time of day comes from the trades parquet (tod column).
  Costs in (scorer). No tweak used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1130, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["|spy_fo| <= 0.4, SPY 6-bar range <= 0.25 SPY ATR",
          "6 bars: higher-or-equal lows, closes >= prev - 0.02 ATR, gain 0.3-0.8 ATR",
          "each bar range <= 5m ATR, volumeRatio 0.6-1.6", "buyPressure >= 0.3, close > VWAP",
          "11:30-14:30 ET", "stop low of bar i-2 - 0.05 ATR, hold to 15:55"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, atr, atr5, vr, bp, vd, spy, sq, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 6, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            if not (abs(spy[i]) <= 0.4 and sq[i]):
                continue
            a = atr[i]
            if not (a > 0 and bp[i] >= 0.3 and vd[i] > 0):
                continue
            g = c[i] - c[i - 6]
            if not (g >= 0.3 * a and g <= 0.8 * a):
                continue
            ok = True
            for k in range(i - 5, i + 1):
                if not (l[k] >= l[k - 1] and c[k] >= c[k - 1] - 0.02 * a and (h[k] - l[k]) <= atr5[k]
                        and vr[k] >= 0.6 and vr[k] <= 1.6):
                    ok = False
                    break
            if not ok:
                continue
            sp = l[i - 2] - 0.05 * a
            if sp < c[i]:
                m[i] = True
                stop[i] = sp
    return m, stop


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c = f("close")
    sym = df["symbol"].astype(str).to_numpy()
    spy = df.loc[sym == "SPY", ["date", "tod", "high", "low", "atr_d"]].copy()
    if not len(spy):
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    spy = spy.sort_values(["date", "tod"])
    g = spy.groupby("date", sort=False)
    hh = g["high"].transform(lambda x: x.rolling(6).max())
    ll = g["low"].transform(lambda x: x.rolling(6).min())
    spy["sq"] = ((hh - ll) <= 0.25 * spy["atr_d"]).astype(float)
    key = pd.DataFrame({"date": df["date"].to_numpy(), "tod": df["tod"].to_numpy()})
    sq = key.merge(spy[["date", "tod", "sq"]], on=["date", "tod"], how="left")["sq"].to_numpy(float) == 1
    with np.errstate(invalid="ignore"):
        atr5 = f("atrPct") * c / 100
    b, e = _segments(df)
    m, stop = _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), f("atr_d"), atr5, f("volumeRatio"),
                      f("buyPressure"), f("vwapDistPct"), f("spy_fo"), sq, WINDOW[0], WINDOW[1])
    return m, stop, np.full(n, np.nan)


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
