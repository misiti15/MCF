"""Mechanic NM-RWN5: 1-minute paths 09:50-16:00 (float32) for every candidate symbol-day that any tested config can select
(2y: data/cache_hist/1Min, locked block dropped on read; replay: the fetched SIP bars). Educational only - not financial advice."""
import sys, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, LOCK
LO, HI = 950, 1600

def per_sym(a):
    sym, dates = a
    try:
        df = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet")
    except Exception:
        return {}
    idx = df.index.tz_localize(None)
    day = idx.values.astype("datetime64[D]")
    hm = (idx.hour * 100 + idx.minute).to_numpy()
    want = np.array(sorted(dates), dtype="datetime64[D]")
    lo, hi = np.datetime64(LOCK[0]), np.datetime64(LOCK[1])
    m = np.isin(day, want) & ~((day >= lo) & (day <= hi)) & (hm >= LO) & (hm < HI)
    day, hm = day[m], hm[m].astype(np.int16)
    o, h, l, c = (df[k].to_numpy(np.float32)[m] for k in ("open", "high", "low", "close"))
    out = {}
    if not len(day): return out
    cut = np.flatnonzero(day[1:] != day[:-1]) + 1
    for s_, e_ in zip(np.r_[0, cut], np.r_[cut, len(day)]):
        out[(sym, str(day[s_]))] = (hm[s_:e_], o[s_:e_], h[s_:e_], l[s_:e_], c[s_:e_])
    return out

def arr(g):
    hm = (g.index.hour * 100 + g.index.minute).to_numpy()
    k = (hm >= LO) & (hm < HI); g = g[k]
    return (hm[k].astype(np.int16), g.open.to_numpy(np.float32), g.high.to_numpy(np.float32), g.low.to_numpy(np.float32),
            g.close.to_numpy(np.float32))

if __name__ == "__main__":
    if sys.argv[1] == "2y":
        c = pd.read_parquet(OUT + "cand2y.parquet", columns=["symbol", "date", "tod", "fromOpen"])
        c = c[(c.fromOpen < -1.5) & (c.tod <= 1200)]
        sd = c.groupby("symbol").date.apply(set).to_dict()
        with Pool(3) as p:
            res = p.map(per_sym, list(sd.items()))
        P = {k: v for r in res for k, v in r.items()}
        pickle.dump(P, open(OUT + "paths2y.pkl", "wb"), protocol=5); print(len(P), c.groupby(["symbol", "date"]).ngroups)
    else:
        from mcf.report import engine as E
        m = pd.read_parquet(OUT + "rep_1min_raw.parquet")
        m = m.set_index(pd.DatetimeIndex(m.ts).tz_convert(E.TZ)); m["date"] = m.index.strftime("%Y-%m-%d")
        c = pd.read_parquet(OUT + "cand_replay.parquet", columns=["symbol", "date"])
        keep = set(zip(c.symbol, c.date))
        P = {(s, d): arr(g.sort_index()) for (s, d), g in m.groupby(["symbol", "date"]) if (s, d) in keep}
        pickle.dump(P, open(OUT + "paths_replay.pkl", "wb"), protocol=5); print(len(P), len(keep))
