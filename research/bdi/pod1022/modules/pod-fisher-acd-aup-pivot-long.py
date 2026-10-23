"""pod-fisher-acd-aup-pivot-long - ACD 'A up' with time confirmation and a narrow pivot-range filter (LONG).

Source: Mark Fisher, 'The Logical Trader' (ACD method). Web search was unavailable this round, so the URL was not
re-checked.
URL: https://www.wiley.com/en-us/The+Logical+Trader%3A+Applying+a+Method+to+the+Madness-p-9780471215516

VARIANT of CWT ep138 Kevin Muir 'opening-range side filter + VWAP lean', nr7-orb (idea) and
pod-unger-first-hour-2nd-hour-break. Stated change: Fisher's offset A level, the time-acceptance rule and the
pivot-range gate; not a plain OR-high break.
Levels: OR = HOD / LOD as of the 09:50 bar (09:30-09:50). A_up = ORH + 0.15 x atr_d. Pivot range from the prior
COMPLETED day's H/L/C (research/history2y lib.daily()): P = (H+L+C)/3, BC = (H+L)/2, top = max(P, BC).
Rules (plain English):
  1. Today's open and the current close are above the pivot-range top.
  2. Three consecutive 5m closes above A_up (time acceptance), first occurrence of the day only, the third bar's close
     10:00-11:30.
  3. close > VWAP and spy_fo > 0.
  4. The pivot-range width |P - BC| / P ranks in the bottom 40% of the trailing 20 sessions (completed days only).
  Entry: the third bar's close. Stop (GEOM S): the OR midpoint (Fisher's B), or entry - 0.35 x atr_d if that is
  closer. Target: entry + 1.5R; else flat 15:55.
Harness notes: the count of closes above A starts at the 09:50 bar (the 09:50 close is the end of the OR, so it can
count). No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
CONTEXT = ["spy_fo"]
LAYERS = ["open and close above the prior-day pivot-range top", "3rd consecutive close above ORH + 0.15 ATR (first)",
          "close > VWAP, spy_fo > 0", "pivot width bottom 40% of 20 sessions",
          "stop max(OR mid, entry - 0.35 ATR), target 1.5R"]

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


@numba.njit(cache=False)
def _third(st, c, a):
    """True on the first bar of each day where the run of consecutive closes above a reaches 3."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    run = 0
    done = False
    for i in range(n):
        if st[i]:
            run = 0
            done = False
        if c[i] > a[i]:
            run += 1
        else:
            run = 0
        if run == 3 and not done:
            m[i] = True
            done = True
    return m


def _at(x, k, tod, T):
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df:
        return z
    k = _key(df)
    dd = _map_daily(df, k, ["pr_hi", "wrank"])
    if dd is None:
        return z
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        orh, orl = _at(hod, k, tod, 950), _at(lod, k, tod, 950)
        a_up = orh + 0.15 * _at(atr, k, tod, 950)
        opn = c / (1 + _f(df, "fromOpen") / 100)
        trig = _third(_start(k), c, np.where(np.isfinite(a_up), a_up, np.inf))
        m = trig & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        m &= (opn > dd["pr_hi"]) & (c > dd["pr_hi"])
        m &= (_f(df, "vwapDistPct") > 0) & (_f(df, "spy_fo") > 0)
        m &= dd["wrank"] <= 0.40
        stop = np.maximum(0.5 * (orh + orl), c - 0.35 * atr)
        m &= stop < c
        tgt = c + 1.5 * (c - stop)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
