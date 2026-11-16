"""Incremental 2-year 1-min paths (same as paths2y.py; saves one chunk per 50 symbols so a stop loses little)."""
import pickle, os, glob, numpy as np, pandas as pd
from multiprocessing import Pool
LOCK = ("2024-11-01", "2025-02-28")
C = pd.read_parquet("cand_low.parquet"); rate = pd.read_parquet("etb_rate.parquet").rate
C = C[(C.symbol.map(rate) >= 0.9) & (C.gap <= -2.65) & (C.sma20_slope_pct > 0.37) & (C.dist_lod_atr > 0.78) & (C.dist_lod_atr <= 0.98) & C.tod.between(950, 1500) & (C.close >= 5)]
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
os.makedirs("pchunks", exist_ok=True)
done = set()
for f in glob.glob("pchunks/*.pkl"):
    done |= {k[0] for k in pickle.load(open(f, "rb"))} | set(pickle.load(open(f + ".syms", "rb")))
todo = [s for s in sorted(need) if s not in done]
print(len(todo), "to do", flush=True)
with Pool(4) as p:
    for i in range(0, len(todo), 50):
        ch = todo[i:i + 50]; P = {}
        for o in p.imap_unordered(job, ch): P.update(o)
        pickle.dump(P, open(f"pchunks/c{i:05d}_{len(done)}.pkl", "wb")); pickle.dump(ch, open(f"pchunks/c{i:05d}_{len(done)}.pkl.syms", "wb"))
        print(i + len(ch), flush=True)
P = {}
for f in glob.glob("pchunks/*.pkl"): P.update(pickle.load(open(f, "rb")))
pickle.dump(P, open("paths_low.pkl", "wb")); print(len(P), len(need))
