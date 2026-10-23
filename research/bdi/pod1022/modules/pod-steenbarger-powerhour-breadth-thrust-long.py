"""pod-steenbarger-powerhour-breadth-thrust-long - Down-day power-hour short covering: a breadth thrust off a late low
(LONG).

Source: Brett Steenbarger, TraderFeed blog (intraday NYSE TICK / breadth thrusts after one-sided selling). The URL was
not re-checked this round.
URL: https://traderfeed.blogspot.com/

VARIANT of pod-raschke-blindfold-breadth-div (breadth DIVERGENCE at a second swing low, 10:30-15:00),
pod-edgeful-powerhour-containment-fade (QUIET days, LOD approach) and pod-raschke-trend-day-last-hour-long (UP trend
days). Stated change: down days only, the trigger is a breadth THRUST off its afternoon low (not a divergence), and the
window is the power hour.

Rules (plain English, LONG). Derived: LOD = close - dist_lod_atr x atr_d (running low of day); VWAP =
close / (1 + vwapDistPct / 100). Breadth = context `breadth` (share of the universe above its own VWAP), standing in
for NYSE TICK / breadth.
  1. spy_fo at the 14:30 bar <= -0.6%, and SPY's D-1 close is > its daily SMA50 (50 completed open-history sessions,
     never spanning the locked-block hole; no trade until 50 exist).
  2. The symbol's LOD was set by a bar closing 13:30-14:45 (the last bar whose low made a new low of day), and that
     bar is at least 4 bars back (no new LOD in the last 4 bars: bars i-3..i made none).
  3. breadth now >= (its minimum over bars closing 13:00..now) + 0.15.
  4. close > the highest high of the previous 6 bars, and vwapDistPct <= -0.3 (still >= 0.3% below VWAP).
  Entry: bar close 14:45-15:00 (the idea says 14:45-15:30; the harness frames end at 15:00, so 15:05-15:30 is cut).
  GEOM S: stop = LOD - 0.05 x atr_d; target = VWAP at entry (limit); else flat 15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1445, 1500)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["spy_fo(14:30) <= -0.6 and SPY D-1 close > SMA50", "LOD set 13:30-14:45, none in the last 4 bars",
          "breadth >= min since 13:00 + 0.15", "close > 6-bar high, vwapDistPct <= -0.3",
          "stop LOD - 0.05 ATR, target VWAP", "14:45-15:00 ET"]
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


def _spy_ok():
    if "s50" in _DC:
        return _DC["s50"]
    d = _daily()
    if d is None:
        _DC["s50"] = None
        return None
    s = d[d["symbol"] == "SPY"][["date", "close"]].sort_values("date").reset_index(drop=True)
    seg = _segment(s["date"])
    sma = s.groupby(seg.to_numpy())["close"].transform(lambda x: x.rolling(50, min_periods=50).mean())
    ok_prev = (s["close"] > sma)
    seg_next = seg.shift(-1)
    out = set()
    for i in range(len(s) - 1):                     # today = row i+1, D-1 = row i, same segment
        if bool(ok_prev.iloc[i]) and seg.iloc[i] == seg_next.iloc[i]:
            out.add(s["date"].iloc[i + 1].date().isoformat())
    _DC["s50"] = out
    return out


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, dtype=bool)
    if not n or "spy_fo" not in df or "breadth" not in df:
        return z
    ok = _spy_ok()
    if not ok:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    ds = df["date"].astype(str).to_numpy()
    c, h, l, atr, vd = (_f(df, x) for x in ("close", "high", "low", "atr_d", "vwapDistPct"))
    # spy_fo at the 14:30 bar, per date
    t = pd.DataFrame({"d": ds, "tod": tod, "v": _f(df, "spy_fo")})
    t = t[(t["tod"] == 1430) & np.isfinite(t["v"])].drop_duplicates("d")
    fo1430 = pd.Series(t["v"].to_numpy(), index=t["d"].to_numpy()).reindex(ds).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - _f(df, "dist_lod_atr") * atr
        plod = _lag(lod, k)
        newlow = (l <= lod + 1e-9) & ~(plod <= l + 1e-9)       # this bar's low made (or equalled first) a new LOD
        newlow |= np.isnan(plod) & (l <= lod + 1e-9)
        idx = np.arange(n, dtype=float)
        last_nl = pd.Series(np.where(newlow, idx, np.nan)).groupby(k).ffill().to_numpy(float)
        last_tod = np.where(np.isfinite(last_nl), tod[np.nan_to_num(last_nl).astype(np.int64)], -1)
        br = _f(df, "breadth")
        brmin = _gfun(np.where(tod >= 1300, br, np.inf), k, "min")
        hh6 = np.fmax.reduce([_lag(h, k, j) for j in range(1, 7)])
        m = np.isin(ds, list(ok))
        m &= fo1430 <= -0.6
        m &= (last_tod >= 1330) & (last_tod <= 1445) & ((idx - last_nl) >= 4)
        m &= np.isfinite(brmin) & (br >= brmin + 0.15)
        m &= c > hh6
        m &= vd <= -0.3
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * atr
        vw = c / (1 + vd / 100)
        m &= (stop < c) & (vw > c)
    _ST[id(df)] = (stop, vw)
    return np.asarray(m, dtype=bool)
