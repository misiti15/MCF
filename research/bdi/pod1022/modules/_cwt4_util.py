"""_cwt4_util - shared helpers for the pod-cwt4-* lab modules (not a setup; no SIDE / mask).

Point-in-time inputs the scorer frame does not carry:
  * daily bars since 2023-06 from research/swarm1010/w3_daily/data/daily_2016.parquet. The rule-19 locked block
    (2024-11-01..2025-02-28) is excluded by the parquet read filter, so it is never read. Every value is mapped to
    day D as of D-1's close (completed days only).
    - "segmented" features (ATR14, SMA50, 20-day return z-score, range boxes) restart after a > 7-day calendar gap,
      so nothing is bridged across the dropped block (warm-up NaN after it).
    - SPY SMA200 and the 250-session gap-fill statistics run over the last N OPEN sessions and do bridge the dropped
      block (declared: slow, distribution-type values; the block itself is never read).
  * VIX daily closes (research/swarm1010/w5_sources/data/vix_daily.parquet; locked dates dropped again here).
  * the macro release calendar (CPI / NFP / PPI from _r212_util, FOMC from _r25_util; published in advance).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _cwt3_bars as CB  # noqa: E402

_ROOT = Path(__file__).resolve().parents[4]
_D2016 = _ROOT / "research" / "swarm1010" / "w3_daily" / "data" / "daily_2016.parquet"
_VIX = _ROOT / "research" / "swarm1010" / "w5_sources" / "data" / "vix_daily.parquet"
LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
_MEM = {}

f, key, start, lag, base, map_rows, full_bars, tf5 = (CB.f, CB.key, CB.start, CB.lag, CB.base, CB.map_rows,
                                                     CB.full_bars, CB.tf5)
ETF15 = list(CB.ETFS)


def macro_days():
    if "macro" not in _MEM:
        try:
            import _r212_util as R212
            import _r25_util as R25
            _MEM["macro"] = set(R212.RELEASE) | set(R25.FOMC)
        except Exception:
            _MEM["macro"] = set()
    return _MEM["macro"]


def dstr(df):
    return pd.Series(df["date"].to_numpy()).astype(str).to_numpy()


def raw_daily():
    """Daily OHLC since 2023-06-01 for the history2y symbols, locked block excluded at read."""
    if "raw" in _MEM:
        return _MEM["raw"]
    import pyarrow.dataset as ds
    syms = sorted(set(CB.lib().daily()["symbol"].astype(str)))
    dset = ds.dataset(str(_D2016), format="parquet")
    dt = dset.schema.field("date").type
    import pyarrow as pa
    def lit(ts):
        return pa.scalar(ts.to_pydatetime(), type=dt) if pa.types.is_timestamp(dt) else pa.scalar(ts.date(), type=dt)
    flt = (ds.field("symbol").isin(syms) & (ds.field("date") >= lit(pd.Timestamp("2023-06-01")))
           & ((ds.field("date") < lit(LOCK_A)) | (ds.field("date") > lit(LOCK_B + pd.Timedelta(hours=23)))))
    d = dset.to_table(columns=["symbol", "date", "open", "high", "low", "close"], filter=flt).to_pandas()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = pd.to_datetime(d["date"]).dt.normalize()
    d = d[(d["date"] < LOCK_A) | (d["date"] > LOCK_B)]
    d = d.dropna(subset=["open", "high", "low", "close"])
    d = d.sort_values(["symbol", "date"]).drop_duplicates(["symbol", "date"]).reset_index(drop=True)
    _MEM["raw"] = d
    return d


def _seg(d):
    dt = d["date"]
    return ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()


def daily_basic():
    """Per (symbol, date D): values as of D-1 (suffix _1) from segmented series."""
    if "basic" in _MEM:
        return _MEM["basic"]
    d = raw_daily()
    g = _seg(d)
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    pcl = c.groupby(g).shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    sma50 = c.groupby(g).transform(lambda x: x.rolling(50, min_periods=50).mean())
    above = (c > sma50).astype(float).where(sma50.notna())
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"].dt.strftime("%Y-%m-%d")})
    cur = {"atr14": tr.groupby(g).transform(lambda x: x.rolling(14, min_periods=14).mean()),
           "sma50": sma50,
           "above15": above.groupby(g).transform(lambda x: x.rolling(15, min_periods=15).sum()),
           "sma50_10": sma50.groupby(g).shift(10),
           "d_high": h, "d_low": l, "d_close": c, "d_range": h - l}
    for nm, s in cur.items():
        out[nm + "_1"] = s.groupby(g).shift(1)
    _MEM["basic"] = out
    return out


def map_day(df, k, tab, cols):
    st = start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": dstr(df)[st]})
    m = u.merge(tab, on=["symbol", "date"], how="left")
    assert len(m) == int(st.sum())
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def spy_sma200_ok():
    """date str -> True when SPY's close on D-1 > its SMA200 (last 200 open sessions, bridging the dropped block)."""
    if "spy200" in _MEM:
        return _MEM["spy200"]
    d = raw_daily()
    s = d[d["symbol"] == "SPY"].set_index("date")["close"].sort_index()
    ok = (s > s.rolling(200, min_periods=200).mean()).where(s.rolling(200, min_periods=200).mean().notna())
    ok1 = ok.shift(1)
    _MEM["spy200"] = {dd.strftime("%Y-%m-%d"): v for dd, v in ok1.items()}
    return _MEM["spy200"]


def vix_rise():
    """date str D -> VIX close(D-1) / VIX close(D-6) - 1 (both completed days; NaN if they are > 12 days apart)."""
    if "vix" in _MEM:
        return _MEM["vix"]
    v = pd.read_parquet(_VIX, columns=["date", "close"])
    v["date"] = pd.to_datetime(v["date"])
    v = v[(v["date"] < LOCK_A) | (v["date"] > LOCK_B)].sort_values("date").reset_index(drop=True)
    v = v[v["date"] >= "2023-06-01"].reset_index(drop=True)
    days = raw_daily()
    sess = sorted(set(days.loc[days["symbol"] == "SPY", "date"]))
    out = {}
    vd = v["date"].to_numpy()
    vc = v["close"].to_numpy(float)
    for D in sess:
        j = np.searchsorted(vd, np.datetime64(D), side="left") - 1      # last VIX date strictly before D
        if j < 5:
            continue
        if (np.datetime64(D) - vd[j]) > np.timedelta64(7, "D") or (vd[j] - vd[j - 5]) > np.timedelta64(12, "D"):
            continue
        out[pd.Timestamp(D).strftime("%Y-%m-%d")] = vc[j] / vc[j - 5] - 1
    _MEM["vix"] = out
    return out


def stash_get(store, fr, mask_fn, i, j):
    s = store.get(id(fr))
    if s is None or len(s[0]) != len(fr):
        mask_fn(fr)
        s = store.get(id(fr))
    return float(s[j][i]) if s is not None else float("nan")
