"""NEVERAGAIN bench build: P4 candidate lots (R3B booked union) + minute-close paths + SPY/IWM day grids.
Locked block 2024-11-01..2025-02-28 never read. Usage: python build_bench.py OUTDIR. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

OUT = Path(sys.argv[1]); SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
NAME = {"L3-fromopen": "L3-gap-slope-fromopen-FD", "RW3": "RW3-gapdn-rsi5pop-flowsell-short-FD",
        "RW5": "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF": "NM-ETF-late-dip-di-long"}


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(sym, src):
    p = src / f"{sym}.parquet"
    if not p.exists():
        return None
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    cols = ["open", "close", "__index_level_0__"]
    b = pads.dataset(str(p), format="parquet").to_table(filter=flt, columns=cols).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def grids(b, days, with_open=False):
    day = b.index.date.astype(str)
    mins = (b.index.hour * 60 + b.index.minute).to_numpy()
    C = b["close"].to_numpy(float); O = b["open"].to_numpy(float)
    out = {}
    for d in days:
        ix = np.flatnonzero(day == d)
        if not len(ix):
            continue
        g = np.full(390, np.nan)
        mm = mins[ix] - 570
        ok = (mm >= 0) & (mm < 390)
        if not ok.any():
            continue
        g[mm[ok]] = C[ix][ok]
        g = pd.Series(g).ffill().bfill().to_numpy()
        if with_open:
            out[d] = (O[ix][ok][0], g)
        else:
            out[d] = g
    return out


def job(args):
    sym, T = args
    res = []
    for src, sub in ((HIST, T[T.date >= "2024-09-16"]), (FRESH, T[T.date < "2024-09-16"])):
        if not len(sub):
            continue
        b = load(sym, src)
        if b is None:
            continue
        G = grids(b, sorted(sub.date.unique()))
        for r in sub.itertuples():
            g = G.get(r.date)
            if g is None:
                continue
            a, z = int(r.em) - 570, min(int(r.xm), 955) - 570
            p = g[a:max(a + 1, z)].astype(np.float32)
            res.append((r.Index, p))
    return res


if __name__ == "__main__":
    x = pd.read_parquet(SP / "pyramid/R3B/booked.parquet")
    x = x[x.base.isin(list(NAME)) & (x.gate == "")]
    x = x.drop_duplicates(["base", "symbol", "date", "tod", "side"]).copy()
    x["setup"] = x.base.map(NAME)
    x["date"] = x.date.astype(str)
    x["per"] = x.date.map(period)
    x = x[x.per != "none"]
    no_locked(x.date.unique())
    x["lcost"] = x.r_gross - x.r
    t = x[["setup", "symbol", "date", "per", "tod", "side", "entry", "risk", "px", "kind", "em", "xm", "r", "lcost"]]
    t = t.reset_index(drop=True)
    print(t.groupby(["setup", "per"]).size().unstack())
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    paths = {}
    with Pool(3) as p:
        for k, res in enumerate(p.imap_unordered(job, jobs, chunksize=8)):
            for i, a in res:
                paths[i] = a
    miss = (~t.index.isin(paths.keys())).sum()
    t = t[t.index.isin(paths.keys())].copy()
    off, n, arr, pos = [], [], [], 0
    for i in t.index:
        a = paths[i]; off.append(pos); n.append(len(a)); arr.append(a); pos += len(a)
    t["off"], t["n"] = off, n
    np.save(OUT / "paths.npy", np.concatenate(arr).astype(np.float32))
    t.to_parquet(OUT / "cand.parquet", index=False)
    print("candidates", len(t), "missing paths", miss, "path floats", pos)
    # index grids for every bench session (SPY / IWM), 390 closes + 09:30 open
    days = sorted(t.date.unique())
    allidx = {}
    for sym in ("SPY", "IWM"):
        G = {}
        for src, ds in ((HIST, [d for d in days if d >= "2024-09-16"]), (FRESH, [d for d in days if d < "2024-09-16"])):
            G.update(grids(load(sym, src), ds, with_open=True))
        allidx[sym] = G
    D = [d for d in days if d in allidx["SPY"] and d in allidx["IWM"]]
    arr = np.zeros((len(D), 2, 391), np.float32)
    for i, d in enumerate(D):
        for j, sym in enumerate(("SPY", "IWM")):
            o, g = allidx[sym][d]
            arr[i, j, 0] = o; arr[i, j, 1:] = g
    np.save(OUT / "idx.npy", arr); pd.Series(D).to_csv(OUT / "idx_days.csv", index=False)
    print("index days", len(D), "of", len(days))
