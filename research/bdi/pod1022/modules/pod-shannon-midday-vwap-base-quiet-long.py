"""pod-shannon-midday-vwap-base-quiet-long - Quiet tape: midday base sitting on VWAP in a modest mover, afternoon break
(LONG).

Source: Brian Shannon Face2Face 'VWAP strategies' (videohighlight summary); Alpha Trends multiple-timeframe material.
URL: https://videohighlight.com/v/6So99CixJNg

VARIANT of CWT46 afternoon breakout (fromOpen >= 4/8%, failed) and CWT12 coil (failed). Sibling of
pod-smb-trend-trend-pm-consolidation-hold (daily-trend gate) and pod-chop-pop-volume-breakout-long (strong mover near
HOD). Stated change: MODEST movers (+0.8..+3%), the base must sit on VWAP, quiet-SPY gate.

Rules (plain English):
  1. Quiet tape: |spy_fo| < 0.3% and SPY's range so far today ((HOD - LOD) / close, from SPY's own frame row at the
     same (date, tod)) is below its median at the same time of day over the prior 20 sessions (prior sessions seen
     by this process, at least 10 required; no SPY row or too little history -> no trade).
  2. fromOpen +0.8% to +3%, and close above session VWAP on every bar closing 11:00 or later.
  3. Base = the 6 bars before the trigger: high-low range <= 0.3 x atr_d, base low at or above VWAP (VWAP at the last
     base bar) and within 0.3% above it.
  4. Trigger: close > the base high and buyPressure > 0.1.
  Entry: the trigger close. Stop (GEOM S): min(base low, VWAP) - 0.05 x atr_d. Target: HOD (at entry) + 0.25 x atr_d;
  else flat 15:55. Bar close 12:30-14:45.
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; the
SPY median uses only dates before the current one.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1445)
CONTEXT = ["spy_fo"]
LAYERS = ["|spy_fo| < 0.3, SPY range below its 20-day same-time median", "fromOpen 0.8-3%, above VWAP since 11:00",
          "6-bar base <= 0.3 ATR sitting 0-0.3% above VWAP", "close > base high, buyPressure > 0.1",
          "stop min(base low, VWAP) - 0.05 ATR, target HOD + 0.25 ATR"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


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


def _lag(x, k, n=1):
    """x from n bars earlier in the same group k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each group k."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    """True only on the first True row of each group (no earlier row qualified)."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to its symbol-day. Callers use it only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _ema_sym(x, sc, n):
    """Causal EMA(n) of 5-minute closes per symbol across the frame's days."""
    s = pd.Series(np.asarray(x, float))
    return s.groupby(sc).transform(lambda v: v.ewm(span=n, adjust=False).mean()).to_numpy(float)


def _sma_sym(x, sc, n):
    s = pd.Series(np.asarray(x, float))
    return s.groupby(sc).transform(lambda v: v.rolling(n, min_periods=n).mean()).to_numpy(float)


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vd"] = _f(df, "vwapDistPct")
    b["vwap"] = c / (1 + b["vd"] / 100)
    return b


def _daily_feats():
    """Per (symbol, date D): daily values as of D-1's close (completed days only). Series restart after a calendar
    gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        try:
            import lib
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        d = lib.daily()[["symbol", "date", "high", "low", "close", "adv20"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    sma10 = gc.transform(lambda x: x.rolling(10).mean())
    sma20 = gc.transform(lambda x: x.rolling(20).mean())
    ret21 = c / gc.shift(21) - 1
    elig = (d["adv20"] >= 20e6) & ret21.notna()
    rk = ret21.where(elig).groupby(d["date"]).rank(pct=True)
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c, "d_high": h, "d_low": l,
        "d_high_p": h.groupby(g).shift(1), "d_low_p": l.groupby(g).shift(1),
        "sma10": sma10, "sma10_p": sma10.groupby(g).shift(1),
        "sma20": sma20, "sma20_p": sma20.groupby(g).shift(1),
        "sma50": gc.transform(lambda x: x.rolling(50).mean()),
        "hi20": h.groupby(g).transform(lambda x: x.rolling(20).max()),
        "hi10": h.groupby(g).transform(lambda x: x.rolling(10).max()),
        "lo10": l.groupby(g).transform(lambda x: x.rolling(10).min()),
        "ret21_rank": rk,
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


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)

_SPYH = {}


def _spy_quiet(df, tod):
    """SPY range-so-far (%) vs its median at the same tod over the prior 20 dates (min 10) in the process store."""
    sym = df["symbol"].astype(str).to_numpy()
    sel = sym == "SPY"
    out = np.zeros(len(df), bool)
    if not sel.any():
        return out
    atr = _f(df, "atr_d")[sel]
    rng = (_f(df, "dist_hod_atr")[sel] + _f(df, "dist_lod_atr")[sel]) * atr / _f(df, "close")[sel] * 100
    ds = df["date"].astype(str).to_numpy()[sel]
    for d, t, r in zip(ds, tod[sel], rng):
        _SPYH[(d, int(t))] = float(r)
    s = pd.Series(_SPYH)
    s.index = pd.MultiIndex.from_tuples(s.index, names=["date", "tod"])
    piv = s.unstack("tod").sort_index()
    med = piv.shift(1).rolling(20, min_periods=10).median()
    q = (piv < med).stack()
    q = q[q]
    keys = pd.MultiIndex.from_arrays([df["date"].astype(str).to_numpy(), tod.astype(int)])
    return np.asarray(keys.isin(q.index), bool)


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr, vw = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"], b["vwap"]
    quiet = _spy_quiet(df, tod)
    with np.errstate(invalid="ignore", divide="ignore"):
        fo = _f(df, "fromOpen")
        m = quiet & (np.abs(_f(df, "spy_fo")) < 0.3) & (fo >= 0.8) & (fo <= 3.0)
        m &= (tod >= 1100) & (_gcum((tod >= 1100) & ~(b["vd"] > 0), k) == 0)
        bh = np.max(np.vstack([_lag(h, k, j) for j in range(1, 7)]), axis=0)
        bl = np.min(np.vstack([_lag(l, k, j) for j in range(1, 7)]), axis=0)
        pvw = _lag(vw, k, 1)
        m &= (bh - bl) <= 0.3 * atr
        m &= (bl >= pvw) & (bl <= pvw * 1.003)
        m &= (c > bh) & (_f(df, "buyPressure") > 0.1)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = np.minimum(bl, vw) - 0.05 * atr
        tgt = b["hod"] + 0.25 * atr
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
