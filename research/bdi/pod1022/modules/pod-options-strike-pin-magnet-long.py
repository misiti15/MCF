"""pod-options-strike-pin-magnet-long - Option-strike pin: afternoon drift back up to the nearest major strike on quiet
days (LONG).

Source: Ni, Pearson & Poteshman (2005), 'Stock price clustering on option expiration dates', Journal of Financial
Economics 78(1); the dealer-gamma 'pinning' discussion on options day-trading shows (SpotGamma / tastylive). The URL
was not re-checked this round.
URL: https://doi.org/10.1016/j.jfineco.2004.08.005

VARIANT of pod-wt-flat-top-roundnum-long (buys a BREAK of a round number on momentum). Same round-number family, the
opposite logic: buy the MAGNET return to a strike that was already visited today, on a quiet day. Unlike
pod-cal-opex-friday-strike-pin-fade (opex Fridays only, oversold rsi5 <= 30, strike from the frame's grid), this one
runs every day, uses the index $1 strike grid, needs the strike to have traded earlier today and an rsi5 up-cross.

Rules (plain English, LONG). Derived: HOD/LOD = close +/- dist_hod_atr / dist_lod_atr x atr_d.
  Universe: SPY, QQQ, IWM, DIA (strike step $1) plus stocks priced >= $100 with adv20 >= $1B (strike step $5).
  1. Quiet day: day range so far (HOD - LOD) <= 0.8 x atr_d and |spy_fo| <= 0.4%.
  2. K = the nearest strike ABOVE the close (floor(close / step) x step + step). K - close is 0.10-0.30 x atr_d.
  3. The previous bar's HOD was >= K (price traded at or above K earlier today).
  4. rsi5 crosses up through 40 (previous bar < 40, this bar >= 40) and flow3 > 0.
  Window: bar close 13:30-15:00 (the idea says 13:30-15:15; the harness frames end at 15:00, so 15:05-15:15 is cut).
  Entry: bar close. GEOM S: stop = max(entry - 0.15 x atr_d, LOD) (the closer of the two); target = K (limit);
  else flat 15:55.
  Pre-declared split report: Fridays plus monthly-opex days vs other days, one configuration reported in both cuts
  (computed from the trades file by the batch runner, not by the scorer).
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1330, 1500)
MIN_ADV = 0
CONTEXT = ["spy_fo"]
INDEX = ["SPY", "QQQ", "IWM", "DIA"]
LAYERS = ["SPY/QQQ/IWM/DIA ($1 strikes) or price >= $100 and adv20 >= $1B ($5 strikes)",
          "day range <= 0.8 ATR and |spy_fo| <= 0.4", "strike K above, 0.10-0.30 ATR away, HOD already >= K",
          "rsi5 crosses up through 40, flow3 > 0", "stop max(entry - 0.15 ATR, LOD), target K", "13:30-15:00 ET"]
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
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    is_idx = np.isin(df["symbol"].astype(str).to_numpy(), INDEX)
    with np.errstate(invalid="ignore", divide="ignore"):
        big = (~is_idx) & (c >= 100) & (_f(df, "adv20") >= 1e9)
        step = np.where(is_idx, 1.0, np.where(big, 5.0, np.nan))
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        K = np.floor(c / step) * step + step
        m = is_idx | big
        m &= (hod - lod) <= 0.8 * atr
        m &= np.abs(_f(df, "spy_fo")) <= 0.4
        d = (K - c) / atr
        m &= (d >= 0.10) & (d <= 0.30)
        m &= _lag(hod, k) >= K
        r5 = _f(df, "rsi5")
        m &= (_lag(r5, k) < 40) & (r5 >= 40)
        m &= _f(df, "flow3") > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = np.maximum(c - 0.15 * atr, lod)
        m &= (stop < c) & (K > c)
    _ST[id(df)] = (stop, K)
    return np.asarray(m, dtype=bool)
