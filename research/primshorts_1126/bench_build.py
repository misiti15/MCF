"""PRIMSHORTS-1126 bench build for the lineup options (copy of research/squeeze_1125/build.py, betas / SPY grid dropped):
Primary's 4 setups' bench10 candidate lots (L3-fromopen, RW3, RW5 from WORK, NM-ETF from WORK2) + 1-min close paths.
Costs: LIVE-L (cells_live.json) for the shorts and, as sensitivity, LR8 research; NM-ETF keeps LR8 research in both (its
live cost is ~0, LIVE-L over-charges liquid ETFs). Locked block 2024-11-01..2025-02-28 never read.
Usage (repo root): python bench_build.py WORK WORK2 OUT. Educational only - not financial advice."""
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

W, W2, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(H + "/../..")); sys.path.insert(0, os.path.abspath(H + "/../../research/ultimate_1119/top10"))
sys.path.insert(0, H)
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]


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


def load(sym, src, cols=("open", "close")):
    p = src / f"{sym}.parquet"
    if not p.exists():
        return None
    f = pads.field("__index_level_0__")
    flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
    b = pads.dataset(str(p), format="parquet").to_table(filter=flt, columns=list(cols) + ["__index_level_0__"]).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def grid(b, d):
    day = b.index.date.astype(str)
    ix = np.flatnonzero(day == d)
    if not len(ix):
        return None
    mm = (b.index.hour[ix] * 60 + b.index.minute[ix]).to_numpy() - 570
    ok = (mm >= 0) & (mm < 390)
    if not ok.any():
        return None
    g = np.full(390, np.nan)
    g[mm[ok]] = b["close"].to_numpy(float)[ix][ok]
    return pd.Series(g).ffill().bfill().to_numpy()


def job(args):
    sym, T = args
    res = []
    for src, sub in ((HIST, T[T.date >= "2024-09-16"]), (FRESH, T[T.date < "2024-09-16"])):
        if not len(sub):
            continue
        b = load(sym, src)
        if b is None:
            continue
        G = {d: grid(b, d) for d in sorted(sub.date.unique())}
        for r in sub.itertuples():
            g = G.get(r.date)
            if g is None:
                continue
            a, z = int(r.em) - 570, min(int(r.xm), 955) - 570
            res.append((r.Index, g[a:max(a + 1, z)].astype(np.float32)))
    return res




if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [pd.read_parquet(W / f"{f}.parquet") for f in ("trades_t1", "trades_t2")]
    parts += [pd.read_parquet(W2 / f"{f}.parquet") for f in ("trades_t1", "trades_t2")]
    x = pd.concat(parts, ignore_index=True)
    x = x[x.setup.isin(SETUPS)].copy()
    x["date"] = x.date.astype(str)
    x = B.add_r(x)
    x["per"] = x.date.map(period)
    x = x[x.per != "none"]
    no_locked(x.date.unique())
    etb = pd.read_parquet(H + "/etb_rate.parquet").rate
    x = x[x.entry >= 5.0]
    x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)]
    cells = json.load(open(H + "/cells_live.json"))
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    x["r_lr8"] = x.r
    x["r_live"] = np.where(x.side < 0, x.r_gross - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd), x.r)
    t = x[["setup", "symbol", "date", "per", "tod", "side", "entry", "risk", "px", "kind", "em", "xm", "r_gross", "r_lr8",
           "r_live"]].reset_index(drop=True)
    print(t.groupby(["setup", "per"]).size().unstack())
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    paths = {}
    with Pool(3) as p:
        for res in p.imap_unordered(job, jobs, chunksize=8):
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
