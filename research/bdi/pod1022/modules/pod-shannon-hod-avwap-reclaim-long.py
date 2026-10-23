"""pod-shannon-hod-avwap-reclaim-long - Reclaim of the VWAP anchored at today's high after a morning sell-off (LONG).

Source: Brian Shannon (Chat With Traders ep 029; Alpha Trends 'How To Use The Anchored VWAP'; Benzinga 'My favorite
ways to use the Anchored VWAP'); TradingView 'Anchored VWAP Auto High Low'. MERGED from pod-cwt-shannon-hod-avwap-reclaim
and pod-shannon-hod-avwap-reclaim-long.
URL: https://www.benzinga.com/general/education/22/05/27200039/my-favorite-ways-to-use-the-anchored-vwap-brian-shannon

VARIANT of AVR (bdi-vid AVWAP first retest; anchors open / pdhv / pdh / pdl / tdhv, failed), r02 VWAP reclaim (failed)
and CWT11. Stated changes: a new anchor (today's HOD bar, set after 09:50 so the anchor is inside the frame), the
trigger is a reclaim from BELOW after a higher low, target a round trip to the HOD.

Rules (plain English):
  AVWAP_H: VWAP anchored at the bar that set the current high of day; that bar must close after 09:50 (frame bar
  09:50-09:55 or later). The frame has no raw volume, so bar volumes are recovered (up to one scale factor per
  symbol-day) from successive session-VWAP values: v_t / cumV_t = (VWAP_t - VWAP_{t-1}) / (tp_t - VWAP_{t-1}),
  tp = (high + low + close) / 3, VWAP = close / (1 + vwapDistPct/100). When that ratio is not in (0, 1) the bar's
  volume is scaled from the last valid bar by volumeRatio. A new high of day moves the anchor and resets everything.
  1. Sell-off: a bar closing 09:50-11:30 whose low is >= 0.8 x daily ATR below the HOD (pre-declared 0.8, the middle of
     the source's 0.6-1.0 range).
  2. Higher low: after the sell-off and after the latest low-of-day bar, a swing low (low <= the prior bar's low,
     confirmed by the next bar's higher low - so it is known only one bar later) at least 0.3 x daily ATR above the
     low of day. A new low of day cancels it.
  3. 11:00-14:30: the first 5-minute close that crosses above AVWAP_H (previous close at or below it), with close >=
     session VWAP - 0.1 x daily ATR and volumeRatio >= 1.2.
  4. spy_fo > -0.3% at the trigger.
  The optional daily SMA50 gate is not used. Entry at the trigger close, one per symbol-day.
  Stop (GEOM S): the higher low - 0.05 x daily ATR. Target: the HOD at entry. Flat 15:55. Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
CONTEXT = ["spy_fo"]
SELL_ATR = 0.8
LAYERS = ["AVWAP anchored at the in-frame HOD bar (volumes recovered from session VWAP)",
          "09:50-11:30 sell-off >= 0.8 ATR from the HOD", "higher low >= 0.3 ATR above the LOD",
          "11:00-14:30 first close crossing above AVWAP_H, close >= VWAP - 0.1 ATR, volumeRatio >= 1.2",
          "spy_fo > -0.3%", "stop higher low - 0.05 ATR, target HOD, flat 15:55"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, lod, vw, vr, spy, atr, sell, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        cum = 1.0
        lastv = np.nan
        lastvr = np.nan
        a = -1
        spv = 0.0
        sv = 0.0
        av_prev = np.nan
        sold = False
        jl = -1
        hl = np.nan
        rh = h[i0]
        for i in range(i0, i1):
            # recovered relative bar volume
            v = np.nan
            if i > i0:
                tp = (h[i] + l[i] + c[i]) / 3.0
                den = tp - vw[i - 1]
                w = (vw[i] - vw[i - 1]) / den if den != 0.0 else np.nan
                if w > 0.0 and w < 1.0:
                    nc = cum / (1.0 - w)
                    v = nc - cum
                    cum = nc
                elif lastv == lastv and lastvr > 0 and vr[i] > 0:
                    v = lastv * vr[i] / lastvr
                    cum = cum + v
                if v == v:
                    lastv = v
                    lastvr = vr[i]
            rh = max(rh, h[i])
            H = max(hod[i], rh)
            tp = (h[i] + l[i] + c[i]) / 3.0
            if h[i] >= H - 1e-9 * c[i]:
                # new high of day: new anchor (valid only inside the frame, after the first bar)
                a = i if (i > i0 and v == v) else -1
                spv = tp * v if a >= 0 else 0.0
                sv = v if a >= 0 else 0.0
                av_prev = tp if a >= 0 else np.nan
                sold = False
                jl = -1
                hl = np.nan
                continue
            if a < 0:
                continue
            if v == v:
                spv += tp * v
                sv += v
            av = spv / sv if sv > 0 else np.nan
            L = lod[i]
            if not sold and tod[i] <= 1130 and H - l[i] >= sell * atr[i]:
                sold = True
            if sold:
                if jl < 0 or l[i] <= L + 1e-9 * c[i]:
                    if l[i] <= L + 1e-9 * c[i]:
                        jl = i
                        hl = np.nan
                    elif jl < 0:
                        jl = i
                else:
                    mm = i - 1
                    if mm > jl and mm - 1 >= i0 and l[mm] <= l[mm - 1] and l[i] > l[mm] and l[mm] >= L + 0.3 * atr[i]:
                        hl = l[mm]
                if hl == hl and tod[i] >= w0 and tod[i] <= w1 and av == av and av_prev == av_prev:
                    if c[i] > av and c[i - 1] <= av_prev and c[i] >= vw[i] - 0.1 * atr[i] and vr[i] >= 1.2 \
                            and spy[i] > -0.3:
                        m[i] = True
                        stop[i] = hl - 0.05 * atr[i]
                        tgt[i] = H
            av_prev = av
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + f("dist_hod_atr") * atr
        lod = c - f("dist_lod_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, hod, lod, vw, f("volumeRatio"), f("spy_fo"), atr,
                   SELL_ATR, WINDOW[0], WINDOW[1])


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
