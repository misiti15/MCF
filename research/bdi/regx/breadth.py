"""REGX breadth: share of the day's top-500 lab names (prior-day 20-day dollar ADV) above their session VWAP at each
5-minute boundary (last closed 1-min bar). Writes <scratch>/breadth500.parquet. Locked block never read.
Usage: python breadth.py <scratch> [workers]. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd

M = Path("/home/user/MCF")
S = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
BND = np.arange(575, 960, 5)          # 09:35 .. 15:55


def members():
    d = pd.read_parquet(M / "research/history2y/data/daily.parquet", columns=["symbol", "date", "adv20"])
    d["date"] = d.date.astype(str)
    d = d.sort_values(["symbol", "date"])
    d["adv_prev"] = d.groupby("symbol").adv20.shift(1)
    last = d[d.date == d.date.max()][["symbol", "adv20"]].rename(columns={"adv20": "adv_prev"}).assign(date="2026-11-05")
    d = pd.concat([d[["symbol", "date", "adv_prev"]], last])
    d = d[~d.date.between(*LOCK) & d.adv_prev.notna()]
    d["rk"] = d.groupby("date").adv_prev.rank(ascending=False, method="first")
    return d[d.rk <= 500][["symbol", "date"]]


def frame_of(b):
    b = b.copy(); b["date"] = b.index.strftime("%Y-%m-%d")
    b["m"] = b.index.hour * 60 + b.index.minute
    return b[(b.m >= 570) & (b.m < 960)]


def one(args):
    sym, dates = args
    p = M / "data/cache_hist/1Min" / f"{sym}.parquet"
    parts = []
    if p.exists():
        b = pd.read_parquet(p); parts.append(frame_of(b[(b.index < "2024-11-01") | (b.index >= "2025-03-01")]))
    x = B5[B5.symbol == sym]
    if len(x):
        x = x.set_index("t")[["open", "high", "low", "close", "volume"]]; parts.append(frame_of(x))
    if not parts:
        return None
    b = pd.concat(parts); b = b[b.date.isin(dates)]
    out = []
    for d, g in b.groupby("date"):
        m = g.m.values; tp = ((g.high + g.low + g.close) / 3).values; v = g.volume.values
        vw = np.cumsum(tp * v) / np.maximum(np.cumsum(v), 1e-9)
        ab = g.close.values > vw
        i = np.searchsorted(m, BND) - 1             # last bar with start < boundary
        ok = i >= 0
        out.append(pd.DataFrame({"date": d, "b": BND[ok], "above": ab[i[ok]].astype(np.int8)}))
    return pd.concat(out) if out else None


B5 = pd.read_parquet(S / "bars1105.parquet")
if __name__ == "__main__":
    mem = members()
    jobs = [(s, set(g.date)) for s, g in mem.groupby("symbol")]
    res = []
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 2) as pool:
        for k, r in enumerate(pool.imap_unordered(one, jobs, chunksize=4)):
            if r is not None:
                res.append(r.groupby(["date", "b"]).above.agg(["sum", "count"]))
            if k % 100 == 0:
                print(k, len(jobs), flush=True)
    a = pd.concat(res).groupby(level=[0, 1]).sum()
    a["brd"] = a["sum"] / a["count"]
    a.reset_index().to_parquet(S / "breadth500.parquet")
    print(a.brd.describe(), a.reset_index().date.nunique())
