"""Mechanic GEN-261027-01: 1-minute paths 13:30-16:00 for every candidate symbol-day of the variant superset
(macd_hist >= 0.08, ret3_atr <= -0.05, bar close >= 13:30, any breadth). 2y: data/cache_hist 1-minute, locked block
dropped on read; replay (2026-10-27..11-13): cache to 11-04 + the fetched SIP bars. Educational only - not financial advice."""
import sys, pickle, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, LOCK
SUP = lambda c: c[(c.macd_hist >= 0.08) & (c.ret3_atr <= -0.05) & (c.tod >= 1330)]

def arr(g):
    hm = g.index.hour * 100 + g.index.minute
    g = g[(hm >= 1330) & (hm < 1600)]
    return ((g.index.hour * 100 + g.index.minute).to_numpy(np.int16), g.open.to_numpy(np.float64), g.high.to_numpy(np.float64),
            g.low.to_numpy(np.float64), g.close.to_numpy(np.float64))

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
    C = pd.read_parquet(OUT + "cand_frames.parquet"); C = C[~C.date.between(*LOCK)]
    sd = SUP(C).groupby("symbol").date.apply(set).to_dict()
    with Pool(3) as p:
        res = p.map(per_sym, list(sd.items()), chunksize=8)
    P = {k: v for r in res for k, v in r.items()}
    rep = {k: v for k, v in P.items() if k[1] >= "2026-10-27"}
    P2 = {k: v for k, v in P.items() if k[1] <= "2026-10-26"}
    pickle.dump(P2, open(OUT + "paths2y.pkl", "wb"))
    # replay days after the cache: fetched SIP bars
    RN = pd.read_parquet(OUT + "cand_replay_new.parquet"); RN = RN[RN.date >= "2026-11-05"]
    F = pd.read_parquet(OUT + "fetch_1m.parquet"); F["ts"] = pd.DatetimeIndex(F.ts).tz_convert("America/New_York")
    F["date"] = F.ts.dt.strftime("%Y-%m-%d")
    need = set(map(tuple, SUP(RN)[["symbol", "date"]].drop_duplicates().to_numpy()))
    F = F[[k in need for k in zip(F.symbol, F.date)]]
    for (s, d), g in F.groupby(["symbol", "date"]):
        rep[(s, d)] = arr(g.set_index("ts").astype({"open": float, "high": float, "low": float, "close": float}))
    pickle.dump(rep, open(OUT + "paths_rep.pkl", "wb"))
    print(len(P2), len(rep))
