"""_r25_util - shared helpers for the pod r2_5 modules (Williams Oops / smash day, FOMC flush, VXX gates, Alvarez exit).
Not a setup (no SIDE / mask).

Point-in-time inputs the scorer frame does not carry:
  * daily OHLC as of D-1 / D-2 and short look-backs, from lib.daily() (completed days only; the rule-19 locked block
    is not in lib.daily(); series restart after a > 7-day gap so nothing is bridged across it)
  * the VXX 5-minute rows of the frame's month (read straight from the open history frames, never a locked month),
    because a module with SYMBOLS only sees its own symbols' rows
  * the FOMC statement-day calendar (14:00 ET releases; the same list as research/bdi/cwt/test_c/families.py)
Callers use a bar's values only on that bar or later. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as CB  # noqa: E402

_CACHE = {}

# FOMC statement days inside the open history (locked-block dates omitted on purpose).
FOMC = ["2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16"]

ETF15 = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "SMH", "XBI", "KRE"]

f, key, start, lag, base, map_rows, full_bars = CB.f, CB.key, CB.start, CB.lag, CB.base, CB.map_rows, CB.full_bars


def daily_tab():
    """Per (symbol, date D): values known at D's open (D-1 and earlier, completed days)."""
    if "d" in _CACHE:
        return _CACHE["d"]
    d = CB.lib().daily()[["symbol", "date", "open", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    sh = lambda s, n: s.groupby(g).shift(n)
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"]})
    out["o1"], out["h1"], out["l1"], out["c1"] = sh(o, 1), sh(h, 1), sh(l, 1), sh(c, 1)
    out["l2"], out["c2"] = sh(l, 2), sh(c, 2)
    lows = pd.concat([sh(l, n) for n in range(2, 9)], axis=1)          # D-8 .. D-2
    out["ll2_8"] = lows.min(axis=1, skipna=False)
    out["sma50_1"] = sh(c.groupby(g).transform(lambda x: x.rolling(50, min_periods=50).mean()), 1)
    _CACHE["d"] = out
    return out


def map_daily(df, k, cols):
    t = daily_tab()
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(t, on=["symbol", "date"], how="left")
    assert len(m) == int(st.sum())
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def vxx_rows(df, sym="VXX"):
    """VXX 5m rows (date str, tod, h, l, c, fromOpen, vwapDistPct, hod) for the frame's open month(s)."""
    months = CB._open_months(df, warm=False)
    ck = ("vxx", sym, tuple(months))
    if ck in _CACHE:
        return _CACHE[ck]
    for k in [k for k in _CACHE if isinstance(k, tuple) and k[0] == "vxx"]:
        del _CACHE[k]
    L = CB.lib()
    import pyarrow.dataset as ds
    parts = []
    for mo in months:
        if mo in CB._LOCKED_MONTHS or mo in L.LOCKED_MONTHS:
            continue
        x = ds.dataset(str(L.DATA / "frames" / f"month={mo}"), format="parquet").to_table(
            columns=["symbol", "date", "tod", "high", "low", "close", "fromOpen", "vwapDistPct", "dist_hod_atr",
                     "atr_d"], filter=ds.field("symbol") == sym).to_pandas()
        parts.append(x)
    if not parts:
        return None
    x = pd.concat(parts, ignore_index=True)
    x = pd.DataFrame({"date": x["date"].astype(str).to_numpy(), "tod": x["tod"].to_numpy(np.int64),
                      "vh": x["high"].to_numpy(float), "vl": x["low"].to_numpy(float), "vc": x["close"].to_numpy(float),
                      "vfo": x["fromOpen"].to_numpy(float), "vvd": x["vwapDistPct"].to_numpy(float),
                      "vhod": x["close"].to_numpy(float) + x["dist_hod_atr"].to_numpy(float) * x["atr_d"].to_numpy(float)})
    x = x.drop_duplicates(["date", "tod"]).sort_values(["date", "tod"]).reset_index(drop=True)
    _CACHE[ck] = x
    return x


def map_dt(df, t, cols):
    """Left-join a (date, tod) table onto df's rows, in df order."""
    k = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64)})
    m = k.merge(t[["date", "tod"] + list(cols)], on=["date", "tod"], how="left")
    assert len(m) == len(df)
    return {c: m[c].to_numpy(float) for c in cols}
