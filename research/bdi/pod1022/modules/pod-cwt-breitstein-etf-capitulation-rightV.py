"""pod-cwt-breitstein-etf-capitulation-rightV - Market-wide capitulation, right side of the V (index ETFs), LONG.

Source: Lance Breitstein, Chat With Traders 228/229/236 'The Ultimate Day Trader' (right side of the V, capitulation
reversals, same price different EV); CWT catalog CWT05 member setup ep236.
URL: https://chatwithtraders.com/228

VARIANT of CWT05 panic-flush V (Testing 2, single stocks, first bar above the prior bar high) and the IDX1-5 / LD index
dip bounces (shallow 09:45-09:55 dips). Stated changes: a daily multi-day capitulation gate, index ETFs only, the
confirmed right-side entry (higher high AND higher low), and a prior-bar-low trail (not in the harness, see exits).

Rules (plain English). SYMBOLS SPY, QQQ, IWM (config 3x: TQQQ, UPRO, SPXL, TNA - the -3x module).
  1. Daily gate (completed days only, research/history2y daily table): at least 3 of the last 4 daily closes were down
     (close below the close before it), and the prior close is at least 2 x daily ATR below the 10-day SMA of closes.
  2. The low bar (the bar that set the current low of day; it must be inside the frame and close 10:00-14:30) shows
     capitulation: fromOpen <= -1.2 x atr_d / close (in %), at least one bar of the last 6 (low bar included) has
     volumeRatio >= 2.5, and universe breadth (share above VWAP) is in the bottom decile of its own history. The
     decile is point-in-time: the 10th percentile of breadth over 10:00-14:30 bars of all EARLIER open dates (>= 20
     dates required; the locked block is never read).
  3. After the low bar, the first bar with high > low-bar high AND low > low-bar low (no new low in between), closing
     in the upper half of its own range. Entry at that close (10:00-14:30). A new low of day resets the low bar.
  Stop (GEOM S): low of day - 0.05 x daily ATR. Target: session VWAP at entry (if VWAP is not above the entry the
  trade holds to 15:55). Flat 15:55. The idea's prior-bar-low trail is not in the harness; the holdtr proxy is the
  separate config pod-cwt-breitstein-etf-capitulation-rightV-holdtr.py. Costs in (scorer).
No tweaks. Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM"]
CONTEXT = ["breadth"]
DROP_ATR = 1.2
VR_CLIMAX = 2.5
LAYERS = [">= 3 of last 4 daily closes down", "prior close >= 2 ATR below daily SMA10",
          "low bar: fromOpen <= -1.2 ATR%, volumeRatio >= 2.5 within 6 bars, breadth bottom decile (point-in-time)",
          "first bar after the low bar with HH and HL, close in the upper half", "10:00-14:30",
          "stop LOD - 0.05 ATR, target VWAP at entry, flat 15:55"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    return lib


def _daily_gate():
    """Per (symbol, next trading date): features of completed days only. Rows whose look-back spans a gap in the
    open daily table (the locked block) are dropped."""
    if "daily" in _CACHE:
        return _CACHE["daily"]
    d = _lib().daily()[["symbol", "date", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)["close"]
    dn = (d["close"] < g.shift(1)).astype(float)
    dn[g.shift(1).isna()] = np.nan
    d["dn4"] = dn.groupby(d["symbol"]).transform(lambda x: x.rolling(4).sum())
    d["sma10"] = g.transform(lambda x: x.rolling(10).mean())
    dt = pd.to_datetime(d["date"])
    span = (dt - dt.groupby(d["symbol"]).shift(10)).dt.days
    d.loc[~(span <= 22), ["dn4", "sma10"]] = np.nan
    d["next_date"] = d.groupby("symbol")["date"].shift(-1)
    nspan = (pd.to_datetime(d["next_date"]) - dt).dt.days
    d = d[nspan <= 5]
    out = d[["symbol", "next_date", "close", "dn4", "sma10"]].rename(columns={"next_date": "date", "close": "pc_d"})
    _CACHE["daily"] = out
    return out


def _breadth_thr(dates):
    """10th percentile of breadth (10:00-14:30 bars) over all earlier open dates; NaN with < 20 earlier dates."""
    if "ctx" not in _CACHE:
        lib = _lib()
        cs = []
        for mo in lib.months():
            try:
                cs.append(lib.load_context(mo)[["date", "tod", "breadth"]])
            except Exception:  # noqa: BLE001
                pass
        c = pd.concat(cs, ignore_index=True)
        c = c[(c["tod"] >= 1000) & (c["tod"] <= 1430) & np.isfinite(c["breadth"].to_numpy(float))]
        c["date"] = c["date"].astype(str)
        _CACHE["ctx"] = c
    c = _CACHE["ctx"]
    res = {}
    for dd in sorted(set(dates)):
        prior = c[c["date"] < dd]
        res[dd] = float(np.quantile(prior["breadth"].to_numpy(float), 0.10)) if prior["date"].nunique() >= 20 else np.nan
    return res


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, lod, fo, vr, br, thr, atr, gate, w0, w1, drop, vrc):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if not gate[i0]:
            continue
        j = -1
        cap = False
        used = False
        for i in range(i0, i1):
            if j < 0 or l[i] < l[j]:
                j = i
                used = False
                cap = False
                # the frame low must be the day's low (the low bar is inside the frame)
                if l[i] <= lod[i] + 1e-6 * c[i] and tod[i] >= w0 and tod[i] <= w1:
                    vmax = 0.0
                    for k in range(max(i0, i - 5), i + 1):
                        if vr[k] > vmax:
                            vmax = vr[k]
                    cap = (fo[i] <= -drop * atr[i] / c[i] * 100.0) and vmax >= vrc and br[i] <= thr[i]
                continue
            if used:
                continue
            if h[i] > h[j] and l[i] > l[j]:
                used = True
                if cap and tod[i] >= w0 and tod[i] <= w1 and (c[i] - l[i]) >= 0.5 * (h[i] - l[i]) and h[i] > l[i]:
                    m[i] = True
                    stop[i] = l[j] - 0.05 * atr[i]
    return m, stop


def compute(df):
    n = len(df)
    if n == 0 or "breadth" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - f("dist_lod_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    dg = key.merge(_daily_gate(), on=["symbol", "date"], how="left")
    with np.errstate(invalid="ignore"):
        gate = (dg["dn4"].to_numpy(float) >= 3) & (dg["pc_d"].to_numpy(float) <= dg["sma10"].to_numpy(float) - 2 * atr)
    ds = df["date"].astype(str).to_numpy()
    tm = _breadth_thr(ds)
    thr = np.array([tm[x] for x in ds], float)
    b, e = _segments(df)
    m, stop = _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, lod, f("fromOpen"), f("volumeRatio"),
                      f("breadth"), thr, atr, gate, WINDOW[0], WINDOW[1], DROP_ATR, VR_CLIMAX)
    tgt = np.where(vw > c, vw, c + 50 * atr)       # VWAP at entry; none above -> effectively hold to 15:55
    return m, stop, tgt


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
