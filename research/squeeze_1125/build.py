"""SQUEEZE_1125 bench build: P4 candidate lots (bench10 regenerated) + 1-min close paths + point-in-time betas + SPY
grid (open, closes, session VWAP). Locked block 2024-11-01..2025-02-28 never read. Usage (cwd repo): python build.py W.
Educational only - not financial advice."""
import datetime as dt
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads

W = Path(sys.argv[1])
sys.path.insert(0, ".")
sys.path.insert(0, "research/ultimate_1119/top10")
import bench10 as B  # noqa: E402

SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
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


def betas(t):
    """point-in-time 60-session daily beta to SPY (>= 20 obs), shrunk 0.67 b + 0.33, clipped [-3, 3]."""
    syms = sorted(set(t.symbol) | {"SPY"})
    f = pads.field("date")
    flt = ((f < dt.date(2024, 11, 1)) | (f >= dt.date(2025, 3, 1))) & pads.field("symbol").isin(syms)
    a = pads.dataset("/home/user/MCF/research/history2y/data/daily.parquet").to_table(
        filter=flt, columns=["symbol", "date", "close"]).to_pandas()
    b = pd.read_parquet("/home/user/MCF/data/cache_fresh/daily.parquet", columns=["symbol", "date", "close"])
    b = b[b.symbol.isin(syms)]
    a["date"] = a.date.astype(str); b["date"] = b.date.astype(str)
    x = pd.concat([b[b.date < "2024-09-16"], a]).drop_duplicates(["symbol", "date"]).sort_values(["symbol", "date"])
    no_locked(x.date.unique())
    x["dt"] = pd.to_datetime(x.date)
    x["ret"] = x.groupby("symbol").close.pct_change()
    gap = x.groupby("symbol").dt.diff().dt.days
    x.loc[gap > 5, "ret"] = np.nan          # never bridge the locked gap or data holes
    spy = x[x.symbol == "SPY"].set_index("date").ret
    x["m"] = x.date.map(spy)
    out = []
    for s, g in x.groupby("symbol"):
        g = g.copy()
        v = g[["ret", "m"]].where(g.ret.notna() & g.m.notna())
        r, m = v.ret, v.m
        n = r.rolling(60, min_periods=20).count()
        cov = (r * m).rolling(60, min_periods=20).mean() - r.rolling(60, min_periods=20).mean() * m.rolling(60, min_periods=20).mean()
        var = (m * m).rolling(60, min_periods=20).mean() - m.rolling(60, min_periods=20).mean() ** 2
        g["beta"] = (cov / var).shift(1)    # strictly before the trade date
        g["nobs"] = n.shift(1)
        out.append(g[["symbol", "date", "beta", "nobs"]])
    bb = pd.concat(out)
    return bb


if __name__ == "__main__":
    parts = []
    for f in ("trades_t1", "trades_t2"):
        parts.append(pd.read_parquet(W / f"{f}.parquet"))
    x = pd.concat(parts, ignore_index=True)
    x = x[x.setup.isin(SETUPS)].copy()
    x["date"] = x.date.astype(str)
    x = B.add_r(x)
    x["per"] = x.date.map(period)
    x = x[x.per != "none"]
    no_locked(x.date.unique())
    etb = pd.read_parquet(SP / "pyramid/S/etb_rate.parquet").rate
    x = x[x.entry >= 5.0]
    x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)]
    x["lcost"] = x.r_gross - x.r
    bb = betas(x)
    x = x.merge(bb, on=["symbol", "date"], how="left")
    raw = x.beta.copy()
    x["beta"] = np.where(x.nobs.ge(20) & raw.notna(), np.clip(0.67 * raw + 0.33, -3, 3), 1.0)
    print("beta: default-1 share %.3f; median %.2f; neg share %.3f" % ((~(x.nobs.ge(20) & raw.notna())).mean(),
                                                                      x.beta.median(), (x.beta < 0).mean()))
    t = x[["setup", "symbol", "date", "per", "tod", "side", "entry", "risk", "px", "kind", "em", "xm", "r", "lcost",
           "beta"]].reset_index(drop=True)
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
    np.save(W / "paths.npy", np.concatenate(arr).astype(np.float32))
    t.to_parquet(W / "cand.parquet", index=False)
    print("candidates", len(t), "missing paths", miss, "path floats", pos)
    # SPY grid per session: [open, close(390), vwap(390)]
    days = sorted(t.date.unique())
    rows = {}
    for src, ds in ((HIST, [d for d in days if d >= "2024-09-16"]), (FRESH, [d for d in days if d < "2024-09-16"])):
        b = load("SPY", src, cols=("open", "high", "low", "close", "volume"))
        day = b.index.date.astype(str)
        for d in ds:
            ix = np.flatnonzero(day == d)
            mm = (b.index.hour[ix] * 60 + b.index.minute[ix]).to_numpy() - 570
            ok = (mm >= 0) & (mm < 390)
            if not ok.any():
                continue
            sub = b.iloc[ix[ok]]
            c = np.full(390, np.nan); tp = np.zeros(390); v = np.zeros(390)
            k = mm[ok]
            c[k] = sub.close.to_numpy()
            tp[k] = ((sub.high + sub.low + sub.close) / 3).to_numpy(); v[k] = sub.volume.to_numpy()
            c = pd.Series(c).ffill().bfill().to_numpy()
            cv = np.cumsum(v); vw = np.where(cv > 0, np.cumsum(tp * v) / np.maximum(cv, 1e-9), c)
            rows[d] = np.concatenate([[sub.open.iloc[0]], c, vw])
    D = sorted(rows)
    np.save(W / "spy.npy", np.stack([rows[d] for d in D]).astype(np.float64))
    pd.Series(D).to_csv(W / "spy_days.csv", index=False)
    print("SPY days", len(D), "of", len(days))
