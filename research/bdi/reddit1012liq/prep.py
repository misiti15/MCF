"""Reddit liquidity study, step 0 (PLAN.md section 1): full-session 5-minute bars for the eligible symbol-days.

  bars   per symbol-day with adv20 >= $95M: 5-minute bars ending 09:35..15:55 rebuilt from the SIP 1-minute cache
         (open, high, low, close, volume, session VWAP on hlc3 as heat_frame), plus the day constants from the lab
         frames (atr_d, adv20, gap, prior-day high/low) and the multi-day levels D5/D20 (prior 5/20 open sessions'
         highest high / lowest low; NaN when the window spans the dropped locked block).

The rule-19 locked block (2024-11-01..2025-02-28) is filtered out at read (pyarrow filter) for the 1-minute cache and
never loaded from the frames (lib.load_month refuses it). Output (git-ignored): data/bars/month=YYYY-MM.parquet.
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

CACHE = ROOT / "data" / "cache_hist" / "1Min"
OUT = HERE / "data"
TZ = "America/New_York"
MIN_ADV = 95e6


def day_table() -> pd.DataFrame:
    rows = []
    for m in lib.months():
        f = lib.load_month(m, ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "dist_pdh_atr", "dist_pdl_atr"])
        f = f.drop_duplicates(["symbol", "date"], keep="first")
        f["pdh"] = f["close"] + f["dist_pdh_atr"] * f["atr_d"]
        f["pdl"] = f["close"] - f["dist_pdl_atr"] * f["atr_d"]
        rows.append(f[["symbol", "date", "atr_d", "adv20", "gap", "pdh", "pdl"]])
    d = pd.concat(rows, ignore_index=True)
    d["symbol"] = d["symbol"].astype(str)
    # multi-day levels from the open daily rows (locked rows absent): prior n sessions' high / low
    dl = lib.daily()[["symbol", "date", "high", "low"]].copy()
    dl["symbol"] = dl["symbol"].astype(str)
    dl = dl.sort_values(["symbol", "date"]).reset_index(drop=True)
    lo_l, hi_l = pd.Timestamp(lib.LOCKED[0]).date(), pd.Timestamp(lib.LOCKED[1]).date()
    out = []
    for sym, x in dl.groupby("symbol", sort=False):
        x = x.reset_index(drop=True)
        dates = pd.Series(x["date"])
        for n in (5, 20):
            hi = x["high"].rolling(n, min_periods=n).max().shift(1)
            lo = x["low"].rolling(n, min_periods=n).min().shift(1)
            first = dates.shift(n)                      # earliest session in the window
            span = first.map(lambda v: isinstance(v, type(lo_l)) and v < lo_l).astype(bool) & (dates > hi_l)
            x[f"d{n}h"] = hi.where(~span)
            x[f"d{n}l"] = lo.where(~span)
        out.append(x[["symbol", "date", "d5h", "d5l", "d20h", "d20l"]])
    dl = pd.concat(out, ignore_index=True)
    d = d.merge(dl, on=["symbol", "date"], how="left")
    return d


def one(args):
    sym, days = args
    lo, hi = pd.Timestamp(lib.LOCKED[0], tz=TZ), pd.Timestamp(lib.LOCKED[1], tz=TZ) + pd.Timedelta(days=1)
    first = pd.Timestamp(lib.FIRST, tz=TZ)
    col = "__index_level_0__"
    p = CACHE / f"{sym}.parquet"
    if not p.exists():
        return None
    t = pq.read_table(p, columns=["open", "high", "low", "close", "volume", col],
                      filters=[[(col, ">=", first), (col, "<", lo)], [(col, ">=", hi)]]).to_pandas()
    if t.empty:
        return None
    ts = pd.DatetimeIndex(t.index).tz_convert(TZ)
    m = ts.hour * 60 + ts.minute
    ok = (m >= 570) & (m < 955)                          # 09:30 .. 15:54 -> bars ending 09:35 .. 15:55
    t, ts, m = t[ok], ts[ok], m[ok]
    t = t.reset_index(drop=True)
    t["date"] = np.asarray(ts.normalize().tz_localize(None).date)
    t["b"] = np.asarray((m - 570) // 5, dtype=np.int16)
    t = t[t["date"].isin(days)]
    if t.empty:
        return None
    g = t.groupby(["date", "b"], sort=True)
    bars = pd.DataFrame({"o": g["open"].first(), "h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last(),
                         "v": g["volume"].sum()}).reset_index()
    tp = (bars.h + bars.l + bars.c) / 3
    cv = bars.groupby("date")["v"].cumsum()
    bars["vwap"] = (tp * bars.v).groupby(bars.date).cumsum() / cv.replace(0, np.nan)
    bars["tod"] = (((570 + 5 * bars.b + 5) // 60) * 100 + (570 + 5 * bars.b + 5) % 60).astype(np.int16)
    bars["symbol"] = sym
    for c in ("o", "h", "l", "c", "v", "vwap"):
        bars[c] = bars[c].astype("float64")
    return bars


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "bars").mkdir(exist_ok=True)
    t0 = time.time()
    d = day_table()
    d = d[(d["adv20"] >= MIN_ADV) & (d["atr_d"] > 0)].reset_index(drop=True)
    d.to_parquet(OUT / "days.parquet", index=False)
    print("days", len(d), d.symbol.nunique(), d[["d5h", "d20h"]].notna().mean().round(3).to_dict(), round(time.time() - t0), flush=True)
    jobs = [(s, set(x["date"])) for s, x in d.groupby("symbol")]
    parts = []
    with Pool(3) as pool:
        for k, b in enumerate(pool.imap_unordered(one, jobs, chunksize=4)):
            if b is not None:
                parts.append(b)
            if k % 100 == 0:
                print(k, round(time.time() - t0), flush=True)
    x = pd.concat(parts, ignore_index=True)
    x = x.merge(d, on=["symbol", "date"], how="inner")
    x["month"] = pd.to_datetime(x["date"]).dt.strftime("%Y-%m")
    x["symbol"] = x["symbol"].astype(str)
    for m, g in x.groupby("month"):
        g = g.sort_values(["symbol", "date", "b"]).drop(columns="month").reset_index(drop=True)
        g.to_parquet(OUT / "bars" / f"month={m}.parquet", index=False, compression="zstd")
    print("rows", len(x), "symbol-days", x.groupby(["symbol", "date"]).ngroups, "done", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
