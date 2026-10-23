"""pod-fisher-pivot-range-pullback-long - Narrow pivot-range day: buy the first pullback into the pivot range (LONG).

Source: Mark Fisher, 'The Logical Trader' (daily pivot range as support / resistance). The URL was not re-checked
this round.
URL: https://www.wiley.com/en-us/The+Logical+Trader%3A+Applying+a+Method+to+the+Madness-p-9780471215516

VARIANT of pod-cpr-wide-range-day-pivot-fade (fades S1/R1 back to the CPR on WIDE-pivot days). Stated change: the
opposite regime gate (NARROW pivot range), the level is the pivot range itself, and the trade is trend continuation.
Levels from the prior COMPLETED day's H/L/C (research/history2y lib.daily()): P = (H+L+C)/3, BC = (H+L)/2,
PR top / bottom = max / min(P, BC); width = |P - BC| / P.
Rules (plain English):
  0. Narrow pivot range: width ranks in the bottom 30% of the trailing 20 sessions (completed days only).
  1. Today's open > the PR top and |gap| <= 1.0%.
  2. Tag: between 10:00 and 13:00, the first bar whose low <= the PR top and whose close >= the PR bottom (a tag
     without acceptance below).
  3. Signal: the tag bar or the next bar closes back above the PR top with lower_wick >= 0.35 or close > the prior
     bar's high.
  4. spy_fo >= 0, and the high of day before the signal was >= PR top + 0.3 x atr_d.
  Entry: that close. Stop (GEOM S): PR bottom - 0.10 x atr_d. Target: the HOD (skip if < 1R away); else flat 15:55.
Pre-declared readings: 'first bar' counts from 10:00 (one tag per day; if neither the tag bar nor the next bar
signals, no trade that day); rule 4's HOD is the high of day as of the bar before the signal. No tweak used. No
tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1305)
CONTEXT = ["spy_fo"]
LAYERS = ["pivot width bottom 30% of 20 sessions", "open > PR top, |gap| <= 1%",
          "first 10:00-13:00 bar with low <= PR top and close >= PR bottom",
          "that/next bar closes > PR top with lower_wick >= 0.35 or close > prior high",
          "spy_fo >= 0, HOD >= PR top + 0.3 ATR", "stop PR bottom - 0.1 ATR, target HOD (>= 1R)"]

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


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def _daily_feats():
    """Per (symbol, date D): Fisher pivot range from D-1 H/L/C (P = (H+L+C)/3, BC = (H+L)/2, top/bottom = max/min)
    and the pivot-range width |P-BC|/P percentile rank over D-20..D-1 (completed days only). Series restart after a
    calendar gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        try:
            import lib
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        d = lib.daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    H, L, C = d["high"], d["low"], d["close"]
    P = (H + L + C) / 3
    BC = (H + L) / 2
    w = (P - BC).abs() / P
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "pr_hi": np.maximum(P, BC), "pr_lo": np.minimum(P, BC),
        "wrank": w.groupby(g).transform(lambda x: x.rolling(20).rank(pct=True)),
    })
    for col in ("pr_hi", "pr_lo", "wrank"):
        f[col] = f[col].groupby(g).shift(1)          # the row for D carries values as of D-1's close
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


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


def _lag(x, k, n=1):
    x = np.asarray(x, float)
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


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df:
        return z
    k = _key(df)
    dd = _map_daily(df, k, ["pr_hi", "pr_lo", "wrank"])
    if dd is None:
        return z
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    top, bot = dd["pr_hi"], dd["pr_lo"]
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        opn = c / (1 + _f(df, "fromOpen") / 100)
        tagc = (l <= top) & (c >= bot) & (tod >= 1000) & (tod <= 1300)
        tag = tagc & ((_gcum(tagc, k) - tagc) == 0)
        ptag = _lag(tag.astype(float), k) == 1
        recl = (c > top) & ((_f(df, "lower_wick") >= 0.35) | (c > _lag(h, k)))
        m = recl & (tag | ptag)
        m &= (dd["wrank"] <= 0.30) & (opn > top) & (np.abs(_f(df, "gap")) <= 1.0)
        phod = _lag(hod, k)
        m &= (_f(df, "spy_fo") >= 0) & (phod >= top + 0.3 * atr)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = bot - 0.10 * atr
        tgt = hod
        m &= (stop < c) & ((tgt - c) >= (c - stop))
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
