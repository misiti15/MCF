"""l3_1022: the lab frames stop at the 15:00 bar, but the lab outcome holds to the 15:55 bar (setup_lab close_by 1555).
This builds the missing 5-minute bars 15:05..15:55 (bar-close tod, the frames' convention) from the 1-minute history
cache, for open dates only: the locked block 2024-11-01..2025-02-28 is excluded inside the parquet read filter, so
its rows are never materialised. -> scratch l3_1022/tail.parquet. Educational only - not financial advice."""
from __future__ import annotations

from datetime import datetime
from multiprocessing import Pool
from zoneinfo import ZoneInfo

import pandas as pd
import pyarrow.dataset as ds

import l3c
from rc import ROOT, no_locked

TZ = ZoneInfo("America/New_York")
C = ROOT / "data" / "cache_hist" / "1Min"
F = "__index_level_0__"
LO, L1, L2 = (datetime(2024, 10, 1, tzinfo=TZ), datetime(2024, 11, 1, tzinfo=TZ), datetime(2025, 3, 1, tzinfo=TZ))


def one(p):
    col = ds.field(F)
    flt = (col >= pd.Timestamp(LO)) & ((col < pd.Timestamp(L1)) | (col >= pd.Timestamp(L2)))
    t = ds.dataset(str(p)).to_table(filter=flt).to_pandas()
    if t.empty:
        return None
    t = t.set_index(F) if F in t else t
    t.index = pd.DatetimeIndex(t.index).tz_convert(TZ)
    t = t[(t.index.hour == 15)]
    if t.empty:
        return None
    g = t.resample("5min", label="left", closed="left").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    end = g.index + pd.Timedelta(minutes=5)
    g["tod"] = end.hour * 100 + end.minute
    g["date"] = g.index.date
    g = g[(g["tod"] > 1500) & (g["tod"] <= 1555)]
    g["symbol"] = p.stem
    return g.reset_index(drop=True)


def main():
    files = sorted(C.glob("*.parquet"))
    with Pool(4) as pool:
        parts = [x for x in pool.imap_unordered(one, files, chunksize=8) if x is not None]
    out = pd.concat(parts, ignore_index=True)
    no_locked(out["date"].unique())
    out.to_parquet(l3c.SCRATCH / "tail.parquet")
    print(len(out), out["date"].min(), out["date"].max(), out["symbol"].nunique())


if __name__ == "__main__":
    main()
