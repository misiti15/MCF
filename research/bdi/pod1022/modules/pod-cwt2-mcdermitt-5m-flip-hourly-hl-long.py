"""pod-cwt2-mcdermitt-5m-flip-hourly-hl-long - 5-minute trend flip marks the hourly higher low (LONG).

Source: Chat With Traders ep 267, Dan McDermitt; record ep267 '5-minute trend flip marks the hourly higher low'.
URL: https://chatwithtraders.com

VARIANT of CWT11 VWAP trend pullback (cwt-b-b7 variants failed: VWAP- or oscillator-based pullbacks) and
pod-brooks-h2-second-entry (bar-count H2). Stated change: the trigger is structural on two timeframes (an hourly
HH/HL uptrend plus a 5-min swing-structure flip), with no VWAP-distance or oscillator trigger.

Rules (plain English):
  1. Hourly uptrend: the last two COMPLETED clock-hour bars (closes 10:30, 11:30, ... ; when only today's 10:30 bar
     is complete, it is paired with yesterday's last complete clock-hour bar in the frame, 13:30-14:30) make a higher
     high and a higher low, and the latest hourly close is above the session VWAP at the decision bar.
  2. Hourly pause: no new high of day for >= 8 five-minute bars (40 min) and the close is still above the low of the
     latest completed hourly bar.
  3. Inside the pause the 5-min chart made a lower high LH (a confirmed swing high after the HOD bar and below the HOD)
     and then a swing low HL that is higher than the previous 5-min swing low. Swing pivots: a bar whose high (low) is
     above (below) both neighbours, confirmed when the next bar closes (one bar later; no lookahead).
  4. Trigger: the first 5-min close above LH after HL is confirmed.
  5. breadth >= 0.45.
  Entry: that close, bar close 10:45-14:30. Stop (GEOM S): HL - 0.05 x atr_d. Target: the high of day at entry
  (the prior hourly high); flat 15:55. First signal per symbol-day.
Pre-declared choices: one-bar-each-side swing pivots; yesterday's last complete clock hour is 13:30-14:30 because the
history frames end at the 15:00 bar. No tweak used. No tuning on the valid period. Costs per config/default.yaml.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1045, 1430)
CONTEXT = ["breadth"]
LAYERS = ["hourly HH+HL over the last two completed clock hours, last hourly close > VWAP",
          "no new HOD for >= 8 bars, close above the last hourly low",
          "5-min LH below HOD then a higher swing low HL", "close above LH", "breadth >= 0.45",
          "stop HL - 0.05 ATR, target HOD", "10:45-14:30 ET"]

import numba
import numpy as np
import pandas as pd

_ST = {}
NB = 7


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def hourly(k, tod, h, l, c, hod, lod):
    mins = (tod // 100) * 60 + tod % 100
    b = np.where(mins <= 630, 0, np.ceil((mins - 630) / 60.0)).astype(np.int64)
    endm = 630 + 60 * b
    nk = int(k.max()) + 1
    HH = np.full((nk, NB), np.nan)
    HL = np.full((nk, NB), np.nan)
    HC = np.full((nk, NB), np.nan)
    ok = b < NB
    g = pd.DataFrame({"k": k[ok], "b": b[ok], "h": h[ok], "l": l[ok]})
    agg = g.groupby(["k", "b"], sort=False).agg(h=("h", "max"), l=("l", "min"))
    kk = agg.index.get_level_values(0).to_numpy()
    bb = agg.index.get_level_values(1).to_numpy()
    HH[kk, bb] = agg["h"].to_numpy()
    HL[kk, bb] = agg["l"].to_numpy()
    endbar = ok & (mins == endm)
    HC[k[endbar], b[endbar]] = c[endbar]
    e0 = tod == 1030
    HH[k[e0], 0] = hod[e0]
    HL[k[e0], 0] = lod[e0]
    inc = np.isnan(HC)
    HH[inc] = np.nan
    HL[inc] = np.nan
    return b, mins == endm, HH, HL, HC


@numba.njit(cache=False)
def _kern(starts, ends, h, l, c, hod):
    n = len(c)
    sig = np.zeros(n, np.bool_)
    hlv = np.full(n, np.nan)
    since = np.zeros(n, np.int64)
    hm = np.full(n, np.nan)
    for s in range(len(starts)):
        b, e = starts[s], ends[s]
        hidx = b
        lh = np.nan
        lhi = -1
        prevsl = np.nan
        armed = False
        hl = np.nan
        hmax = h[b] if np.isnan(hod[b]) else max(hod[b], h[b])                 # running HOD (the first frame row carries 09:30-09:45 via hod)
        for i in range(b, e):
            if i > b and h[i] > hmax:
                hmax = h[i]
                hidx = i
                lh = np.nan
                lhi = -1
                armed = False
            j = i - 1
            if j - 1 >= b:
                if h[j] > h[j - 1] and h[j] > h[i] and j > hidx and h[j] < hmax:
                    lh = h[j]
                    lhi = j
                    armed = False
                if l[j] < l[j - 1] and l[j] < l[i]:
                    if lhi >= 0 and j > lhi and (not np.isnan(prevsl)) and l[j] > prevsl:
                        armed = True
                        hl = l[j]
                    prevsl = l[j]
            since[i] = i - hidx
            hm[i] = hmax
            if armed and c[i] > lh:
                sig[i] = True
                hlv[i] = hl
                armed = False
    return sig, hlv, since, hm


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if not n or "breadth" not in df:
        return np.zeros(n, dtype=bool)
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    sym = df["symbol"].astype(str).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        b, isend, HH, HL, HC = hourly(k, tod, h, l, c, hod, lod)
        lc = np.where(isend, b, b - 1)                       # latest completed hourly bin
        lcc = np.clip(lc, 0, NB - 1)
        pc_ = np.clip(lc - 1, 0, NB - 1)
        # previous symbol-day's last complete clock hour (bin 4, 13:30-14:30) when only bin 0 is complete today
        starts = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
        ksym = sym[starts]
        prevk = np.arange(len(starts)) - 1
        same = np.r_[False, ksym[1:] == ksym[:-1]]
        ph_y = np.where(same, HH[np.clip(prevk, 0, None), 4], np.nan)
        pl_y = np.where(same, HL[np.clip(prevk, 0, None), 4], np.nan)
        lastH, lastL, lastC = HH[k, lcc], HL[k, lcc], HC[k, lcc]
        prevH = np.where(lc >= 1, HH[k, pc_], ph_y[k])
        prevL = np.where(lc >= 1, HL[k, pc_], pl_y[k])
        m = (lc >= 0) & (lastH > prevH) & (lastL > prevL) & (lastC > vwap)
        ends = np.r_[starts[1:], n]
        sig, hlv, since, hm = _kern(starts.astype(np.int64), ends.astype(np.int64), h, l, c, hod)
        m &= sig & (since >= 8) & (c > lastL)
        m &= _f(df, "breadth") >= 0.45
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = hlv - 0.05 * atr
        tgt = hm
        m &= np.isfinite(stop) & (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)
