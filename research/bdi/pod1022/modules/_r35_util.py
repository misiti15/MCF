"""_r35_util - shared helpers for the pod r3_5 modules (Lou-Polk-Skouras intraday persistence / overnight-loser
rebound, Alvarez prior-day IBS and regime-classified ETF dips, Radge limit dip, Harris Monday-morning reclaim).
Not a setup (no SIDE / mask).

Point-in-time inputs (all causal):
  * daily values per (symbol, date D) as of D-1's close (lib.daily(), completed days only; the rule-19 locked block
    is not in it and every rolling series restarts after a > 7-day gap, so nothing bridges the locked block):
    20-session sums of open-to-close and of overnight (gap) returns over D-20..D-1, D-1 IBS, D-1 high / close,
    SMA50 / SMA100 of closes, close D-4, adv20 as of D-1.
  * cross-sectional ranks per date D computed only from those D-1 values.
  * SPY daily class as of D-1: 10-day efficiency ratio and 10-day realized vol vs the median of its prior 120
    available values (min 60; the gap-spanning return across the locked block is dropped, never read).
  * first trading session of the week (from the daily calendar; previous session in an earlier ISO week).
  * 09:35-09:45 closes for the ETF list from the head/tail table (research/bdi/cwt/test_b), never the locked block.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as C3  # noqa: E402

ETF15 = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "SMH", "XBI", "KRE"]
_MEM = {}
f, key, start, base, at_tod = C3.f, C3.key, C3.start, C3.base, C3.at_tod


def lag(x, k, n=1):
    return C3.lag(x, k, n)


def _daily():
    if "d" in _MEM:
        return _MEM["d"]
    d = C3.lib().daily()[["symbol", "date", "open", "high", "low", "close", "adv20"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    s = d["date"].astype(str)
    assert not ((s >= "2024-11-01") & (s <= "2025-02-28")).any(), "locked block in daily"
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    pc = c.groupby(g).shift(1)
    oc = c / o - 1.0
    gp = (o / pc - 1.0) * 100.0
    rng = (h - l).where(h > l)
    cur = {
        "oc20": oc.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).sum()),
        "gap20": gp.groupby(g).transform(lambda x: x.rolling(20, min_periods=20).sum()),
        "ibs": (c - l) / rng,
        "dh": h, "dc": c,
        "sma50": c.groupby(g).transform(lambda x: x.rolling(50, min_periods=50).mean()),
        "sma100": c.groupby(g).transform(lambda x: x.rolling(100, min_periods=100).mean()),
        "adv": d["adv20"],
    }
    out = pd.DataFrame({"symbol": d["symbol"], "date": s})
    for nm, v in cur.items():
        out[nm + "_1"] = v.groupby(g).shift(1)           # as of D-1 (row D)
    out["c_4"] = c.groupby(g).shift(4)                   # close of D-4
    _MEM["d"] = out
    return out


def daily_tab():
    """Daily table with cross-sectional ranks (per date, from D-1 values only)."""
    if "t" in _MEM:
        return _MEM["t"]
    d = _daily().copy()
    # LPS: 20d open-to-close sum, universe adv20 >= 50e6 (as of D-1)
    u1 = (d["adv_1"] >= 50e6) & d["oc20_1"].notna()
    d["oc20_pct"] = np.nan
    d.loc[u1, "oc20_pct"] = d[u1].groupby("date")["oc20_1"].rank(pct=True)
    # LPS overnight loser: 20d gap sum, universe ETF15 + adv20 >= 200e6
    u2 = (d["symbol"].isin(ETF15) | (d["adv_1"] >= 200e6)) & d["gap20_1"].notna()
    d["gap20_pct"] = np.nan
    d.loc[u2, "gap20_pct"] = d[u2].groupby("date")["gap20_1"].rank(pct=True)
    _MEM["t"] = d
    return d


def map_daily(df, k, cols):
    t = daily_tab()
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st],
                      "date": pd.Series(df["date"].to_numpy()[st]).astype(str).to_numpy()})
    m = u.merge(t[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == int(st.sum())
    idx = np.cumsum(st) - 1
    return {c: m[c].to_numpy(float)[idx] for c in cols}


def spy_class():
    """Per date D: SPY er10 and rv10 (as of D-1) and rv_med = median of the prior 120 available rv10 values (min 60,
    ending D-1). Returns a DataFrame (date, er10, rv10, rv_med, first_week)."""
    if "spy" in _MEM:
        return _MEM["spy"]
    d = C3.lib().daily()
    allday = sorted(set(d["date"].astype(str)))
    s = d[d["symbol"].astype(str) == "SPY"][["date", "close"]].copy()
    s["date"] = s["date"].astype(str)
    s = s.sort_values("date").reset_index(drop=True)
    dt = pd.to_datetime(s["date"])
    seg = ((dt - dt.shift()).dt.days > 7).cumsum()
    c = s["close"]
    dc = c.groupby(seg).diff()
    er = (c - c.groupby(seg).shift(10)).abs() / dc.abs().groupby(seg).transform(
        lambda x: x.rolling(10, min_periods=10).sum())
    lr = np.log(c).groupby(seg).diff()
    rv = lr.groupby(seg).transform(lambda x: x.rolling(10, min_periods=10).std())
    rv_med = rv.rolling(120, min_periods=60).median()     # NaN rv values (segment warm-up) are skipped
    out = pd.DataFrame({"date": s["date"], "er10": er.shift(1), "rv10": rv.shift(1), "rv_med": rv_med.shift(1)})
    # values right after a segment restart must not use the previous segment's row via shift(1)
    first = np.r_[True, (seg.to_numpy()[1:] != seg.to_numpy()[:-1])]
    out.loc[first, ["er10", "rv10"]] = np.nan
    # first session of the week, from the full trading calendar
    cal = pd.to_datetime(pd.Series(allday))
    iso = cal.dt.isocalendar()
    wk = iso["year"].astype(int) * 100 + iso["week"].astype(int)
    fw = pd.DataFrame({"date": allday, "first_week": np.r_[True, wk.to_numpy()[1:] != wk.to_numpy()[:-1]]})
    out = fw.merge(out, on="date", how="left")
    _MEM["spy"] = out
    return out


def map_spy(df, cols):
    S = spy_class()
    ds = pd.Series(df["date"].to_numpy()).astype(str)
    m = pd.DataFrame({"date": ds}).merge(S[["date"] + list(cols)], on="date", how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}


def head_closes(symbols):
    """Per (symbol, date): min close of the 09:35-09:45 bars (head/tail table), open months only."""
    ck = ("head", tuple(sorted(symbols)))
    if ck in _MEM:
        return _MEM[ck]
    import pyarrow.dataset as ds
    t = ds.dataset(str(C3._HEADTAIL), format="parquet").to_table(
        columns=["symbol", "date", "tod", "c"],
        filter=ds.field("symbol").isin(list(symbols)) & (ds.field("tod") < 950)).to_pandas()
    t["symbol"] = t["symbol"].astype(str)
    t["date"] = pd.to_datetime(t["date"]).dt.date.astype(str)
    t = t[(t["date"] < "2024-11-01") | (t["date"] > "2025-02-28")]
    out = t.groupby(["symbol", "date"], as_index=False)["c"].min().rename(columns={"c": "hmin"})
    _MEM[ck] = out
    return out


def map_head(df, k, symbols):
    t = head_closes(symbols)
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st],
                      "date": pd.Series(df["date"].to_numpy()[st]).astype(str).to_numpy()})
    m = u.merge(t, on=["symbol", "date"], how="left")
    return m["hmin"].to_numpy(float)[np.cumsum(st) - 1]


def run_min(x, k):
    """Running min of x within each symbol-day (NaN ignored)."""
    s = pd.Series(np.asarray(x, float)).groupby(k).cummin()
    return s.to_numpy(float)


def first_true(m, k):
    """True only on the first True row of each symbol-day."""
    m = np.asarray(m, bool)
    c = pd.Series(m.astype(np.int64)).groupby(k).cumsum().to_numpy()
    return m & (c == 1)
