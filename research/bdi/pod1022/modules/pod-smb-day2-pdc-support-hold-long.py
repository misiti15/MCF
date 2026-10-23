"""pod-smb-day2-pdc-support-hold-long - SMB Second-Day Play: big day-1 winner dips to the day-1 close and holds (LONG).

Source: SMB Capital PlayBook 'Second Day Play' (Mike Bellafiore, The PlayBook; SMB YouTube PlayBook reviews). Taken
from SMB material already known; the web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of pod-smb-day2-drive-pullback-long (needs an opening drive, buys the VWAP/SMA20 pullback) and distinct from
CWT10 (PDH breakout). Stated change: no drive; the support is the day-1 CLOSE (PDC); the entry is a hold / higher low
after the test.

Prior-day values come only from COMPLETED days (research/history2y daily table, open months only): D-1 high, low,
close, volume; D-1 rvol = D-1 volume / mean volume of the 20 days before D-1. Daily ATR = the frame's atr_d (ATR14 as
of the prior close). VWAP = close / (1 + vwapDistPct%). Low of day = close - dist_lod_atr x atr_d (it includes the
09:30-09:50 bars, which the frames do not hold as rows).

Rules (plain English), decision bar i:
  1. Day 1 was a big winner: D-1 range >= 2 x daily ATR, D-1 close in the top 25% of its range, D-1 rvol >= 2.
  2. Day 2 opened above PDC and traded DOWN to within 0.10 ATR of PDC (low of day <= PDC + 0.10 ATR); the low of day
     was made by 12:00 ET; no 5-min close (frame bars from 09:50 up to i) below PDC - 0.15 ATR.
  3. Hold: after the low-of-day bar, bar i makes a higher low (low_i > low_{i-1}) and closes above the prior bar's
     high (close_i > high_{i-1}).
  Entry: the scorer enters at close_i (= next bar open), bar close 09:50-12:00 ET, one per symbol-day.
  Stop (GEOM S): touch low (low of day) - 0.05 ATR.
  Target: the source takes half at VWAP and the rest at the day-1 high or 15:55. The scorer has one limit target,
  so the pre-declared blend is the midpoint of VWAP and PDH (when VWAP is above entry; PDH alone otherwise). Flat 15:55.
  Costs in (scorer, config/default.yaml).
No tweak used; thresholds are the idea's. Frames start at the 09:50 bar, so 09:35-09:45 closes are not checked.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1200)
LAYERS = ["D-1 range >= 2 ATR, D-1 close in top 25% of range, D-1 rvol >= 2",
          "open > PDC, LOD within PDC + 0.10 ATR, LOD made by 12:00, no close below PDC - 0.15 ATR",
          "after the LOD bar: higher low and close > prior high", "stop LOD - 0.05 ATR, target mid(VWAP, PDH)",
          "09:50-12:00 ET"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    return lib


def _daily():
    """Per (symbol, next trading date): D-1 high/low/close/range location/rvol from completed days only."""
    if "d" in _CACHE:
        return _CACHE["d"]
    d = _lib().daily()[["symbol", "date", "high", "low", "close", "volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    d["v20"] = g["volume"].transform(lambda x: x.shift(1).rolling(20).mean())
    dt = pd.to_datetime(d["date"])
    gd = dt.groupby(d["symbol"])
    d.loc[~((dt - gd.shift(20)).dt.days <= 40), "v20"] = np.nan
    d["rvol1"] = d["volume"] / d["v20"]
    d["next_date"] = g["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "high", "low", "close", "rvol1"]].rename(
        columns={"next_date": "date", "high": "d1h", "low": "d1l", "close": "d1c"})
    _CACHE["d"] = out
    return out


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, fo, dlod, vd, atr, d1h, d1l, d1c, rv1, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        pdc, pdh, pdl, rv = d1c[i0], d1h[i0], d1l[i0], rv1[i0]
        if not (a > 0 and pdc > 0 and pdh > pdl and rv == rv):
            continue
        if not (pdh - pdl >= 2.0 * a and (pdc - pdl) / (pdh - pdl) >= 0.75 and rv >= 2.0):
            continue
        op = c[i0] / (1.0 + fo[i0] / 100.0)
        if not (op > pdc):
            continue
        bad = False
        for i in range(i0, i1):
            if c[i] < pdc - 0.15 * a:
                bad = True             # every later bar fails too
            if bad:
                break
            if i == i0 or tod[i] < w0 or tod[i] > w1:
                continue
            lod = c[i] - dlod[i] * a
            if not (lod <= pdc + 0.10 * a):
                continue
            # bar that made the low of day (-1 = before the first frame bar, i.e. 09:30-09:50)
            k = -1
            for j in range(i, i0 - 1, -1):
                if l[j] <= lod + 1e-6 * a:
                    k = j
                    break
            if k >= 0 and tod[k] > 1200:
                continue
            if not (i - 1 >= k and i > k):
                continue
            if not (l[i] > l[i - 1] and c[i] > h[i - 1]):
                continue
            sp = lod - 0.05 * a
            vw = c[i] / (1.0 + vd[i] / 100.0)
            t = 0.5 * (vw + pdh) if vw > c[i] else pdh
            if sp < c[i] and t > c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = t
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    try:
        dg = key.merge(_daily(), on=["symbol", "date"], how="left")
    except Exception:  # noqa: BLE001 - no daily table -> no trades
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    g = lambda k: dg[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("fromOpen"),
                   f("dist_lod_atr"), f("vwapDistPct"), f("atr_d"), g("d1h"), g("d1l"), g("d1c"), g("rvol1"),
                   WINDOW[0], WINDOW[1])


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
