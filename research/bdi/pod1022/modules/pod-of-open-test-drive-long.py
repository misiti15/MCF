"""pod-of-open-test-drive-long - Open test drive: an early test of the PDL / prior close holds, then the first break
of the 09:50 high (LONG).

Source: Axia Futures Volume Profile course notes (open test drive) + FTMO 'Market Profile: types of opens and the
anatomy of a trading day'.
URL: https://ftmo.com/en/futures/blog/market-profile-types-of-opens-and-the-anatomy-of-a-trading-day-2/

VARIANT of orb20_a / t2-orb15 (plain opening-range breaks). Stated change: an early TEST of a key level that HELD
(undercut <= 0.05 x atr_d - a test, not a sweep, so not LIQ / R15) is required, and the OR break is taken only away
from the tested level (the tested level sits at the low, the break is of the high).

Rules (plain English), decision bar i:
  1. Test: the low of day as of the 10:00 bar (covers 09:30-10:00) lies within 0.10 x atr_d of the prior-day low or
     the prior close (from gap / fromOpen), with an undercut of that level of at most 0.05 x atr_d
     (level - 0.05 ATR <= LOD <= level + 0.10 ATR). The test held: the low of day at bar i is still that 10:00 LOD.
  2. OR high = the high of day at the 09:50 bar (09:30-09:50).
  3. Trigger, bar close 10:00-11:00: the FIRST close above the OR high since 09:50, and that bar has
     volumeRatio >= 1.3 (if the first break is on lighter volume, no trade that day).
  4. close > session VWAP and spy_fo > 0.
  Entry: the trigger close. Stop (GEOM S): LOD - 0.05 x atr_d. Exit: the source plan says holdtr; the harness has no
  trail for structural stops, so the trade holds to 15:55 (no target). Costs in (scorer, config/default.yaml).
  No tweak used. Only bars up to the decision bar; prior-day values come from completed days (dist_pdl_atr, gap).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1100)
CONTEXT = ["spy_fo"]
LAYERS = ["10:00 LOD tests PDL or prior close (-0.05..+0.10 ATR) and still holds",
          "first close above the 09:50 HOD, volumeRatio >= 1.3", "close > VWAP, spy_fo > 0",
          "stop LOD - 0.05 ATR, hold to 15:55", "10:00-11:00 ET"]
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day (NaN across a day boundary)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _at(x, k, tod, T):
    """Value of x on the bar closing at T, broadcast to its symbol-day. Use only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        pdl = c - _f(df, "dist_pdl_atr") * atr
        opn = c / (1 + _f(df, "fromOpen") / 100)
        pc = opn / (1 + _f(df, "gap") / 100)
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        lod10 = _at(lod, k, tod, 1000)
        orh = _at(hod, k, tod, 950)
        a = atr
        t_pdl = (lod10 >= pdl - 0.05 * a) & (lod10 <= pdl + 0.10 * a)
        t_pc = (lod10 >= pc - 0.05 * a) & (lod10 <= pc + 0.10 * a)
        m = (tod >= 1000) & (t_pdl | t_pc) & (lod >= lod10 - 1e-9)
        brk = (tod > 950) & (c > orh)
        first = brk & ((_gcum(brk, k) - brk) == 0)
        m &= first & (_f(df, "volumeRatio") >= 1.3)
        m &= (c > vwap) & (_f(df, "spy_fo") > 0)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * a
        m &= stop < c
    _ST[id(df)] = (stop, None)
    return np.asarray(m, dtype=bool)
