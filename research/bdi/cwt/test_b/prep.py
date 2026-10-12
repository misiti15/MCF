"""CWT package B step 0: rows the lab frames do not carry, rebuilt from the 1-minute cache (TESTPLAN amendment
2026-10-12, package B).

  head / tail  5-min bars closing 09:35-09:45 and 15:05-15:55 (high, low, close, session VWAP on 5-min hlc3 as
               mcf.features.vwap), plus check rows (09:50, 10:00, 12:00, 15:00) compared with the frames
  rvol12       09:30-12:00 volume / its mean over the prior 20 open sessions (min 10)
  daily        per symbol-day: ret5 (5-day return to yesterday), beta60 (60-session beta to SPY, sessions before the
               day), near252 (a close within 2% of the 252-day high in the last 5 sessions), ret20 (20-day return to
               yesterday) from the 10-year daily file; return windows spanning the dropped locked block are NaN

The rule-19 locked block (2024-11-01..2025-02-28) is filtered out at read (pyarrow filter) for the 1-minute cache and
dropped right after load for the daily files, before any rolling computation. Output (git-ignored): data/.
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

CACHE = ROOT / "data" / "cache_hist" / "1Min"
OUT = HERE / "data"
KEEP = {935, 940, 945, 950, 1000, 1200, 1500} | set(range(1505, 1556, 5))
TZ = "America/New_York"


def _hhmm(m):
    return (m // 60) * 100 + m % 60


def one(sym: str):
    lo, hi = pd.Timestamp(lib.LOCKED[0], tz=TZ), pd.Timestamp(lib.LOCKED[1], tz=TZ) + pd.Timedelta(days=1)
    first = pd.Timestamp(lib.FIRST, tz=TZ) - pd.Timedelta(days=45)        # 20-session rvol warm-up
    col = "__index_level_0__"
    t = pq.read_table(CACHE / f"{sym}.parquet", columns=["high", "low", "close", "volume", col],
                      filters=[[(col, ">=", first), (col, "<", lo)], [(col, ">=", hi)]]).to_pandas()
    if t.empty:
        return None, None
    ts = pd.DatetimeIndex(t.index).tz_convert(TZ)
    m = ts.hour * 60 + ts.minute
    ok = (m >= 570) & (m < 960)
    t, ts, m = t[ok], ts[ok], m[ok]
    date = ts.normalize().tz_localize(None)
    b = (m - 570) // 5
    t = t.reset_index(drop=True)
    t["date"], t["b"] = np.asarray(date), np.asarray(b)
    g = t.groupby(["date", "b"], sort=True)
    bars = pd.DataFrame({"h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last(), "v": g["volume"].sum()})
    bars = bars.reset_index()
    tp = (bars.h + bars.l + bars.c) / 3
    cv = bars.groupby("date")["v"].cumsum()
    bars["vwap"] = (tp * bars.v).groupby(bars.date).cumsum() / cv.replace(0, np.nan)
    bars["tod"] = _hhmm(570 + 5 * bars.b + 5).astype(np.int16)
    vol12 = bars[bars.tod <= 1200].groupby("date")["v"].sum()
    rv = (vol12 / vol12.shift(1).rolling(20, min_periods=10).mean()).rename("rvol12")
    keep = bars[bars.tod.isin(KEEP) & (bars.date >= pd.Timestamp(lib.FIRST))].copy()
    keep["symbol"] = sym
    out = keep[["symbol", "date", "tod", "h", "l", "c", "vwap"]]
    rv = rv[rv.index >= pd.Timestamp(lib.FIRST)].reset_index()
    rv["symbol"] = sym
    return out, rv


def daily_features():
    d = pd.read_parquet(ROOT / "research" / "swarm1010" / "w3_daily" / "data" / "daily_2016.parquet",
                        columns=["symbol", "date", "high", "close"])
    d["date"] = pd.to_datetime(d["date"])
    s = d["date"].dt.strftime("%Y-%m-%d")
    d = d[(s < lib.LOCKED[0]) | (s > lib.LOCKED[1])]                      # locked rows dropped before rolling
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    gap_after = pd.Timestamp(lib.LOCKED[1])
    out = []
    spy = d[d.symbol == "SPY"].set_index("date")["close"]
    spy_ret = spy.pct_change()
    for sym, x in d.groupby("symbol", sort=False):
        x = x.set_index("date")
        c, h = x["close"], x["high"]
        dates = x.index.to_series()
        # sessions whose look-back spans the dropped locked block get NaN returns
        span = lambda k: (dates.shift(k) < pd.Timestamp(lib.LOCKED[0])) & (dates > gap_after)
        r = c.pct_change()
        r[span(1)] = np.nan
        ret5 = (c / c.shift(5) - 1).where(~span(5)).shift(1) * 100      # 5-day return to yesterday
        ret20 = (c / c.shift(20) - 1).where(~span(20)).shift(1) * 100
        hi252 = h.rolling(252, min_periods=200).max()
        near = (c >= 0.98 * hi252).astype(float).where(hi252.notna())
        near252 = near.rolling(5, min_periods=5).max().shift(1)          # in the last 5 sessions, known at the open
        sr = spy_ret.reindex(x.index)
        sr[span(1)] = np.nan
        cov = r.rolling(60, min_periods=40).cov(sr)
        var = sr.rolling(60, min_periods=40).var()
        beta60 = (cov / var).shift(1)
        f = pd.DataFrame({"ret5": ret5, "ret20": ret20, "near252": near252, "beta60": beta60})
        f["symbol"] = sym
        out.append(f[f.index >= pd.Timestamp(lib.FIRST)].reset_index())
    f = pd.concat(out, ignore_index=True)
    f.to_parquet(OUT / "daily_feat.parquet", index=False)
    print("daily features", len(f), f[["ret5", "ret20", "near252", "beta60"]].notna().mean().round(3).to_dict(), flush=True)


def main():
    OUT.mkdir(exist_ok=True)
    daily_features()
    syms = [s.strip() for s in open(ROOT / "research" / "lab_symbols.txt") if s.strip()]
    rows, rvs = [], []
    t0 = time.time()
    for k, s in enumerate(syms):
        if not (CACHE / f"{s}.parquet").exists():
            continue
        a, b = one(s)
        if a is not None:
            for c in ("h", "l", "c", "vwap"):
                a[c] = a[c].astype("float32")
            rows.append(a)
            rvs.append(b)
        if k % 100 == 0:
            print(k, s, round(time.time() - t0), flush=True)
    x = pd.concat(rows, ignore_index=True)
    x["symbol"] = x["symbol"].astype("category")
    x.to_parquet(OUT / "headtail.parquet", index=False, compression="zstd")
    pd.concat(rvs, ignore_index=True).to_parquet(OUT / "rvol12.parquet", index=False)
    print("rows", len(x), "done", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
