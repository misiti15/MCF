"""pod-breadth-thrust-midday-index-long-live - LIVE copy of
research/bdi/pod1022/modules/pod-breadth-thrust-midday-index-long.py (Setup Generator observation setup, owner
2026-10-23). The research file stays unchanged.

Live adaptation (one change, no rule change): the (date, tod) breadth / qqq_vwap / spy_fo table uses only bars closing
at or after 09:50, as the scored history frames did (they start at the 09:50 bar). The live LabStrategy frame also
carries the 09:35-09:45 bars and their context values, which would otherwise enter the 6-bar breadth minimum and the
day's running spy_fo minimum. On the history frames this filter is a no-op, so the re-score is identical.
Live, the context comes from the runner (`context: [breadth, qqq_vwap, spy_fo]`); breadth there is over the polled
universe, in the history over the lab universe. The mask reads only the symbol's own rows (the market-wide columns
are the same on every row), so it works on one symbol's frame.

ORIGINAL DOCSTRING:
pod-breadth-thrust-midday-index-long - Intraday breadth thrust: the universe swings from washed out to broad
strength within 30 minutes; buy the index ETFs (LONG).

Source: Zweig breadth-thrust concept (Martin Zweig, 'Winning on Wall Street', 1986) applied intraday, a breadth topic in
systematic-trader interviews. NOT verified against a specific episode (web blocked this run).
URL: https://en.wikipedia.org/wiki/Breadth_thrust (concept reference; no episode verified)

VARIANT of pod-breadth-trendday-index-pullback-long, which buys a pullback on an already established breadth trend
day. Stated change: the trigger is the breadth swing itself, out of a washed-out state, so it targets reversal and
chop days.

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM, DIA. breadth = share of the universe above its own VWAP.
  1. Bar close 10:00-14:00.
  2. min(breadth) over the previous 6 bars of the same date <= 0.30 (computed on the (date, tod) breadth series; the
     history frames start at 09:50, so early in the day fewer than 6 earlier bars exist and those that exist are used).
  3. Current breadth >= 0.60.
  4. qqq_vwap > 0 (QQQ above its session VWAP).
  5. spy_fo > the day's earlier running minimum of spy_fo (bars before this one) + 0.30.
  Fire once per day: only the first (date, tod) where 2-5 all hold; each ETF enters on that bar.
  Entry: that bar's close. GEOM holdtr: 1R stop (R = 0.25 x atr_d), a 1R trail once +1R, flat 15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "holdtr"
WINDOW = (1000, 1400)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = ["breadth", "qqq_vwap", "spy_fo"]
LAYERS = ["SPY/QQQ/IWM/DIA", "min breadth previous 6 bars <= 0.30", "breadth >= 0.60", "qqq_vwap > 0",
          "spy_fo > earlier day min + 0.30", "first such bar of the date", "holdtr", "10:00-14:00 ET"]

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
    return t[t["tod"] >= 950].reset_index(drop=True)       # LIVE: as the history frames (start at the 09:50 bar)


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
    if not len(df) or not all(c in df for c in ("breadth", "qqq_vwap", "spy_fo")):
        return z
    with np.errstate(invalid="ignore"):   # LIVE speed-up, same output: a fire needs breadth <= 0.30 on an earlier
        _b, _t = _f(df, "breadth"), df["tod"].to_numpy(np.int64) >= 950   # bar and >= 0.60 on the fire bar (09:50+)
        if not (np.any((_b <= 0.30) & _t) and np.any((_b >= 0.60) & _t)):
            return z
    df = _ident(df)
    t = _date_table(df, "breadth")
    if not len(t):
        return z
    sub = df[["date", "tod", "qqq_vwap", "spy_fo"]].copy()
    sub["date"] = sub["date"].astype(str)
    sub = sub.drop_duplicates(["date", "tod"]).set_index(["date", "tod"])
    t = t.join(sub, on=["date", "tod"])
    g = t.groupby("date")
    with np.errstate(invalid="ignore"):
        t["bmin6"] = g["v"].transform(lambda x: x.shift(1).rolling(6, min_periods=1).min())
        t["sfo_min"] = g["spy_fo"].transform(lambda x: x.shift(1).cummin())
        ok = ((t["bmin6"] <= 0.30) & (t["v"] >= 0.60) & (t["qqq_vwap"] > 0)
              & (t["spy_fo"] > t["sfo_min"] + 0.30)
              & (t["tod"] >= WINDOW[0]) & (t["tod"] <= WINDOW[1]))
    t["ok"] = ok.astype(float)
    prior = t.groupby("date")["ok"].cumsum() - t["ok"]
    t["fire"] = ((t["ok"] > 0) & (prior == 0)).astype(float)
    fire = _map_back(df, t, ["fire"])["fire"]
    tod = df["tod"].to_numpy(np.int64)
    sym = df["symbol"].astype(str).to_numpy()
    # LIVE: the one-symbol live frame has no symbol column (_ident sets "_"); the YAML `symbols:` list restricts there
    m = (fire == 1) & (np.isin(sym, SYMBOLS) | (sym == "_"))
    m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
