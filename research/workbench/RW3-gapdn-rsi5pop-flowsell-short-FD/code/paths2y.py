import pickle, numpy as np, pandas as pd
from multiprocessing import Pool
LOCK = ("2024-11-01", "2025-02-28")
C = pd.read_parquet("cand2y.parquet"); rate = pd.read_parquet("etb_rate.parquet").rate
C = C[(C.symbol.map(rate) >= 0.9) & (C.adv20 >= 95e6) & (C.close >= 5) & (C.heat <= -20) & (C.buyPressure < -0.35) & (C.rsi5 > 80)]  # parent conditions: every declared variant is a subset
need = C.groupby("symbol").date.apply(lambda x: set(x)).to_dict()
def job(s):
    d = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{s}.parquet", columns=["open", "high", "low", "close"])
    d.index = d.index.tz_convert("America/New_York")
    ds = d.index.strftime("%Y-%m-%d"); keep = np.isin(ds, list(need[s]))
    d = d[keep]; ds = ds[keep]
    m = d.index.hour * 60 + d.index.minute; k = (m >= 570) & (m < 960); d = d[k]; ds = ds[k]; m = np.asarray(m[k])
    out = {}
    for day in np.unique(ds):
        assert not (LOCK[0] <= day <= LOCK[1])
        i = ds == day
        out[(s, day)] = (m[i], d.open.values[i], d.high.values[i], d.low.values[i], d.close.values[i])
    return out
P = {}
with Pool(3) as p:
    for o in p.imap_unordered(job, sorted(need)): P.update(o)
pickle.dump(P, open("paths2y.pkl", "wb")); print(len(P), len(need))
