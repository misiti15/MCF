"""pod-carter-pm-midrange-squeeze-long - Afternoon mid-range Bollinger-inside-Keltner squeeze on an up day, target the
high of day (LONG).

Source: John Carter, Chat With Traders ep 069 and 'Mastering the Trade' (the Squeeze: Bollinger Bands inside Keltner
Channels, then the release), applied here on 5-minute bars; already in the research/bdi/cwt catalog (ep069) as a daily
setup.
URL: https://chatwithtraders.com/ep-069-john-carter/

VARIANT of bdi-art-squeeze-vol-rework (morning, both sides, volume >= 1.5x trigger), CWT ep069 (daily),
pod-chop-pop-volume-breakout-long (box NEAR the HOD, volume burst >= 2.5x) and pod-tosind-lunch-compression-index-break
(index ETFs, fixed 11:30-12:30 box). Stated change: the 5m BB/KC squeeze sits in the MIDDLE of the day range
(>= 0.30 x atr_d below the HOD), no volume trigger, long only on up days, the HOD is the target.

Rules (plain English, LONG). Indicators on 5-minute bars, rolling per symbol over the loaded bars (they span earlier
sessions, like a 5m chart): BB = SMA20(close) +/- 2 x stdev20(close); KC = SMA20(close) +/- 1.5 x ATR20 (mean true
range over 20 bars). Squeeze on = BB upper < KC upper and BB lower > KC lower.
  1. fromOpen > +0.3% and spy_fo > 0 at the trigger.
  2. The squeeze was on for >= 6 consecutive bars immediately before the trigger, all of them closing 12:00-14:30
     (the run is counted only over today's bars closing >= 12:00).
  3. Squeeze fires on this bar: BB upper > KC upper; close > SMA20 (5m); emaDiff > 0; close > VWAP (vwapDistPct > 0).
  4. dist_hod_atr >= 0.30 at the trigger (mid-range, room to the HOD).
  Entry: bar close, 12:30-14:45. GEOM S: stop = the lowest low of the squeeze run - 0.05 x atr_d; target = the HOD
  (limit); skip if (HOD - entry) < 1 x (entry - stop). Else flat 15:55.
No tweak used; all values as stated (KC uses a 20-bar ATR mean, Carter's default length). No tuning on valid.
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1445)
CONTEXT = ["spy_fo"]
LAYERS = ["fromOpen > 0.3 and spy_fo > 0", "5m BB(20,2) inside KC(20,1.5 ATR) for >= 6 bars within 12:00-14:30",
          "fires: BB upper > KC upper, close > SMA20, emaDiff > 0, close > VWAP", "dist_hod_atr >= 0.30",
          "stop squeeze low - 0.05 ATR, target HOD, skip < 1R", "12:30-14:45 ET"]
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


def _lag(x, k, n=1):
    """x from n bars earlier in the same group (NaN across a group boundary)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each group."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _gfun(x, k, how):
    """Inclusive running cummax / cummin within each group."""
    s = pd.Series(np.asarray(x, float))
    g = s.groupby(k)
    return (g.cummax() if how == "max" else g.cummin()).to_numpy(float)


def _lib():
    try:
        import lib
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "research" / "history2y"))
        import lib
    return lib


def _daily():
    """Open-history daily table (lib.daily() never returns the locked block). Cached."""
    if "d" not in _DC:
        try:
            d = _lib().daily()[["symbol", "date", "open", "high", "low", "close"]].copy()
            d["symbol"] = d["symbol"].astype(str)
            d["date"] = pd.to_datetime(d["date"])
            _DC["d"] = d.sort_values(["symbol", "date"]).reset_index(drop=True)
        except Exception:
            _DC["d"] = None
    return _DC["d"]


def _segment(dates):
    """Contiguous-segment id per row: a new segment after any calendar gap > 7 days (the locked-block hole)."""
    gap = dates.diff().dt.days
    return (gap.isna() | (gap > 7)).cumsum()


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


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, dtype=bool)
    if not n or "spy_fo" not in df:
        return z
    k = _key(df)
    ks = pd.factorize(df["symbol"].astype(str).to_numpy())[0]
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    pc = _lag(c, ks)
    tr = np.fmax(h - l, np.fmax(np.abs(h - pc), np.abs(l - pc)))
    cs = pd.Series(c)
    g = cs.groupby(ks)
    sma = g.transform(lambda s: s.rolling(20, min_periods=20).mean()).to_numpy(float)
    sd = g.transform(lambda s: s.rolling(20, min_periods=20).std(ddof=0)).to_numpy(float)
    atr5 = pd.Series(tr).groupby(ks).transform(lambda s: s.rolling(20, min_periods=20).mean()).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        bbu, bbl = sma + 2 * sd, sma - 2 * sd
        kcu, kcl = sma + 1.5 * atr5, sma - 1.5 * atr5
        sq = (bbu < kcu) & (bbl > kcl) & (tod >= 1200) & (tod <= 1430)
        # consecutive run length of squeeze bars within today (reset when sq is False)
        sqf = sq.astype(float)
        grp = np.cumsum((~sq) | _start(k))              # new block at every non-squeeze bar or new symbol-day
        run = pd.Series(sqf).groupby(grp).cumsum().to_numpy(float)
        runlow = pd.Series(np.where(sq, l, np.nan)).groupby(grp).cummin().to_numpy(float)
        prun = _lag(run, k)
        plow = _lag(runlow, k)
        hod = c + _f(df, "dist_hod_atr") * atr
        m = (_f(df, "fromOpen") > 0.3) & (_f(df, "spy_fo") > 0)
        m &= prun >= 6
        m &= bbu > kcu
        m &= c > sma
        m &= _f(df, "emaDiff") > 0
        m &= _f(df, "vwapDistPct") > 0
        m &= _f(df, "dist_hod_atr") >= 0.30
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = plow - 0.05 * atr
        m &= (stop < c) & ((hod - c) >= (c - stop))
    _ST[id(df)] = (stop, hod)
    return np.asarray(m, dtype=bool)
