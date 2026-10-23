"""pod-cal-turnaround-tuesday-index-reclaim-long - Turnaround Tuesday intraday: after a down Monday, buy Tuesday's VWAP
reclaim in index and sector ETFs, hold to the close (LONG).

Source: the well-known 'Turnaround Tuesday' weekday effect (Connors / Alvarez-type ETF studies; a Better System Trader
guest staple). NOT verified against a specific episode (web blocked this run).
URL: https://alvarezquanttrading.com (no specific episode verified)

VARIANT of backlog sw-w3-calendar-near (unconditional daily day-of-week tests on index ETFs, close to close, failed).
Stated changes: (a) the entry is conditioned on Monday's SPY decline; (b) the trigger is an intraday VWAP reclaim;
(c) a hold-to-close exit.

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM, DIA plus the sector SPDRs XLK, XLF, XLI, XLY, XLV, XLP, XLU, XLE,
XLB, XLC, XLRE.
  Date gate: today is a Tuesday whose previous session was Monday (a Tuesday after a Monday holiday is excluded), AND
  SPY's Monday close-to-close return (Monday close vs the session before it, from the completed daily closes) is
  <= -0.75%. A return never spans a calendar gap > 7 days (the locked block is never read).
  1. Bar close 10:00-12:00.
  2. vwapReclaim == 1 (close above VWAP, at or below it 3 bars ago).
  3. spy_fo >= -0.20.
  4. rsi (14) between 45 and 65.
  Entry: that bar's close. GEOM hold: 1R stop (R = 0.25 x atr_d), no target, flat 15:55.
No tweak used; all values as stated. No tuning on valid. Few events (about 10-15 qualifying Tuesdays a year), judged
pooled across the ETFs. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "long"
GEOM = "hold"
WINDOW = (1000, 1200)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLI", "XLY", "XLV", "XLP", "XLU", "XLE", "XLB", "XLC", "XLRE"]
CONTEXT = ["spy_fo"]
LAYERS = ["Tuesday after a Monday session with SPY Monday c2c <= -0.75%", "vwapReclaim == 1", "spy_fo >= -0.20",
          "rsi 45-65", "hold 1R stop, flat 15:55", "10:00-12:00 ET"]

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


def _first(cond, k):
    """True only on the first True row of each symbol-day."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _date_table(df, col):
    """One row per (date, tod) with the market-wide column `col` (same value for every symbol), sorted."""
    t = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                      "v": _f(df, col)})
    t = t.dropna(subset=["v"]).drop_duplicates(["date", "tod"]).sort_values(["date", "tod"]).reset_index(drop=True)
    return t


def _map_back(df, t, cols):
    """Map (date, tod) table columns back to the rows of df."""
    idx = pd.MultiIndex.from_arrays([t["date"].to_numpy(), t["tod"].to_numpy()])
    q = pd.MultiIndex.from_arrays([df["date"].astype(str).to_numpy(), df["tod"].to_numpy(np.int64)])
    return {c: pd.Series(t[c].to_numpy(float), index=idx).reindex(q).to_numpy(float) for c in cols}


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


def _gate_dates():
    """Set of Tuesday dates (str) whose previous SPY session was Monday with a c2c return <= -0.75%."""
    if "g" in _DC:
        return _DC["g"]
    try:
        d = _lib().daily()
    except Exception:
        _DC["g"] = None
        return None
    s = d[d["symbol"].astype(str) == "SPY"][["date", "close"]].copy()
    s["date"] = pd.to_datetime(s["date"])
    s = s.sort_values("date").reset_index(drop=True)
    gap = (s["date"] - s["date"].shift()).dt.days
    ret = (s["close"] / s["close"].shift() - 1) * 100
    ret[gap > 7] = np.nan                                   # never span the locked block
    out = set()
    for i in range(1, len(s)):
        dt, pdt = s["date"].iloc[i], s["date"].iloc[i - 1]
        if dt.weekday() == 1 and pdt.weekday() == 0 and (dt - pdt).days == 1 and ret.iloc[i - 1] <= -0.75:
            out.add(dt.date().isoformat())
    _DC["g"] = out
    return out


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df:
        return z
    gd = _gate_dates()
    if not gd:
        return z
    tod = df["tod"].to_numpy(np.int64)
    rsi = _f(df, "rsi")
    with np.errstate(invalid="ignore"):
        m = np.isin(df["date"].astype(str).to_numpy(), list(gd))
        m &= np.isin(df["symbol"].astype(str).to_numpy(), SYMBOLS)
        m &= _f(df, "vwapReclaim") == 1
        m &= _f(df, "spy_fo") >= -0.20
        m &= (rsi >= 45) & (rsi <= 65)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
