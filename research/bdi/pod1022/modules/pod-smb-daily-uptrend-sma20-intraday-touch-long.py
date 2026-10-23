"""pod-smb-daily-uptrend-sma20-intraday-touch-long - Daily-uptrend stock tags its 20-day SMA intraday and reclaims it
(SMB 'buy support in a strong stock') (LONG).

Source: SMB Capital YouTube 'Recognizing a strong stock' / PlayBook support-buy reviews. Taken from SMB material
already known; the web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of CWT25 uptrend pullback to SMA20/50 (daily, next-open / MOC entry) and of pod-shannon-5dma-mtf-pullback-long
(5-day MA). Stated change: the 20-day SMA is an INTRADAY level with a same-day 5-min reclaim entry and same-day exit.

Daily values from COMPLETED days only (research/history2y daily table, open months): SMA20 / SMA50 = mean of the last
20 / 50 daily closes through D-1; SMA20 slope = SMA20 now vs the SMA20 five sessions earlier. PDC = D-1 close. Daily
ATR = atr_d. Low of day = close - dist_lod_atr x atr_d (includes 09:30-09:50). VWAP = close / (1 + vwapDistPct%).

Rules (plain English), decision bar i:
  1. Daily uptrend: PDC > SMA20 > SMA50 and SMA20 rising (SMA20 - SMA20 five sessions back > 0).
  2. Today's low of day (as of bar i) is within 0.10 ATR above the SMA20 or below it, but not more than 0.3 ATR below:
     SMA20 - 0.3 ATR <= LOD <= SMA20 + 0.10 ATR.
  3. Reclaim: close_i > SMA20 with volumeRatio_i >= 1.2, while close_{i-1} <= SMA20 + 0.10 ATR (pre-declared reading
     of 'back above': the prior bar was at or under the level zone).
  4. No big gap down: today's open - PDC >= -1 x daily ATR.
  Entry: the scorer enters at close_i (= next bar open), bar close 10:00-14:30 ET, one per symbol-day.
  Stop (GEOM S): LOD - 0.05 ATR. Target: the farther of VWAP and entry + 1.5R, capped at entry + 2R (R = entry - stop).
  Flat 15:55. Costs in (scorer).
No tweak used; thresholds are the idea's.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
LAYERS = ["PDC > SMA20 > SMA50 (daily), SMA20 5-day slope > 0", "SMA20 - 0.3 ATR <= LOD <= SMA20 + 0.10 ATR",
          "close > SMA20 from <= SMA20 + 0.10 ATR, volumeRatio >= 1.2", "gap >= -1 ATR",
          "stop LOD - 0.05 ATR, target max(VWAP, 1.5R) capped 2R", "10:00-14:30 ET"]

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
    """Per (symbol, next trading date): D-1 close, SMA20, SMA50, SMA20 five sessions earlier (completed days)."""
    if "d" in _CACHE:
        return _CACHE["d"]
    d = _lib().daily()[["symbol", "date", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    d["sma20"] = g["close"].transform(lambda x: x.rolling(20).mean())
    d["sma50"] = g["close"].transform(lambda x: x.rolling(50).mean())
    dt = pd.to_datetime(d["date"])
    gd = dt.groupby(d["symbol"])
    d.loc[~((dt - gd.shift(19)).dt.days <= 40), "sma20"] = np.nan
    d.loc[~((dt - gd.shift(49)).dt.days <= 90), "sma50"] = np.nan
    d["sma20_5"] = d.groupby("symbol", sort=False)["sma20"].shift(5)
    d.loc[~((dt - gd.shift(5)).dt.days <= 12), "sma20_5"] = np.nan
    d["next_date"] = g["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "close", "sma20", "sma50", "sma20_5"]].rename(
        columns={"next_date": "date", "close": "d1c"})
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
def _kernel(b, e, tod, c, fo, dlod, vr, vd, atr, d1c, s20, s50, s20p, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        pdc, S, S50, Sp = d1c[i0], s20[i0], s50[i0], s20p[i0]
        if not (a > 0 and pdc > S and S > S50 and S - Sp > 0):
            continue
        op = c[i0] / (1.0 + fo[i0] / 100.0)
        if not (op - pdc >= -1.0 * a):
            continue
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            lod = c[i] - dlod[i] * a
            if not (lod >= S - 0.3 * a and lod <= S + 0.10 * a):
                continue
            if not (c[i] > S and vr[i] >= 1.2 and c[i - 1] <= S + 0.10 * a):
                continue
            sp = lod - 0.05 * a
            R = c[i] - sp
            if not (R > 0):
                continue
            vw = c[i] / (1.0 + vd[i] / 100.0)
            t = min(max(vw, c[i] + 1.5 * R), c[i] + 2.0 * R)
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
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("fromOpen"), f("dist_lod_atr"), f("volumeRatio"),
                   f("vwapDistPct"), f("atr_d"), g("d1c"), g("sma20"), g("sma50"), g("sma20_5"),
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
