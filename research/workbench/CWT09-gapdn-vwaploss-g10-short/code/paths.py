"""1-minute paths (RTH) for every candidate symbol-day + SPY, both tests; ETB rate per symbol from the universe
snapshots (2y: symbol-level rate >= 0.9, as the L3 Workbench). Locked block rows are dropped on read.
Educational only - not financial advice."""
import pickle, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, LOCK
S2 = pd.read_parquet(OUT + "sig_2y.parquet")
need = S2.groupby("symbol").date.apply(lambda x: set(x)).to_dict()
need["SPY"] = None

def rth(d):
    d.index = d.index.tz_convert("America/New_York")
    m = d.index.hour * 60 + d.index.minute
    return d[(m >= 570) & (m < 960)]

def pack(g):
    mn = np.asarray(g.index.hour * 60 + g.index.minute)
    return (mn, g.open.to_numpy(float), g.high.to_numpy(float), g.low.to_numpy(float), g.close.to_numpy(float))

def job(s):
    try:
        d = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{s}.parquet", columns=["open", "high", "low", "close"])
    except Exception:
        return {}
    d = rth(d); ds = d.index.strftime("%Y-%m-%d")
    keep = ~((ds >= LOCK[0]) & (ds <= LOCK[1]))
    if need[s] is not None: keep &= np.isin(ds, list(need[s]))
    else: keep &= (ds >= "2024-10-01")
    d = d[keep]; ds = ds[keep]
    return {(s, day): pack(d[ds == day]) for day in np.unique(ds)}

if __name__ == "__main__":
    P = {}
    with Pool(4) as p:
        for o in p.imap_unordered(job, sorted(need)): P.update(o)
    assert not any(LOCK[0] <= k[1] <= LOCK[1] for k in P)
    pickle.dump(P, open(OUT + "paths_2y.pkl", "wb")); print("2y paths", len(P))
    R1 = pd.read_parquet(OUT + "replay_1min.parquet")
    R1.index = pd.DatetimeIndex(R1.index).tz_convert("America/New_York") if R1.index.tz is not None else R1.index
    Q = {(s, d): pack(g) for (s, d), g in R1.groupby(["symbol", "date"])}
    pickle.dump(Q, open(OUT + "paths_replay.pkl", "wb")); print("replay paths", len(Q))
