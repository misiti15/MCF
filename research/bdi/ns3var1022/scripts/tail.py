"""ns3var1022: the lab frames stop at the 15:00 bar, but the lab outcome (and every exit) runs to 15:55. This builds the
15:05..15:55 five-minute bars (right-labelled, bar-close tod, as the frames) from the 1-minute SIP cache for every
candidate and partner symbol-day. The locked block is excluded in the read filter and asserted absent.
Educational only - not financial advice.   python research/bdi/ns3var1022/scripts/tail.py 4"""
from __future__ import annotations

import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

from nv import NV, ROOT, no_locked

TZ = "America/New_York"
L0 = pa.scalar(pd.Timestamp("2024-11-01", tz=TZ))
L1 = pa.scalar(pd.Timestamp("2025-03-01", tz=TZ))


def job(args):
    sym, dates = args
    p = ROOT / "data" / "cache_hist" / "1Min" / f"{sym}.parquet"
    if not p.exists():
        return None
    d = ds.dataset(str(p))
    f = ds.field("__index_level_0__")
    t = d.to_table(filter=(f < L0) | (f >= L1), columns=["high", "low", "close", "__index_level_0__"]).to_pandas()
    if not len(t):
        return None
    ix = t.index if isinstance(t.index, pd.DatetimeIndex) else pd.DatetimeIndex(t["__index_level_0__"])
    ix = ix.tz_convert(TZ)
    m = ix.hour * 60 + ix.minute
    keep = (m >= 900) & (m < 955)
    t = t.loc[keep].copy()
    ix = ix[keep]
    t["date"] = ix.date
    t = t[t["date"].isin(dates)]
    if not len(t):
        return None
    no_locked(t["date"].unique())
    ii = pd.DatetimeIndex(t.index if isinstance(t.index, pd.DatetimeIndex) else t["__index_level_0__"]).tz_convert(TZ)
    mm = ii.hour * 60 + ii.minute
    t["tod"] = 1500 + 5 * ((np.asarray(mm) - 900) // 5 + 1)
    g = t.groupby(["date", "tod"]).agg(high=("high", "max"), low=("low", "min"), close=("close", "last")).reset_index()
    g["symbol"] = sym
    return g


def main():
    need = []
    for p in sorted((NV / "cand").glob("*.npz")):
        z = np.load(p)
        need.append(pd.DataFrame({"symbol": z["symbol"], "date": z["date"]}))
    need = pd.concat(need).drop_duplicates()
    # partners: their symbol is not stored; take every symbol-day with adv >= 95M on candidate dates (all lab names)
    need["date"] = pd.to_datetime(need["date"]).dt.date
    dates = set(need["date"])
    syms = sorted(p.stem for p in (ROOT / "data" / "cache_hist" / "1Min").glob("*.parquet"))
    w = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    out = []
    with Pool(w) as pool:
        for i, g in enumerate(pool.imap_unordered(job, [(s, dates) for s in syms], chunksize=8)):
            if g is not None:
                out.append(g)
            if i % 100 == 0:
                print(i, flush=True)
    res = pd.concat(out, ignore_index=True)
    res["date"] = res["date"].astype(str)
    res.to_parquet(NV / "tail.parquet")
    print(len(res))


if __name__ == "__main__":
    main()
