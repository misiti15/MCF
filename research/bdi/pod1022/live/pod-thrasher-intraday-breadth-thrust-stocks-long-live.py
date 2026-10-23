"""pod-thrasher-intraday-breadth-thrust-stocks-long-live - LIVE copy of
research/bdi/pod1022/modules/pod-thrasher-intraday-breadth-thrust-stocks-long.py (Setup Generator observation setup,
owner 2026-10-23). The research file stays unchanged.

Live adaptation (one change, no rule change): the breadth / spy_fo look-backs use only bars closing at or after 09:50,
as the scored history frames did (they start at the 09:50 bar). The live LabStrategy frame also carries the
09:35-09:45 bars and their context values, which would otherwise enter the 9-bar breadth minimum and the 10-bar
spy_fo minimum before 10:40. On the history frames this filter is a no-op, so the re-score is identical.
Live, the context comes from the runner (`context: [breadth, spy_fo]`); breadth there is over the polled universe,
in the history over the lab universe.

ORIGINAL DOCSTRING:
pod-thrasher-intraday-breadth-thrust-stocks-long - Intraday breadth thrust: breadth goes from <= 30% to >= 70% within 45 minutes (LONG).
THIS FILE: the source's secondary run - stocks with adv20 >= $500M and fromOpen - spy_fo >= 0 at the thrust bar, entry on the thrust bar.

Source: Andrew Thrasher (Thrasher Analytics; podcast guest on breadth thrusts) and Zweig / Deemer breadth-thrust
concepts, scaled down to the session. Written from memory, URL not re-checked.
URL: https://www.thrasheranalytics.com/

VARIANT of the LD breadth-turn index dips (LD1-LD8) and the bdi-rg breadth gates. Stated change: the trigger is the
SIZE and SPEED of the breadth move (a full 0.30 -> 0.70 thrust in <= 9 bars), entered on thrust confirmation, not on
a dip. NOTE: close to pod-breadth-thrust-midday-index-long (already in this pod: min breadth of 6 prior bars <= 0.30,
breadth >= 0.60, spy_fo +0.30 off the day low, qqq_vwap > 0, holdtr, SPY/QQQ/IWM/DIA). Here: a 9-bar look-back,
>= 0.70, +0.50 pp, the ETF's own VWAP, no DIA. The scorer's overlap check decides whether it is a copy.

Rules (plain English, LONG). breadth = share of the universe above its own VWAP. Decision bar i, bar close
10:15-14:00; look-backs are same-day bars of the (date, tod) breadth / spy_fo series (frames start at 09:50,
  so before 10:40 fewer than 9 earlier bars exist and those that exist are used).
  1. min(breadth over bars i-9..i-1) <= 0.30.
  2. breadth[i] >= 0.70; bar i must be the FIRST bar of the day where 1 and 2 both hold.
  3. spy_fo[i] - min(spy_fo over i-9..i) >= +0.5 percentage points.
  4. The symbol's vwapDistPct > 0 at bar i.
  Entry: close of bar i (config B: see above). GEOM holdtr: 1R stop (R = 0.25 x atr_d), a 1R trail once +1R, flat
  15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "holdtr"
WINDOW = (1015, 1400)
MIN_ADV = 500e6
CFG = "C"
CONTEXT = ["breadth", "spy_fo"]
LAYERS = ["min breadth prior 9 bars <= 0.30", "breadth >= 0.70 (first such bar of the day)",
          "spy_fo up >= 0.5 pp off its 10-bar min", "vwapDistPct > 0", "holdtr", "10:15-14:00 ET"]

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


def _thrust(df):
    """Per row: 1.0 on the date's thrust bar (rules 1-3), else 0 / NaN. Computed on the (date, tod) series."""
    t = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                      "b": _f(df, "breadth"), "s": _f(df, "spy_fo")})
    t = t.dropna(subset=["b"]).drop_duplicates(["date", "tod"]).sort_values(["date", "tod"]).reset_index(drop=True)
    t = t[t["tod"] >= 950].reset_index(drop=True)          # LIVE: as the history frames (start at the 09:50 bar)
    g = t.groupby("date")
    t["bmin9"] = g["b"].transform(lambda x: x.shift(1).rolling(9, min_periods=1).min())
    t["smin10"] = g["s"].transform(lambda x: x.rolling(10, min_periods=1).min())
    with np.errstate(invalid="ignore"):
        c12 = ((t["bmin9"] <= 0.30) & (t["b"] >= 0.70)).astype(float)
    prior = c12.groupby(t["date"]).cumsum() - c12
    first12 = (c12 > 0) & (prior == 0)
    t["fire"] = (first12 & ((t["s"] - t["smin10"]) >= 0.5)).astype(float)
    idx = pd.MultiIndex.from_arrays([t["date"].to_numpy(), t["tod"].to_numpy()])
    q = pd.MultiIndex.from_arrays([df["date"].astype(str).to_numpy(), df["tod"].to_numpy(np.int64)])
    return pd.Series(t["fire"].to_numpy(float), index=idx).reindex(q).to_numpy(float)


def _ident(df):
    """LIVE: the LabStrategy frame is one symbol-day indexed by bar start, without symbol / date columns; add them
    (one group) so the research code's symbol-day keys work unchanged. History frames already carry them."""
    if "symbol" in df and "date" in df:
        return df
    g = df.copy()
    if "symbol" not in g:
        g["symbol"] = "_"
    if "date" not in g:
        g["date"] = [str(x) for x in pd.DatetimeIndex(df.index).date]
    return g


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "breadth" not in df or "spy_fo" not in df:
        return z
    with np.errstate(invalid="ignore"):   # LIVE speed-up, same output: a fire needs breadth <= 0.30 on an earlier
        _b, _t = _f(df, "breadth"), df["tod"].to_numpy(np.int64) >= 950   # bar and >= 0.70 on the fire bar (09:50+)
        if not (np.any((_b <= 0.30) & _t) and np.any((_b >= 0.70) & _t)):
            return z
    df = _ident(df)
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l = _f(df, "close"), _f(df, "high"), _f(df, "low")
    fire = _thrust(df) == 1
    with np.errstate(invalid="ignore"):
        T = fire & (_f(df, "vwapDistPct") > 0) & (tod >= 1015) & (tod <= 1400)
        if CFG == "C":
            T &= (_f(df, "fromOpen") - _f(df, "spy_fo")) >= 0
        if CFG in ("A", "C"):
            m = T
        else:
            sym = df["symbol"].astype(str).to_numpy()
            ema9 = pd.Series(c).groupby(sym).transform(lambda x: x.ewm(span=9, adjust=False).mean()).to_numpy(float)
            tf = T.astype(float)
            after_t = (_gcum(tf, k) - tf) > 0
            pb = after_t & (l <= ema9) & (_f(df, "breadth") >= 0.55)
            pbf = _first(pb, k)
            pbh = pd.Series(np.where(pbf, h, np.nan)).groupby(k).ffill().to_numpy(float)
            pf = pbf.astype(float)
            after_pb = (_gcum(pf, k) - pf) > 0
            m = after_pb & (c > pbh)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
