"""EDGEHUNT: walk the 'hold' (wider-target) variant of every bench candidate lot in rsw/cand.parquet
(REGSTEER-1126 candidates: bench10 signals, entry >= $5, ETB shorts). Variant = same entry/stop
(stop = entry - side*risk), NO target, exit at the stop or at the 15:55 flatten (bench10 walk rules).
Bars: T1 (FIT/CHECK) data/cache_hist via bench10.hist_bars (locked block filtered + asserted),
T2 data/cache_fresh 1Min (locked block asserted absent). Gross R only; costs are added in score.py.
Usage (cwd = repo checkout with research/): python walk_hold.py CAND OUT
Educational only - not financial advice."""
import sys
from pathlib import Path
from multiprocessing import Pool
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

SCORED = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long",
          "GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long"]


def bars(sym, t2):
    if not t2:
        return B.hist_bars(sym)
    f = B.FRESH / "1Min" / f"{sym}.parquet"
    if not f.exists():
        return None
    b = pd.read_parquet(f)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    return b


def job(a):
    sym, T = a
    out = []
    for t2, g in T.groupby(T.per == "T2"):
        try:
            b = bars(sym, t2)
        except Exception:
            b = None
        if b is None or not len(b):
            continue
        X = g.copy()
        X["stop"] = X.entry - X.side * X.risk
        X["tgt"] = np.nan
        out += B.walk_trades(X, b)
    return out


if __name__ == "__main__":
    c = pd.read_parquet(sys.argv[1])
    c = c[c.setup.isin(SCORED)].copy()
    B.no_locked(c.date.unique())
    jobs = list(c.groupby("symbol"))
    res = []
    with Pool(3) as p:
        for k, r in enumerate(p.imap_unordered(job, jobs, chunksize=4)):
            res += r
            if k % 100 == 0:
                print(k, len(jobs), flush=True)
    w = pd.DataFrame(res, columns=["i", "hpx", "hkind", "hxt"]).set_index("i")
    c = c.join(w)
    c.to_parquet(sys.argv[2])
    print("walked", int(c.hpx.notna().sum()), "of", len(c))
