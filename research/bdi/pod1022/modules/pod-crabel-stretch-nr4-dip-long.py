"""pod-crabel-stretch-nr4-dip-long - Crabel stretch dip buy on NR4 / inside days in a daily uptrend (LONG).

Source: Toby Crabel, 'Day Trading with Short Term Price Patterns and Opening Range Breakout' (1990): stretch = the
10-day average of the smaller of (high - open) and (open - low); NR4 and inside-day range-contraction patterns. Book,
no URL was checked this round.
URL: (none)

VARIANT of bdi1013-limit945-dip-entry (failed: a fixed % dip from the open at 09:45), nr7-orb (the breakout side) and
pod-crabel-stretch-open-reclaim-long (fixed 0.30 ATR proxy for stretch, reclaim of the OPEN, volume >= 1.2, any day).
Stated change: the dip threshold is Crabel's true stretch from the daily table, the gate is NR4 / inside day plus a
daily uptrend, and the trigger is a half-stretch reversal confirmation, not a blind limit order.

Rules (plain English, LONG). Daily values from the completed open-history daily table only (D-1 and earlier; windows
never span a calendar gap > 7 days, i.e. the locked-block hole). Derived: open = close / (1 + fromOpen / 100);
LOD = close - dist_lod_atr x atr_d.
  1. D-1 is NR4 (its high-low range is the smallest of D-1..D-4) or an inside day (H(D-1) <= H(D-2) and
     L(D-1) >= L(D-2)), and the D-1 close is > the daily SMA20 (D-20..D-1).
  2. |gap| <= 0.5%.
  3. Touch: a bar closing 09:50-12:00 has low <= open - 1.0 x stretch (stretch = mean over D-10..D-1 of
     min(H - O, O - L)).
  4. Trigger: a later bar (after the first touch bar) that closes back above open - 0.5 x stretch with flow3 > 0, or
     with the first touch bar's lower_wick >= 0.4 instead of flow3 > 0. The first such bar is taken.
  Entry: that close, bar close 09:55-12:30 (pre-declared: the idea gives no entry cut-off; the trigger may follow a
  late touch, so 30 minutes after the touch window). GEOM S: stop = LOD - 0.05 x atr_d; target = open + 1.0 x
  stretch (limit); else flat 15:55.
No tuning; no tweak beyond the stated entry cut-off. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (955, 1230)
CONTEXT = []
LAYERS = ["D-1 NR4 or inside day, D-1 close > daily SMA20", "|gap| <= 0.5", "low <= open - stretch 09:50-12:00",
          "close back above open - 0.5 stretch with flow3 > 0 (or touch-bar lower_wick >= 0.4)",
          "stop LOD - 0.05 ATR, target open + stretch", "09:55-12:30 ET"]
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


def _table():
    if "c" in _DC:
        return _DC["c"]
    d = _daily()
    if d is None:
        _DC["c"] = None
        return None
    d = d.copy()
    gapd = d.groupby("symbol")["date"].diff().dt.days
    seg = ((gapd.isna()) | (gapd > 7)).cumsum()             # new segment per symbol start or calendar hole
    g = d.groupby(seg.to_numpy())
    rng = d["high"] - d["low"]
    d["nr4"] = rng <= pd.Series(rng.to_numpy()).groupby(seg.to_numpy()).transform(
        lambda x: x.rolling(4, min_periods=4).min()).to_numpy()
    ph, pl = g["high"].shift(1), g["low"].shift(1)
    d["inside"] = (d["high"] <= ph) & (d["low"] >= pl)
    d["sma20"] = g["close"].transform(lambda x: x.rolling(20, min_periods=20).mean())
    mn = np.minimum(d["high"] - d["open"], d["open"] - d["low"])
    d["stretch"] = pd.Series(mn.to_numpy()).groupby(seg.to_numpy()).transform(
        lambda x: x.rolling(10, min_periods=10).mean()).to_numpy()
    d["ok"] = (d["nr4"] | d["inside"]) & (d["close"] > d["sma20"])
    # shift to "today": D-1 values keyed by the next session's date, same segment only
    nxt = g["date"].shift(-1)
    t = pd.DataFrame({"symbol": d["symbol"], "date": nxt, "ok": d["ok"], "stretch": d["stretch"]}).dropna(subset=["date"])
    t = t[t["ok"] & np.isfinite(t["stretch"])]
    out = {(s, dt.date().isoformat()): st for s, dt, st in zip(t["symbol"], t["date"], t["stretch"])}
    _DC["c"] = out
    return out


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, dtype=bool)
    if not n:
        return z
    tb = _table()
    if not tb:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    sym = df["symbol"].astype(str).to_numpy()
    ds = df["date"].astype(str).to_numpy()
    stretch = np.array([tb.get((a, b), np.nan) for a, b in zip(sym, ds)], float)
    c, l, atr, fo = _f(df, "close"), _f(df, "low"), _f(df, "atr_d"), _f(df, "fromOpen")
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + fo / 100)
        lod = c - _f(df, "dist_lod_atr") * atr
        touch = (tod >= 950) & (tod <= 1200) & (l <= opn - 1.0 * stretch)
        ftouch = touch & ((_gcum(touch.astype(float), k) - touch) == 0)
        idx = np.arange(n, dtype=float)
        tidx = pd.Series(np.where(ftouch, idx, np.nan)).groupby(k).ffill().to_numpy(float)
        lw_t = np.where(np.isfinite(tidx), _f(df, "lower_wick")[np.nan_to_num(tidx).astype(np.int64)], np.nan)
        m = np.isfinite(stretch) & (stretch > 0)
        m &= np.abs(_f(df, "gap")) <= 0.5
        m &= np.isfinite(tidx) & (idx > tidx)
        m &= c > opn - 0.5 * stretch
        m &= (_f(df, "flow3") > 0) | (lw_t >= 0.4)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * atr
        tgt = opn + 1.0 * stretch
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
