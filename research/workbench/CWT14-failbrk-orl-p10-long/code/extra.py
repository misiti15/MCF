"""Build lab frames for 2026-11-02..2026-11-10 from 1-minute bars (cache_hist to 11-04 + data/team day files 11-05..11-10),
same pipeline as mcf.research.backlog_lab (setup_lab.build); 11-02..11-04 are a parity check vs the stored frames.
Educational only - not financial advice."""
import sys, glob, numpy as np, pandas as pd, pyarrow.parquet as pq
from multiprocessing import Pool
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/bdi/cwt/live")
from mcf.research.backlog_lab import symbol_frame
import cwt_live_lib as L
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/"
TEAM = {d: None for d in ["2026-11-05","2026-11-06","2026-11-09","2026-11-10"]}
START = pd.Timestamp("2026-07-15", tz="America/New_York")
def team():
    t = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAM])
    t["ts"] = pd.to_datetime(t.ts).dt.tz_convert("America/New_York")
    return t
T = None
def init():
    global T; T = team()
def one(sym):
    try:
        h = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet", filters=[("__index_level_0__", ">=", START)] if False else None)
    except Exception:
        return None
    h = h[h.index >= START]
    t = T[T.symbol == sym].set_index("ts")[["open","high","low","close","volume"]]
    if not len(t): return None
    df = pd.concat([h[["open","high","low","close","volume"]], t]).sort_index()
    df = df[~df.index.duplicated()]
    x, _ = symbol_frame(df, sym)
    if x is None: return None
    x["date"] = pd.to_datetime(x["date"]).dt.date.astype(str)
    x = x[x.date >= "2026-11-02"].copy()
    x["symbol"] = sym
    return x
if __name__ == "__main__":
    s = pd.read_parquet(OUT + "sig_frames.parquet", columns=["symbol"])
    import pyarrow.dataset as ds
    f = ds.dataset("/home/user/MCF/research/history2y/data/frames/month=2026-10", format="parquet").to_table(columns=["symbol","adv20"]).to_pandas()
    syms = sorted(f[f.adv20 >= 50e6].symbol.unique())
    print(len(syms), flush=True)
    with Pool(4, init) as p:
        parts = [x for x in p.map(one, syms, chunksize=8) if x is not None]
    X = pd.concat(parts, ignore_index=True)
    X.to_parquet(OUT + "frames_extra.parquet"); print(X.shape, X.date.unique())
