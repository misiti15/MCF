"""1-minute session paths (09:30-16:00) for every symbol-day of the widened ST7 candidate set: data/cache_hist to 11-04,
data/team day files 11-05..11-10. Locked block rows are never kept (asserted). Educational only - not financial advice."""
import pickle, numpy as np, pandas as pd
from multiprocessing import Pool
OUT = "/dev/shm/mech-st7/"
LOCK = ("2024-11-01", "2025-02-28")
TEAMD = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]
C = pd.read_parquet(OUT + "cand.parquet")
C = C[(C.prsi >= 50) & (C.rsi < 50) & (C.rsi <= 33) & (C.fromOpen < -0.8) & (C.adv20 >= 95e6) & (C.close >= 5)]
need = C.groupby("symbol").date.apply(set).to_dict()
TEAM = None
def init():
    global TEAM
    t = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAMD])
    t["ts"] = pd.to_datetime(t.ts).dt.tz_convert("America/New_York"); TEAM = t
def job(s):
    fr = []
    try:
        d = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{s}.parquet", columns=["open", "high", "low", "close"])
        d.index = d.index.tz_convert("America/New_York"); fr.append(d)
    except Exception:
        pass
    if any(x in TEAMD for x in need[s]):
        t = TEAM[TEAM.symbol == s].set_index("ts")[["open", "high", "low", "close"]]; fr.append(t)
    if not fr: return {}
    d = pd.concat(fr).sort_index(); d = d[~d.index.duplicated()]
    ds = d.index.strftime("%Y-%m-%d"); keep = np.isin(ds, list(need[s])); d = d[keep]; ds = ds[keep]
    m = d.index.hour * 60 + d.index.minute; k = (m >= 570) & (m < 960); d = d[k]; ds = ds[k]; m = np.asarray(m[k])
    out = {}
    for day in np.unique(ds):
        assert not (LOCK[0] <= day <= LOCK[1])
        i = ds == day
        out[(s, day)] = (m[i].astype(np.int16), *(d[c].values[i].astype(np.float64) for c in ("open", "high", "low", "close")))
    return out
import os
SH = OUT + "shards/"
def shard(s):
    f = SH + s + ".pkl"
    if not os.path.exists(f):
        pickle.dump(job(s), open(f + ".tmp", "wb")); os.replace(f + ".tmp", f)
    return s
if __name__ == "__main__":     # resumable: one shard per symbol, then merged
    os.makedirs(SH, exist_ok=True)
    with Pool(3, init) as p:
        for k, _ in enumerate(p.imap_unordered(shard, sorted(need))):
            if k % 100 == 0: print(k, len(need), flush=True)
    P = {}
    for s in need: P.update(pickle.load(open(SH + s + ".pkl", "rb")))
    pickle.dump(P, open(OUT + "paths.pkl", "wb")); print(len(P), sum(len(v) for v in need.values()))
