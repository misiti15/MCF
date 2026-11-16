"""Mechanic NM-ETF: 1-minute paths 13:00-16:00 for every candidate symbol-day (2y from data/cache_hist/1Min, locked block
dropped on read; replay from the fetched SIP bars). Educational only - not financial advice."""
import sys, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, LOCK

def arr(g):
    hm = g.index.hour * 100 + g.index.minute
    g = g[(hm >= 1300) & (hm < 1600)]
    return ((g.index.hour * 100 + g.index.minute).to_numpy(), g.open.to_numpy(float), g.high.to_numpy(float),
            g.low.to_numpy(float), g.close.to_numpy(float))

def per_sym(a):
    sym, dates = a
    try:
        df = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet")
    except Exception:
        return {}
    ds_ = df.index.strftime("%Y-%m-%d")
    df = df[~((ds_ >= LOCK[0]) & (ds_ <= LOCK[1])) & np.isin(ds_, list(dates))]
    return {(sym, d): arr(g) for d, g in df.groupby(df.index.strftime("%Y-%m-%d"))}

if __name__ == "__main__":
    if sys.argv[1] == "2y":
        c = pd.read_parquet(OUT + "cand2y.parquet")
        c = c[(c.atr_d_pct >= 2.4) & (c.ret3 <= -0.5)]
        sd = c.groupby("symbol").date.apply(set).to_dict()
        with Pool(4) as p:
            res = p.map(per_sym, list(sd.items()))
        P = {k: v for r in res for k, v in r.items()}
        pickle.dump(P, open(OUT + "paths2y.pkl", "wb")); print(len(P), len(c))
    else:
        m = pd.read_parquet(OUT + "replay_1min.parquet")
        P = {(s, d): arr(g) for (s, d), g in m.groupby(["symbol", "date"])}
        pickle.dump(P, open(OUT + "paths_replay.pkl", "wb")); print(len(P))
