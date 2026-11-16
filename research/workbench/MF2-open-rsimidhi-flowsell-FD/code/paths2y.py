"""1-min RTH paths (09:45-16:00, float32) for every 2-year candidate symbol-day (open months only). Reused from the RW5 bench."""
import pickle, numpy as np, pandas as pd
from multiprocessing import Pool
LOCK = ("2024-11-01", "2025-02-28")
C = pd.read_parquet("cand2y.parquet")
C = C[(C.tod >= 945) & (C.tod <= 1500)]
need = C.groupby("symbol").date.apply(lambda x: set(x)).to_dict()
def job(s):
    d = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{s}.parquet", columns=["open", "high", "low", "close"])
    d.index = d.index.tz_convert("America/New_York")
    ds = d.index.strftime("%Y-%m-%d"); keep = np.isin(ds, list(need[s]))
    d = d[keep]; ds = ds[keep]
    m = d.index.hour * 60 + d.index.minute; k = (m >= 585) & (m < 960); d = d[k]; ds = ds[k]; m = np.asarray(m[k]).astype(np.int16)
    out = {}
    for day in np.unique(ds):
        assert not (LOCK[0] <= day <= LOCK[1])
        i = ds == day
        out[(s, day)] = (m[i], *(d[c].values[i].astype(np.float32) for c in ("open", "high", "low", "close")))
    return out
P = {}
with Pool(4) as p:
    for o in p.imap_unordered(job, sorted(need)): P.update(o)
pickle.dump(P, open("paths2y.pkl", "wb"), protocol=4); print(len(P), len(need))
