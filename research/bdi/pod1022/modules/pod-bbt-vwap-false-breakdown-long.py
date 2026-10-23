"""pod-bbt-vwap-false-breakdown-long - Low-volume, shallow VWAP breakdown reclaimed within 2 bars (LONG).

Source: Bear Bull Traders forum 'Questions about the VWAP false breakout, double bottom' + BBT webinar 'How to Trade
Using the VWAP'.
URL: https://forums.bearbulltraders.com/topic/1920-questions-about-the-vwap-false-breakout-double-bottom-etc/

VARIANT of SWP Conti VWAP sweep + reclaim (bdi-vid-sweep-delta, failed: same pierce-and-reclaim shape, delta confirm,
no volume rule) and R02 VWAP reclaim (failed, >= 3 bars below). Opposite side of NS3. Stated change: the breakdown
bar must be LOW volume (volumeRatio < 1.0) and shallow, inside an established above-VWAP trend, and the trigger must
clear the breakdown bar's high.

EMA9: the continuous 5-minute EMA9 behind the frame's emaDiff, recovered exactly (EMA9 = EMA21 x (1 + emaDiff/100),
seeds solved from the day's first two rows; same method as pod-bbt-parabolic-ema9-snapback-short). SPY VWAP: SPY's
own frame row at the same (date, tod) (its vwapDistPct); the frame holds SPY. No SPY row -> no trade.

Rules (plain English), decision bar i:
  1. Trend: >= 8 of the previous 10 closes (i-10..i-1) above the session VWAP, and EMA9_i > VWAP_i.
  2. Breakdown bar k = the latest of i-1, i-2 that closed below VWAP, with volumeRatio_k < 1.0 and low_k >= VWAP_k
     - 0.25 x daily ATR (shallow).
  3. Trigger: close_i > VWAP_i and close_i > high_k.
  4. SPY close above SPY's session VWAP; fromOpen_i > 0.
  Entry: close_i, bar close 10:00-14:30. Stop (GEOM S): low_k - 0.03 x daily ATR. Target: high of day if it is >= 1R
  above the entry, else entry + 1R. Flat 15:55. Costs in (scorer). No tweak used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = []
LAYERS = [">= 8 of the previous 10 closes above VWAP, EMA9 > VWAP",
          "breakdown bar in the last 2: close < VWAP, volumeRatio < 1.0, low within 0.25 ATR of VWAP",
          "close > VWAP and > breakdown-bar high", "SPY above its VWAP, fromOpen > 0",
          "stop breakdown low - 0.03 ATR, target HOD if >= 1R else 1R", "10:00-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _ema9(b, e, c, ed):
    out = np.full(len(c), np.nan)
    a9, a21 = 0.2, 2.0 / 22.0
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if i1 - i0 < 2:
            continue
        d0, d1 = ed[i0] / 100.0, ed[i0 + 1] / 100.0
        den = (1 - a9) * (1 + d0) - (1 - a21) * (1 + d1)
        if den == 0.0 or d0 != d0 or d1 != d1:
            continue
        E = (a21 * c[i0 + 1] * (1 + d1) - a9 * c[i0 + 1]) / den
        e9 = (1 + d0) * E
        for i in range(i0 + 1, i1):
            e9 = a9 * c[i] + (1 - a9) * e9
            out[i] = e9
    return out


def _spy_cols(df, cols):
    """SPY's own row values at the same (date, tod), aligned to df (NaN where SPY is absent)."""
    key = pd.DataFrame({"date": df["date"].to_numpy(), "tod": df["tod"].to_numpy()})
    sp = df.loc[df["symbol"].astype(str) == "SPY", ["date", "tod"] + cols].drop_duplicates(["date", "tod"])
    sp = sp.rename(columns={c: "spy_" + c for c in cols})
    j = key.merge(sp, on=["date", "tod"], how="left")
    return {c: j["spy_" + c].to_numpy(float) for c in cols}


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, vw, e9, vr, fo, spyvd, hod, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 10, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and fo[i] > 0 and spyvd[i] > 0 and c[i] > vw[i] and e9[i] > vw[i]):
                continue
            above = 0
            for k in range(i - 10, i):
                if c[k] > vw[k]:
                    above += 1
            if above < 8:
                continue
            k = -1
            if c[i - 1] < vw[i - 1]:
                k = i - 1
            elif c[i - 2] < vw[i - 2]:
                k = i - 2
            if k < 0:
                continue
            if not (vr[k] < 1.0 and l[k] >= vw[k] - 0.25 * a and c[i] > h[k]):
                continue
            sp = l[k] - 0.03 * a
            r = c[i] - sp
            if not (r > 0):
                continue
            t = hod[i] if hod[i] - c[i] >= r else c[i] + r
            m[i] = True
            stop[i] = sp
            tgt[i] = t
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
        hod = c + f("dist_hod_atr") * atr
    spy = _spy_cols(df, ["vwapDistPct"])
    b, e = _segments(df)
    e9 = _ema9(b, e, c, f("emaDiff"))
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), vw, e9, f("volumeRatio"),
                   f("fromOpen"), spy["vwapDistPct"], hod, atr, WINDOW[0], WINDOW[1])


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
