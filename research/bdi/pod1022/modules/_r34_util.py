"""_r34_util - shared daily helper for the pod r3_4 modules (SMB not-in-play OR test, SMB bull flag with no overhead
supply, SMB midday shock flush into daily support, SMB capitulation short, Rule 201 SSR modules). Not a setup.

Per (symbol, date str D), values as of D-1's close (lib.daily(), completed days only; the rule-19 locked block is not
in lib.daily(); each series restarts after a > 7-day calendar gap so nothing is bridged across the block):
  c1..c5 (closes D-1..D-5), o1 (open D-1), sma50_1, atr14_1, h60_1 = max high D-60..D-1, h60_2 = max high D-61..D-2,
  lo20_1 = min low D-20..D-1, swl_1 = the last confirmed daily swing low (low_j < low_{j-1} and low_j < low_{j+1};
  confirmed at day j+1's close, so on row D it is a day <= D-2), v20_1 = mean daily share volume D-20..D-1.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as C3  # noqa: E402

_MEM = {}


def daily_tab():
    if "d" in _MEM:
        return _MEM["d"]
    d = C3.lib().daily()[["symbol", "date", "open", "high", "low", "close", "volume"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    o, h, l, c, v = d["open"], d["high"], d["low"], d["close"], d["volume"]
    gb = lambda s: s.groupby(g)
    pcl = gb(c).shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    atr14 = tr.groupby(g).transform(lambda x: x.rolling(14, min_periods=14).mean())
    sma50 = gb(c).transform(lambda x: x.rolling(50, min_periods=50).mean())
    h60 = gb(h).transform(lambda x: x.rolling(60, min_periods=60).max())
    lo20 = gb(l).transform(lambda x: x.rolling(20, min_periods=20).min())
    v20 = gb(v).transform(lambda x: x.rolling(20, min_periods=20).mean())
    lp, ln = gb(l).shift(1), gb(l).shift(-1)
    sw = l.where((l < lp) & (l < ln))                    # swing low at day j (needs day j+1)
    conf = sw.groupby(g).shift(1)                        # known at day j+1's close
    swl = conf.groupby(g).ffill()                        # last confirmed swing low as of this day's close
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    for k in range(1, 6):
        out[f"c{k}"] = gb(c).shift(k)
    out["o1"] = gb(o).shift(1)
    out["sma50_1"] = sma50.groupby(g).shift(1)
    out["atr14_1"] = atr14.groupby(g).shift(1)
    out["h60_1"] = h60.groupby(g).shift(1)
    out["h60_2"] = h60.groupby(g).shift(2)
    out["lo20_1"] = lo20.groupby(g).shift(1)
    out["swl_1"] = swl.groupby(g).shift(1)
    out["v20_1"] = v20.groupby(g).shift(1)
    _MEM["d"] = out
    return out


def map_daily(df, cols):
    k = C3.key(df)
    st = C3.start(k)
    t = daily_tab()
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st],
                      "date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy()[st]})
    m = u.merge(t[["symbol", "date"] + list(cols)], on=["symbol", "date"], how="left")
    assert len(m) == int(st.sum())
    idx = np.cumsum(st) - 1
    return {c: m[c].to_numpy(float)[idx] for c in cols}
