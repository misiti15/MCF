"""1-min RTH paths + 5-min VWAP band table for every 2-year candidate symbol-day (open months only). Vectorized per symbol,
checkpointed per symbol in p2y/ (resumable). Band = the parent module's own vwap_band_block on 5-min bars of the session."""
import os, pickle, sys, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "code"); import band
LOCK = ("2024-11-01", "2025-02-28")
C = pd.read_parquet("cand2y.parquet", columns=["symbol", "date", "tod"])
C = C[(C.tod >= 935) & (C.tod <= 1530)]
need = C.groupby("symbol").date.apply(lambda x: set(x)).to_dict()
os.makedirs("p2y", exist_ok=True)
def job(s):
    fo = f"p2y/{s}.pkl"
    if os.path.exists(fo): return s
    d = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{s}.parquet", columns=["open", "high", "low", "close", "volume"])
    d.index = d.index.tz_convert("America/New_York")
    ds = d.index.strftime("%Y-%m-%d").values; m = (d.index.hour * 60 + d.index.minute).values
    k = np.isin(ds, list(need[s])) & (m >= 570) & (m < 960)
    d = d[k]; ds = ds[k]; m = m[k].astype(np.int16)
    assert not ((ds >= LOCK[0]) & (ds <= LOCK[1])).any()
    paths = {}
    o, h, l, c, v = (d[x].to_numpy(np.float64) for x in ("open", "high", "low", "close", "volume"))
    brk = np.r_[0, np.flatnonzero(ds[1:] != ds[:-1]) + 1, len(ds)]
    for a, b in zip(brk[:-1], brk[1:]):
        paths[(s, ds[a])] = (m[a:b], o[a:b], h[a:b], l[a:b], c[a:b])
    f = pd.DataFrame({"date": ds, "bin": (m - 570) // 5, "open": o, "high": h, "low": l, "close": c, "volume": v})
    g = f.groupby(["date", "bin"], sort=True).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum")).reset_index()
    g["symbol"] = s
    out = pd.DataFrame({"symbol": s, "date": g.date, "tod": ((570 + 5 * g.bin + 5) // 60 * 100 + (570 + 5 * g.bin + 5) % 60).astype(int)})
    key = pd.factorize(g.date)[0]; gg = pd.Series(key)
    hh, ll, cc, vv = (g[x].to_numpy(float) for x in ("high", "low", "close", "volume"))
    tp = (hh + ll + cc) / 3
    cv = pd.Series(vv).groupby(gg).cumsum().to_numpy().copy(); cv[cv == 0] = np.nan
    vw = pd.Series(tp * vv).groupby(gg).cumsum().to_numpy() / cv
    sd = np.sqrt(np.clip(pd.Series(tp * tp * vv).groupby(gg).cumsum().to_numpy() / cv - vw * vw, 0, None))
    out["vw5"] = vw; out["sd5"] = sd; out["c5"] = cc
    with np.errstate(invalid="ignore", divide="ignore"):
        out["z5"] = np.where(sd > 0, (cc - vw) / sd, np.nan)
    for kk in band.KS:
        out[f"blk{int(kk * 10)}"] = band.M.vwap_band_block(g[["symbol", "date", "high", "low", "close", "volume"]], kk)
    pickle.dump((paths, out), open(fo + ".tmp", "wb")); os.replace(fo + ".tmp", fo)
    return s
if __name__ == "__main__":
    with Pool(3) as p:
        for i, s in enumerate(p.imap_unordered(job, sorted(need))):
            if i % 100 == 0: print(i, s, flush=True)
    P, B = {}, []
    for s in sorted(need):
        a, b = pickle.load(open(f"p2y/{s}.pkl", "rb")); P.update(a); B.append(b)
    pickle.dump(P, open("paths2y.pkl", "wb")); pd.concat(B).to_parquet("band2y.parquet"); print("DONE", len(P), len(need))
