"""pod-raschke-310-first-cross-short - Raschke 3/10 oscillator: the first fast/signal re-cross after the signal line
flips sign (SHORT).

Source: Linda Raschke, LBR 3/10 oscillator (SMA3 - SMA10 of the close, 16-period signal line); 'first cross' rule
as described in the TradingView LBR 3-10 oscillator scripts.
URL: https://in.tradingview.com/script/SbWIhVzi-LBR-3-10-Oscillator

VARIANT of R13 macd-zero, R20 sma-macd and CWT39 (failed: zero-line crosses). Sibling of pod-raschke-anti-stoch-hook
(a hook while the slow line slopes); this is the first re-cross after the signal line changes sign.
Side: SHORT (this file; the exact mirror of pod-raschke-310-first-cross-long).

Rules (plain English; long shown, short = exact mirror):
  Fast line = SMA3(close) - SMA10(close); signal = SMA16(fast), on 5-minute bars per symbol (spans previous days,
  like the frame's own 5m indicators).
  1. The signal line crossed above 0 within the last 12 bars (same symbol-day) and is still above 0.
  2. Since that cross, the fast line has dipped below the signal line.
  3. The fast line now crosses back above the signal line, for the first time since the dip (one re-cross per
  signal-line flip).
  4. close > session VWAP; RSI(14) 45-70 (short: close < VWAP, RSI 30-55).
  Entry: that close, 10:00-14:45. Stop (GEOM S): the pullback swing low (lowest low since the fast line first went
  below the signal line) - 0.01, capped at 1R = 0.25 x daily ATR from the entry. Target: 1R (entry-to-stop) or the
  high of day at entry, whichever is nearer, when the HOD is at least 0.25 of that risk above the entry; else 1R.
  Flat 15:55. Costs per config/default.yaml (scorer).
Pre-declared choices: the 12-bar memory and the RSI bands are the idea's values; the 0.25-risk HOD floor stops a
target sitting on the entry. No tuning on valid.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1000, 1445)
CONTEXT = []
LAYERS = ["signal line (SMA16 of SMA3-SMA10) crossed 0 within 12 bars", "fast line dipped through the signal since",
          "first fast/signal re-cross", "close vs VWAP and RSI band", "stop swing extreme (cap 1R), target 1R or HOD/LOD"]

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

LONG = SIDE == "long"


@numba.njit(cache=False)
def _kernel(b, e, fast, sig, x, atr, c, ext, ok, sg):
    """sg = +1 long / -1 short; x = low (long) or -high (short), ext = HOD (long) or -LOD (short), c signed."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        zc = -1
        dip = -1
        swing = np.nan
        done = False
        for i in range(i0 + 1, i1):
            S0, S1 = sg * sig[i], sg * sig[i - 1]
            F0, F1 = sg * fast[i], sg * fast[i - 1]
            if not (S0 == S0 and S1 == S1 and F0 == F0 and F1 == F1):
                zc = -1
                continue
            if S0 > 0 and S1 <= 0:
                zc = i
                dip = -1
                swing = np.nan
                done = False
            elif S0 <= 0:
                zc = -1
                continue
            if zc < 0:
                continue
            if F0 < S0 and dip < 0:
                dip = i
                swing = x[i]
            if dip >= 0:
                swing = min(swing, x[i])
            if dip >= 0 and dip < i and not done and F0 > S0 and F1 <= S1:
                done = True
                if ok[i] and i - zc <= 11:
                    cc = c[i]
                    st = max(swing - 0.01, cc - 0.25 * atr[i])
                    risk = cc - st
                    if risk > 0:
                        t = cc + risk
                        if ext[i] >= cc + 0.25 * risk:
                            t = min(t, ext[i])
                        m[i] = True
                        stop[i] = sg * st
                        tgt[i] = sg * t
    return m, stop, tgt


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    k = _key(df)
    sc = _symcode(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    fast = _sma_sym(c, sc, 3) - _sma_sym(c, sc, 10)
    sig = _sma_sym(fast, sc, 16)
    rsi = _f(df, "rsi")
    vd = _f(df, "vwapDistPct")
    with np.errstate(invalid="ignore"):
        if LONG:
            ok = (vd > 0) & (rsi >= 45) & (rsi <= 70)
            x, ext, cs, sg = l, c + _f(df, "dist_hod_atr") * atr, c, 1.0
        else:
            ok = (vd < 0) & (rsi >= 30) & (rsi <= 55)
            x, ext, cs, sg = -h, -(c - _f(df, "dist_lod_atr") * atr), -c, -1.0
        ok &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    b, e = _segments(k)
    m, stop, tgt = _kernel(b, e, fast, sig, x, atr, cs, ext, np.asarray(ok, np.bool_), sg)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
