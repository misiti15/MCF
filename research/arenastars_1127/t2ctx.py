"""ARENASTARS-1127: T2 breadth context (breadth = share of names above their 5-min VWAP, breadth_open = share above the
day open, per 5-min bar close tod) from the T2 1-minute cache (data/cache_fresh/1Min), joined to cache_fresh/ctx.parquet.
Same definitions as mcf.strategies.lab_context.context_from_frames / heat.py (typical-price VWAP from the first regular
bar). Locked block asserted absent. Usage: python t2ctx.py W. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

FRESH = Path("/home/user/MCF/data/cache_fresh")
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")


def job(p):
    b = pd.read_parquet(p)
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    if not len(b):
        return None
    d5 = b.resample("5min", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min",
                                                               "close": "last", "volume": "sum"}).dropna(subset=["close"])
    day = d5.index.date.astype(str)
    assert not ((day >= LOCK[0]) & (day <= LOCK[1])).any()
    typ = (d5.high + d5.low + d5.close) / 3
    g = pd.Series(day, index=d5.index)
    vw = (typ * d5.volume).groupby(day).cumsum() / d5.volume.groupby(day).cumsum().replace(0, np.nan)
    op = d5.open.groupby(day).transform("first")
    end = d5.index + pd.Timedelta(minutes=5)
    tod = end.hour * 100 + end.minute
    return pd.DataFrame({"date": day, "tod": tod.astype(int),
                         "a": np.where(vw.notna(), (d5.close > vw).astype(float), np.nan),
                         "o": (d5.close > op).astype(float)})


if __name__ == "__main__":
    W = Path(sys.argv[1])
    ps = sorted((FRESH / "1Min").glob("*.parquet"))
    with Pool(3) as pl:
        parts = [x for x in pl.imap_unordered(job, ps, chunksize=4) if x is not None]
    x = pd.concat(parts, ignore_index=True)
    br = x.groupby(["date", "tod"]).agg(breadth=("a", "mean"), breadth_open=("o", "mean"), n=("o", "size")).reset_index()
    c = pd.read_parquet(FRESH / "ctx.parquet"); c["date"] = c.date.astype(str)
    out = c.merge(br, on=["date", "tod"], how="left")
    out.to_parquet(W / "ctx_t2.parquet", index=False)
    print(len(ps), "symbols; ctx rows", len(out), "breadth missing", float(out.breadth.isna().mean()))
    print(out.describe().to_string())
