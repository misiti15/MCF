"""pod-chop-pop-volume-breakout-long - Chop and Pop: a compressed midday box near the HOD breaks on a volume burst
(LONG).

Source: DayTradingToolkit 'The Chop and Pop Strategy'; tosindicators 'Can't Trade The Market Open Or Close? Try This
Hour Instead' (11:30-12:30 range < 30% of the morning range).
URL: https://daytradingtoolkit.com/strategies/the-chop-and-pop-strategy-afternoon-reversals

VARIANT of CWT46 afternoon breakout (cwt-b-b6, failed, 32 configs). Siblings: pod-shannon-midday-vwap-base-quiet-long
(modest movers, quiet SPY), pod-smb-trend-trend-pm-consolidation-hold (daily trend). Stated change: a compression ratio
against the morning range, a volume burst measured against the box's own volume, a later trigger window and a midpoint
stop.

Rules (plain English), decision bar i:
  1. Strong morning: fromOpen >= +1.5% on the 11:00 bar; adv20 >= $50M (MIN_ADV).
  2. Box = the bars closing 11:05-14:00. Box height (max high - min low) <= 0.40 x atr_d AND <= 35% of the morning
     range (HOD - LOD as of the 11:00 bar, i.e. 09:30-11:00).
  3. Box high within 0.35 x atr_d of the HOD as of 14:00; mean volumeRatio over the box bars <= 0.7 (proxy for box
     volume <= 0.7x the morning average; the frames hold no raw volume).
  4. Trigger, bar close 14:05-15:00: the first close above the box high after 14:00, with volumeRatio >= 2.5.
  The optional SPY-above-VWAP filter is not used (SPY VWAP is not in the context). Entry: close. Stop (GEOM S): box
  midpoint. Target: box high + box height, else flat 15:55. No tweak used. Only bars up to the decision bar (the box
  ends at 14:00, before every trigger). Costs in (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1405, 1500)
MIN_ADV = 50e6
CONTEXT = []
LAYERS = ["fromOpen >= 1.5% at 11:00, adv20 >= $50M", "11:00-14:00 box <= 0.40 ATR and <= 35% of the morning range",
          "box high within 0.35 ATR of HOD, mean box volumeRatio <= 0.7", "first close > box high with volumeRatio >= 2.5",
          "stop box midpoint, target box high + height", "14:05-15:00 ET"]
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


def _grp(x, k, sel, how):
    """Per symbol-day aggregate of x over rows sel, broadcast to the day."""
    g = int(k.max()) + 1
    s = pd.Series(np.where(sel, x, np.nan))
    r = getattr(s.groupby(k), how)()
    out = np.full(g, np.nan)
    out[r.index.to_numpy()] = r.to_numpy(float)
    return out[k]


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    vr = _f(df, "volumeRatio")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        fo11 = _at(_f(df, "fromOpen"), k, tod, 1100)
        mrng = _at(hod - lod, k, tod, 1100)
        hod14 = _at(hod, k, tod, 1400)
        box = (tod > 1100) & (tod <= 1400)
        bh = _grp(h, k, box, "max")
        bl = _grp(l, k, box, "min")
        bn = _grp(np.ones(len(df)), k, box, "sum")
        bvr = _grp(vr, k, box, "mean")
        ht = bh - bl
        m = (tod > 1400) & (bn >= 30)
        m &= fo11 >= 1.5
        m &= (ht <= 0.40 * atr) & (ht <= 0.35 * mrng)
        m &= (hod14 - bh) <= 0.35 * atr
        m &= bvr <= 0.7
        brk = (tod > 1400) & (c > bh)
        first = brk & ((_gcum(brk, k) - brk) == 0)
        m &= first & (vr >= 2.5)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = (bh + bl) / 2
        tgt = bh + ht
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)
