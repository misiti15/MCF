"""pod-raschke-blindfold-breadth-div - Raschke 'blindfold' divergence: a new low not confirmed by the 3/10
oscillator and by breadth (LONG).

Source: Linda Raschke intraday 3/10 oscillator + TICK divergence, as codified in TradingView 'LBR 3-10 TICK
Divergence'.
URL: https://fr.tradingview.com/script/s3jUDndY-LBR-3-10-TICK-Divergence/

VARIANT of R12 rsi-div (bull_div + close above the prior bar high, failed) and obos-levels. Stated change: the
divergence must be confirmed by market breadth at the same two swing lows, and the oscillator is the 3/10.

Universe: MIN_ADV = $500M adv20 (this keeps SPY, QQQ, IWM and the most liquid stocks; a few other very liquid ETFs
also pass this floor - the frame has no ETF flag).
Rules (plain English):
  Fast line = SMA3(close) - SMA10(close) on 5-minute bars per symbol (spans previous days). Breadth = share of the
  universe above its own session VWAP (the NYSE TICK proxy; context column).
  1. L2 = the previous bar: its low is a new 20-bar low (below the lows of the 20 bars before it, per symbol). L1 =
  the lowest low among the bars 6-30 bars before L2 in the same session, and it is a swing low (its low is at or
  below the lows of the bars on each side). L2's low is below L1's low.
  2. The 3/10 fast line at L2 > the fast line at L1.
  3. Breadth at L2 > breadth at L1 + 0.03.
  4. spy_fo > -1.0% and vwapDistPct > -1.5% (at the entry bar).
  5. The entry bar (the bar after L2) closes above L2's high.
  Entry: that close, 10:30-15:00. Stop (GEOM S): L2's low - 0.05 x daily ATR. Target: session VWAP at entry when it
  is at least 0.5 x the risk above the entry, else 1R (entry-to-stop, the t1s1 option). Flat 15:55. Costs per
  config/default.yaml (scorer).
Pre-declared choices: L1 = the lowest swing low in the 6-30 bar band; the 0.5-risk VWAP floor picks between the two
targets the idea names. No tuning on valid.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1500)
MIN_ADV = 500e6
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["L2 new 20-bar low below swing low L1 (6-30 bars earlier, same session)", "3/10 fast at L2 > at L1",
          "breadth at L2 > breadth at L1 + 0.03", "spy_fo > -1%, vwapDistPct > -1.5%", "next bar closes above L2 high",
          "stop L2 - 0.05 ATR, target VWAP or 1R, flat 15:55"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_DC = {}
_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _symcode(df):
    return pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()))[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _lag(x, k, n):
    """x from n bars earlier in the same group k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    if n <= 0:
        return x.copy()
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _sma_sym(x, sc, n):
    """Causal SMA(n) per symbol over the frame (spans previous days, like the frame's 5m indicators)."""
    s = pd.Series(np.asarray(x, float))
    return s.groupby(sc).transform(lambda v: v.rolling(n, min_periods=n).mean()).to_numpy(float)


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _daily_feats():
    """Per (symbol, date D): daily values as of D-1's close (completed days only). Series restart after a
    calendar gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        d = _lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    rng = (h - l).replace(0, np.nan)
    sma5 = gc.transform(lambda x: x.rolling(5).mean())
    sma50 = gc.transform(lambda x: x.rolling(50).mean())
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c,
        "sma5": sma5, "sma5_p": sma5.groupby(g).shift(1),
        "sma10": gc.transform(lambda x: x.rolling(10).mean()),
        "sma20": gc.transform(lambda x: x.rolling(20).mean()),
        "sma50": sma50, "sma50_p5": sma50.groupby(g).shift(5),
        "ibs": (c - l) / rng,
    })
    for col in [x for x in f.columns if x not in ("symbol", "date")]:
        f[col] = f[col].groupby(g).shift(1)          # the row for D carries the values as of D-1's close
    _DC["f"] = f
    return f


def _map_daily(df, k, cols):
    f = _daily_feats()
    if f is None:
        return None
    st = _start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(f, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


@numba.njit(cache=False)
def _relvol(b, e, c, h, l, vw, vr):
    """Bar volumes recovered (up to one scale per symbol-day) from successive session-VWAP values:
    v_t / cumV_t = (VWAP_t - VWAP_{t-1}) / (tp_t - VWAP_{t-1}); when that is not in (0,1) the bar's volume is
    scaled from the last valid bar by volumeRatio. First bar of the day: NaN."""
    n = len(c)
    out = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        cum = 1.0
        lastv = np.nan
        lastvr = np.nan
        for i in range(i0 + 1, i1):
            tp = (h[i] + l[i] + c[i]) / 3.0
            den = tp - vw[i - 1]
            w = (vw[i] - vw[i - 1]) / den if den != 0.0 else np.nan
            v = np.nan
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
            out[i] = v
    return out


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


@numba.njit(cache=False)
def _kernel(b, e, c, h, l, fast, br, ll20, ok):
    """For entry bar i: L2 = i-1; L1 = argmin low over [i-31, i-7] inside the session, a swing low."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    l2i = np.full(n, -1, np.int64)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 1, i1):
            if not ok[i]:
                continue
            j2 = i - 1
            if not (l[j2] < ll20[j2]):
                continue
            if not (c[i] > h[j2]):
                continue
            lo = max(i0, j2 - 30)
            hi = j2 - 6
            if hi < lo:
                continue
            j1 = -1
            best = np.inf
            for j in range(lo, hi + 1):
                if l[j] < best:
                    best = l[j]
                    j1 = j
            if j1 < 0 or j1 + 1 >= j2:
                continue
            if j1 > i0 and l[j1] > l[j1 - 1]:
                continue
            if l[j1] > l[j1 + 1]:
                continue
            if not (l[j2] < l[j1]):
                continue
            if not (fast[j2] > fast[j1]):
                continue
            if not (br[j2] > br[j1] + 0.03):
                continue
            m[i] = True
            l2i[i] = j2
    return m, l2i


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "breadth" not in df or "spy_fo" not in df:
        return z
    k = _key(df)
    sc = _symcode(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    fast = _sma_sym(c, sc, 3) - _sma_sym(c, sc, 10)
    ll20 = np.fmin.reduce(np.vstack([_lag(l, sc, j) for j in range(1, 21)]), axis=0)
    ll20 = np.where(np.isfinite(ll20), ll20, -np.inf)
    # need all 20 earlier bars present
    ll20 = np.where(np.isnan(_lag(l, sc, 20)), -np.inf, ll20)
    with np.errstate(invalid="ignore", divide="ignore"):
        vd = _f(df, "vwapDistPct")
        ok = (_f(df, "spy_fo") > -1.0) & (vd > -1.5) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        vw = c / (1 + vd / 100)
    b, e = _segments(k)
    m, l2i = _kernel(b, e, c, h, l, fast, _f(df, "breadth"), ll20, np.asarray(ok, np.bool_))
    stop = np.full(len(df), np.nan)
    tgt = np.full(len(df), np.nan)
    idx = np.flatnonzero(m)
    if len(idx):
        st = l[l2i[idx]] - 0.05 * atr[idx]
        risk = c[idx] - st
        tg = np.where(vw[idx] >= c[idx] + 0.5 * risk, vw[idx], c[idx] + risk)
        stop[idx] = st
        tgt[idx] = tg
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
