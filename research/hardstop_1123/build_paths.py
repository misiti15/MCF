"""hardstop_1123 step 1: candidate lots of the 4 Primary setups (bench10 trade lists) + their minute-close paths
(for open marks) + SPY % vs prior close per minute. Locked block 2024-11-01..2025-02-28 never read.
Usage: python build_paths.py CHECKOUT TOP10W ETB OUTDIR.  Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

CK, T10, ETB, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, str(CK))
from mcf.research.gates import tod_cost_mult  # noqa: E402

P = ["NM-ETF-late-dip-di-long", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
     "L3-gap-slope-fromopen-FD"]
TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
BORROW = 1.2e-4


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if d >= "2025-10-01":
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
    if src is HIST:
        flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
        b = pads.dataset(str(p), format="parquet").to_table(filter=flt, columns=["close", "__index_level_0__"]).to_pandas()
    else:
        b = pd.read_parquet(p, columns=["close"])
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def grids(b, days):
    """day -> 390-minute close grid (09:30..15:59), forward-filled inside the day."""
    day = b.index.date.astype(str)
    mins = (b.index.hour * 60 + b.index.minute).to_numpy()
    C = b["close"].to_numpy(float)
    out = {}
    for d in days:
        ix = np.flatnonzero(day == d)
        if not len(ix):
            continue
        g = np.full(390, np.nan)
        mm = mins[ix] - 570
        ok = (mm >= 0) & (mm < 390)
        g[mm[ok]] = C[ix][ok]
        out[d] = pd.Series(g).ffill().to_numpy()
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
            p = g[a:max(a, z)].astype(np.float32)
            p = np.where(np.isnan(p), np.float32(r.entry), p)
            res.append((r.Index, p))
    return res


def spy_only():
    # SPY % vs prior close, per minute
    rows = []
    for src in (HIST, FRESH):
        b = load("SPY", src)
        days = sorted(set(b.index.date.astype(str)))
        rth = b[(b.index.hour * 60 + b.index.minute >= 570) & (b.index.hour * 60 + b.index.minute < 960)]
        dclose = rth.groupby(rth.index.date.astype(str)).close.last()
        G = grids(b, days)
        prev = None
        for d in days:
            if d in G and prev is not None and period(d) != "none" and (pd.Timestamp(str(d)) - pd.Timestamp(str(prev))).days <= 5:
                pc = dclose[prev]
                rows.append(pd.DataFrame({"date": d, "m": np.arange(570, 960), "spy_pct": (G[d] / pc - 1) * 100}))
            if d in dclose.index:
                prev = d
    S = pd.concat(rows, ignore_index=True)
    S = S.drop_duplicates(["date", "m"])
    no_locked(S.date.unique())
    S.to_parquet(OUT / "spy.parquet", index=False)


if __name__ == "__main__":
    if len(sys.argv) > 5 and sys.argv[5] == "spyonly":
        spy_only()
        sys.exit()
    etb = pd.read_parquet(ETB).rate
    t = pd.concat([pd.read_parquet(T10 / "trades_t1.parquet"), pd.read_parquet(T10 / "trades_t2.parquet")], ignore_index=True)
    t = t[t.setup.isin(P) & t.kind.notna() & (t.kind >= 0)].copy()
    t["date"] = t.date.astype(str)
    t["per"] = t.date.map(period)
    t = t[t.per != "none"]
    no_locked(t.date.unique())
    t = t[t.entry >= 5.0]
    t = t[(t.side > 0) | t.symbol.map(etb).fillna(0).ge(0.9)]
    # add_r (bench10) + per-lot cost terms for marks
    t["tier"] = np.where((np.abs(t.gap) >= 20) | (t.entry < 5), 3.0, 1.0)
    t["ecost"] = (0.01 + t.entry * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xcost = np.where(t.kind == 2, 0.0, 0.01 + t.px * 1e-4) + np.where(t.kind == 1, 0.02, 0.0)
    t["borrow"] = np.where(t.side < 0, BORROW * t.entry, 0.0)
    t["r"] = (t.side * (t.px - t.entry) - t.tier * (t.ecost + xcost) - t.borrow) / t.risk
    t["em"] = (t.tod // 100) * 60 + t.tod % 100
    t["xm"] = (t.xt // 100) * 60 + t.xt % 100
    t = t.reset_index(drop=True)
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    paths = {}
    with Pool(3) as p:
        for k, res in enumerate(p.imap_unordered(job, jobs, chunksize=8)):
            for i, a in res:
                paths[i] = a
            if k % 200 == 0:
                print(k, len(jobs), flush=True)
    t = t[t.index.isin(paths.keys())].copy()
    off, arr, n = [], [], []
    pos = 0
    for i in t.index:
        a = paths[i]
        off.append(pos)
        n.append(len(a))
        arr.append(a)
        pos += len(a)
    t["off"], t["n"] = off, n
    np.save(OUT / "paths.npy", np.concatenate(arr).astype(np.float32))
    t.drop(columns=["px"]).assign(px=t.px).to_parquet(OUT / "cand.parquet", index=False)
    print("candidates", len(t), "path floats", pos)
    spy_only()
