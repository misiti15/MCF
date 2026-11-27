"""hsscale step 1: candidate lots for the 9 lineup setups (bench10 trade lists) + minute-close paths (open marks).
Locked block 2024-11-01..2025-02-28 never read. Usage (cwd inbox): python build.py OUTDIR. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads
sys.path.insert(0, ".")
from mcf.research.gates import tod_cost_mult  # noqa: E402

OUT = Path(sys.argv[1]); SP = Path(__file__).resolve().parent.parent
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
BORROW = 1.2e-4
GEN = "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short"
COLS = ["setup", "symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind", "xt"]


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


if __name__ == "__main__":
    parts = []
    for f in ("fit", "check", "t2"):
        x = pd.read_parquet(SP / f"pyramid/L1/trades_{f}.parquet")
        parts.append(x[x.kind_ == "prim"].rename(columns={"cfg": "setup"})[COLS])
    for f in ("t1", "t2"):
        x = pd.read_parquet(SP / f"pyramid/S/work/trades_{f}.parquet")
        parts.append(x[x.setup == GEN][COLS])
        parts.append(pd.read_parquet(SP / f"hsscale/work/trades_{f}.parquet")[COLS])
    t = pd.concat(parts, ignore_index=True)
    etb = pd.read_parquet(SP / "pyramid/S/etb_rate.parquet").rate
    t = t[t.kind.notna() & (t.kind >= 0)].copy()
    t["date"] = t.date.astype(str)
    t["per"] = t.date.map(period)
    t = t[t.per != "none"]
    no_locked(t.date.unique())
    t = t[t.entry >= 5.0]
    t = t[(t.side > 0) | t.symbol.map(etb).fillna(0).ge(0.9)]
    t["tier"] = np.where((np.abs(t.gap) >= 20) | (t.entry < 5), 3.0, 1.0)
    t["ecost"] = (0.01 + t.entry * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xcost = np.where(t.kind == 2, 0.0, 0.01 + t.px * 1e-4) + np.where(t.kind == 1, 0.02, 0.0)
    t["borrow"] = np.where(t.side < 0, BORROW * t.entry, 0.0)
    t["r"] = (t.side * (t.px - t.entry) - t.tier * (t.ecost + xcost) - t.borrow) / t.risk
    t["em"] = (t.tod // 100) * 60 + t.tod % 100
    t["xm"] = (t.xt // 100) * 60 + t.xt % 100
    t = t.reset_index(drop=True)
    print(t.groupby(["setup", "per"]).size().unstack())
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    paths = {}
    with Pool(3) as p:
        for k, res in enumerate(p.imap_unordered(job, jobs, chunksize=8)):
            for i, a in res:
                paths[i] = a
            if k % 300 == 0:
                print(k, len(jobs), flush=True)
    t = t[t.index.isin(paths.keys())].copy()
    off, n, arr, pos = [], [], [], 0
    for i in t.index:
        a = paths[i]; off.append(pos); n.append(len(a)); arr.append(a); pos += len(a)
    t["off"], t["n"] = off, n
    np.save(OUT / "paths.npy", np.concatenate(arr).astype(np.float32))
    t.to_parquet(OUT / "cand.parquet", index=False)
    print("candidates", len(t), "path floats", pos)
