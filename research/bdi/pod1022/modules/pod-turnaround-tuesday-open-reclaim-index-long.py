"""pod-turnaround-tuesday-open-reclaim-index-long - Turnaround Tuesday: an index ETF reclaims today's open after a down
prior session (LONG).

Source: Quantified Strategies, 'Turnaround Tuesday' (Larry Williams-style day-of-week bias), a staple of index
day-trading shows. The URL was not re-checked this round.
URL: https://www.quantifiedstrategies.com/turnaround-tuesday/

VARIANT of pod-dalton-open-rejection-reverse-long (any day, needs a >= 0.4 ATR failed drive, target PDH),
R06 / wi-red-to-green (prior-close level, failed), sw-w3-calendar-near (DAILY day-of-week holds, failed) and
pod-cal-turnaround-tuesday-index-reclaim-long (Tuesday-after-Monday only, SPY's Monday return, VWAP reclaim with
rsi 45-65, 1R ATR stop). Stated change here: the second session of the week, the symbol's OWN prior-session drop, an
SMA200 bull filter, an early dip below the open, an open-AND-VWAP reclaim, a structural LOD stop held to the close.

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM, DIA. Derived: open = close / (1 + fromOpen / 100);
LOD = close - dist_lod_atr x atr_d.
  1. Today is the second session of its calendar week (normally Tuesday), from the SPY daily dates.
  2. The symbol's prior session closed down >= 0.75% close-to-close (completed daily closes; never across a calendar
     gap > 7 days), and SPY's D-1 close is > its daily SMA200.
     DATA LIMIT, stated substitution: the open daily table starts 2024-10-01 and the locked block (2024-11..2025-02) is
     never read, so a true 200-session SMA does not exist for most of the history. The SMA is the mean of the up-to-200
     most recent completed open-history SPY closes before today, and needs at least 60 of them (no trade before that).
  3. Earlier today, by the 10:45 bar, the low of day was <= open x (1 - 0.20%) (fromOpen reached <= -0.20%; the LOD
     includes the 09:30-09:45 bars).
  4. Trigger: the first bar closing 10:00-12:00 that closes above today's open (fromOpen > 0) AND above VWAP
     (vwapDistPct > 0), after the dip in 3.
  Entry: that close. GEOM S: stop = LOD - 0.05 x atr_d; no target; flat 15:55. One configuration (configurations
  tried: 1).
No tweak used. No tuning on valid. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1200)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = []
LAYERS = ["2nd session of the week", "own prior session c2c <= -0.75%", "SPY D-1 close > SMA200 (open-history proxy)",
          "LOD <= open - 0.20% by 10:45", "first close above open and VWAP 10:00-12:00",
          "stop LOD - 0.05 ATR, hold to 15:55"]
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



def _tables():
    if "t" in _DC:
        return _DC["t"]
    d = _daily()
    if d is None:
        _DC["t"] = None
        return None
    s = d[d["symbol"] == "SPY"][["date", "close"]].sort_values("date").reset_index(drop=True)
    # SMA200 proxy: mean of the up-to-200 previous completed closes, >= 60 of them
    sma = s["close"].rolling(200, min_periods=60).mean().shift(1)
    prevc = s["close"].shift(1)
    spy_ok = {dt.date().isoformat() for dt, a, b in zip(s["date"], prevc, sma) if np.isfinite(b) and a > b}
    iso = s["date"].dt.isocalendar()
    wk = iso["year"].astype(str) + "-" + iso["week"].astype(str)
    rank = s.groupby(wk.to_numpy()).cumcount() + 1
    # a week whose first days fall in the locked hole cannot be ranked: drop weeks touching a > 7-day gap
    seg = _segment(s["date"])
    wk_seg = pd.Series(seg.to_numpy()).groupby(wk.to_numpy()).transform("nunique").to_numpy()
    second = {dt.date().isoformat() for dt, r, ns in zip(s["date"], rank, wk_seg) if r == 2 and ns == 1}
    gate = spy_ok & second
    # each symbol's prior-session c2c return, keyed by today's date
    rows = {}
    for sym in SYMBOLS:
        x = d[d["symbol"] == sym].sort_values("date").reset_index(drop=True)
        gapd = x["date"].diff().dt.days
        ret = (x["close"] / x["close"].shift(1) - 1) * 100
        ret[gapd > 7] = np.nan
        pret = ret.shift(1)
        pgap = gapd                                 # today vs D-1 must also be contiguous
        for dt, r, gg in zip(x["date"], pret, pgap):
            if np.isfinite(r) and np.isfinite(gg) and gg <= 7:
                rows[(sym, dt.date().isoformat())] = r
    _DC["t"] = (gate, rows)
    return _DC["t"]


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, dtype=bool)
    if not n:
        return z
    t = _tables()
    if t is None:
        return z
    gate, rows = t
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    sym = df["symbol"].astype(str).to_numpy()
    ds = df["date"].astype(str).to_numpy()
    c, atr, fo = _f(df, "close"), _f(df, "atr_d"), _f(df, "fromOpen")
    pr = np.array([rows.get((a, b), np.nan) for a, b in zip(sym, ds)], float)
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + fo / 100)
        lod = c - _f(df, "dist_lod_atr") * atr
        dip = (tod <= 1045) & ((lod / opn - 1) * 100 <= -0.20)
        dipped = _gcum(dip.astype(float), k) > 0
        m = np.isin(ds, list(gate)) & np.isin(sym, SYMBOLS)
        m &= pr <= -0.75
        m &= dipped
        m &= (fo > 0) & (_f(df, "vwapDistPct") > 0)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * atr
        m &= stop < c
    _ST[id(df)] = (stop, np.full(n, np.nan))
    return np.asarray(m, dtype=bool)
