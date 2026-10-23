"""pod-smb-20d-high-time-acceptance-long - Multi-week (20-day) high break held for 15+ minutes (LONG).

Source: SMB Capital YouTube / PlayBook trade reviews of stocks breaking multi-week highs ('Trade2Hold', in play at new
highs). Taken from SMB material already known; the web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of pod-of-pdh-time-acceptance-long. Stated change: the level is the 20-day high (excluding today) instead of
PDH, and there is an SPY trend gate.

Levels from COMPLETED days only (research/history2y daily table, open months): L = max daily high of the 20 completed
sessions before today (D-1 included); PDH = D-1 high. Daily ATR = the frame's atr_d. SPY vs its session VWAP = the SPY
frame row's vwapDistPct at the same (date, tod) (live this needs an SPY VWAP context column; none exists yet, so live
the module returns no trades rather than guessing).

Rules (plain English), decision bar i:
  1. L >= PDH + 0.5 x daily ATR (not just a PDH break).
  2. Today's open is below L, and the FIRST 5-min close above L (bar j) is a bar closing after 10:00 (tod >= 10:05);
     no frame bar before j closed above L.
  3. Bars j+1, j+2, j+3 all close above L (15-minute acceptance) and their mean volumeRatio >= 1.2.
  4. SPY is above its session VWAP on bar i = j+3.
  Entry: the open of the 5th bar = close of bar j+3 (scorer enters at close_i), bar close 10:15-14:30 ET, one entry
  per symbol-day.
  Stop (GEOM S): L - 0.25 x daily ATR. Exit: the source exits on a 5-min close below session VWAP or at 15:55; the
  scorer has no indicator exit, so the trade holds to 15:55 (no target) with the structural stop. Costs in (scorer).
No tweak used; thresholds are the idea's. Frames start at the 09:50 bar; 09:30-09:45 closes cannot be checked, so the
open-below-L rule stands in for them.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1430)
LAYERS = ["20-day high >= PDH + 0.5 ATR", "open below it; first close above it after 10:00",
          "next 3 closes above it, mean volumeRatio >= 1.2", "SPY above its session VWAP",
          "stop 20dH - 0.25 ATR, hold to 15:55", "10:15-14:30 ET"]

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
    """Per (symbol, next trading date): 20-day high of completed sessions and D-1 high."""
    if "d" in _CACHE:
        return _CACHE["d"]
    d = _lib().daily()[["symbol", "date", "high"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    d["h20"] = g["high"].transform(lambda x: x.rolling(20).max())
    dt = pd.to_datetime(d["date"])
    gd = dt.groupby(d["symbol"])
    d.loc[~((dt - gd.shift(19)).dt.days <= 40), "h20"] = np.nan
    d["next_date"] = g["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "high", "h20"]].rename(columns={"next_date": "date", "high": "d1h"})
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
def _kernel(b, e, tod, c, fo, vr, atr, d1h, h20, spyv, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        L, pdh = h20[i0], d1h[i0]
        if not (a > 0 and L == L and pdh == pdh and L >= pdh + 0.5 * a):
            continue
        op = c[i0] / (1.0 + fo[i0] / 100.0)
        if not (op < L):
            continue
        j = -1
        for k in range(i0, i1):
            if c[k] > L:
                j = k
                break
        if j < 0 or tod[j] < 1005:
            continue
        i = j + 3
        if i >= i1 or tod[i] < w0 or tod[i] > w1:
            continue
        if not (c[j + 1] > L and c[j + 2] > L and c[j + 3] > L):
            continue
        if not ((vr[j + 1] + vr[j + 2] + vr[j + 3]) / 3.0 >= 1.2):
            continue
        if not (spyv[i] > 0):
            continue
        sp = L - 0.25 * a
        if sp < c[i]:
            m[i] = True
            stop[i] = sp
    return m, stop


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy(),
                        "tod": df["tod"].to_numpy()})
    spy = df.loc[df["symbol"].astype(str) == "SPY", ["date", "tod", "vwapDistPct"]]
    if not len(spy):
        return np.zeros(n, bool), np.full(n, np.nan)
    spy = spy.drop_duplicates(["date", "tod"]).rename(columns={"vwapDistPct": "spyv"})
    try:
        dg = key.merge(_daily(), on=["symbol", "date"], how="left").merge(spy, on=["date", "tod"], how="left")
    except Exception:  # noqa: BLE001 - no daily table -> no trades
        return np.zeros(n, bool), np.full(n, np.nan)
    g = lambda k: dg[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("fromOpen"), f("volumeRatio"), f("atr_d"),
                   g("d1h"), g("h20"), g("spyv"), WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop,)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])
