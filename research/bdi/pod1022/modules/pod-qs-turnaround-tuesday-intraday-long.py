"""pod-qs-turnaround-tuesday-intraday-long - Turnaround Tuesday, intraday: index ETF VWAP reclaim on the Tuesday after a down Monday (LONG).
THIS FILE: the main config, GEOM S (stop LOD so far - 0.05 x atr_d, hold to 15:55).

Source: Quantified Strategies, 'Turnaround Tuesday' (daily backtest: buy after a down Monday), translated to an
intraday entry. Written from memory, URL not re-checked this round.
URL: https://www.quantifiedstrategies.com/turnaround-tuesday/

VARIANT of the CWT26 daily day-of-week / calendar holds and of Reddit R02 VWAP reclaim (failed). Stated change: a
calendar gate plus a prior-day-down gate, held intraday only. NOTE: very close to pod-cal-turnaround-tuesday-index-
reclaim-long (already in this pod; SPY Monday <= -0.75%, 15 ETFs, rsi 45-65, hold). Differences: each ETF's own
Monday return at -0.5%, a Tuesday gap band, a required morning dip below VWAP, and an LOD structural stop. The
scorer's overlap check decides whether it is a copy.

Rules (plain English, LONG). SYMBOLS SPY, QQQ, IWM, DIA.
  1. Today is a Tuesday and the previous session was Monday (a Tuesday after a Monday holiday is excluded).
  2. Monday down: that ETF's Monday close vs its prior close <= -0.5%. Deviation: Monday's completed DAILY close is
     used (research/history2y daily table), not its 15:00 bar, because Monday can sit in the previous month's frame.
     A return never spans a calendar gap > 7 days (the locked block is never read).
  3. Tuesday gap between -1.0% and +0.3%.
  4. Morning dip: some bar closing 09:50-10:30, at or before the trigger, had fromOpen <= -0.2% and vwapDistPct < 0.
  5. Trigger in 10:00-11:30: vwapReclaim == +1 (close back above session VWAP) and close > previous bar's close.
  Entry: the trigger close. Exit: see THIS FILE above; no target (QS exits at the close).
No tweak used; all values as stated. No tuning on valid. Small sample (about 90 Tuesdays x 4 ETFs), report n.
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = []
LAYERS = ["SPY/QQQ/IWM/DIA", "Tuesday after Monday", "own Monday c2c <= -0.5%", "gap -1.0..+0.3%",
          "dip 09:50-10:30: fromOpen <= -0.2 and below VWAP", "vwapReclaim == 1 and close > prior close", "10:00-11:30 ET"]

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


def _gacc(x, k, fn):
    """Inclusive running max / min (fn = np.fmax / np.fmin) within each symbol-day, ignoring NaN."""
    s = pd.Series(np.asarray(x, float))
    g = s.groupby(k)
    return (g.cummax() if fn is np.fmax else g.cummin()).to_numpy(float)


def _first(cond, k):
    """True only on the first True row of each symbol-day."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _sym_ctx(df, sym, x):
    """Column x of symbol `sym` at the same (date, tod) as each row (NaN when that symbol's bar is missing)."""
    s = df["symbol"].astype(str).to_numpy()
    sel = s == sym
    if not sel.any():
        return np.full(len(df), np.nan)
    d = df["date"].astype(str).to_numpy()
    t = df["tod"].to_numpy(np.int64)
    ser = pd.Series(np.asarray(x, float)[sel], index=pd.MultiIndex.from_arrays([d[sel], t[sel]]))
    ser = ser[~ser.index.duplicated()]
    return ser.reindex(pd.MultiIndex.from_arrays([d, t])).to_numpy(float)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def _lib():
    try:
        import lib
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "research" / "history2y"))
        import lib
    return lib


def _gate_keys():
    """Set of 'SYMBOL|YYYY-MM-DD' Tuesdays whose previous session was a Monday with that symbol's c2c <= -0.5%."""
    if "g" in _DC:
        return _DC["g"]
    try:
        d = _lib().daily()
    except Exception:
        _DC["g"] = None
        return None
    out = set()
    d = d[d["symbol"].astype(str).isin(SYMBOLS)][["symbol", "date", "close"]].copy()
    d["date"] = pd.to_datetime(d["date"])
    for sym, s in d.groupby("symbol"):
        s = s.sort_values("date").reset_index(drop=True)
        gapd = (s["date"] - s["date"].shift()).dt.days
        ret = (s["close"] / s["close"].shift() - 1) * 100
        ret[gapd > 7] = np.nan
        for i in range(1, len(s)):
            dt, pdt = s["date"].iloc[i], s["date"].iloc[i - 1]
            if dt.weekday() == 1 and pdt.weekday() == 0 and (dt - pdt).days == 1 and ret.iloc[i - 1] <= -0.5:
                out.add(f"{sym}|{dt.date().isoformat()}")
    _DC["g"] = out
    return out


def stop_price(f, i):
    return _stash_get(f, i, 0)


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    gk = _gate_keys()
    if not gk:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    keys = df["symbol"].astype(str).to_numpy().astype(object) + "|" + df["date"].astype(str).to_numpy().astype(object)
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - _f(df, "dist_lod_atr") * atr
        gap = _f(df, "gap")
        dip = ((tod >= 950) & (tod <= 1030) & (_f(df, "fromOpen") <= -0.2) & (_f(df, "vwapDistPct") < 0)).astype(float)
        had_dip = _gcum(dip, k) > 0
        m = np.isin(keys, list(gk))
        m &= (gap >= -1.0) & (gap <= 0.3)
        m &= had_dip
        m &= (_f(df, "vwapReclaim") == 1) & (c > _lag(c, k))
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * atr
    _ST[id(df)] = (stop,)
    return np.asarray(m, dtype=bool)
