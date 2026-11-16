"""Shared loader: candidates + point-in-time SPY context (after 09:50) + 1-minute paths; run(v) -> trades per test."""
import pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib, sim
OUT = "/dev/shm/mech-st7/"
LOCK = ("2024-11-01", "2025-02-28")
REPLAY = ("2026-10-12", "2026-11-10"); TWO_Y = ("2024-10-01", "2026-10-09")
split = lambda d: "TRAIN" if d <= "2025-12-31" else "VALID"
C = pd.read_parquet(OUT + "cand.parquet"); C["tod"] = C.tod.astype(int)
assert not C.date.between(*LOCK).any()
X = pd.read_parquet(OUT + "ctx.parquet")[["date", "tod", "spy_d950", "spy_rng", "breadth", "breadth_open"]]
C = C.merge(X, on=["date", "tod"], how="left")
P = pickle.load(open(OUT + "paths.pkl", "rb"))
get = lambda s, d: P.get((s, d))
CAND = {"replay": C[C.date.between(*REPLAY)], "2y": C[C.date.between(*TWO_Y)]}
DAYS = {"replay": sorted(set(X.date[X.date.between(*REPLAY)])), "2y": sorted(set(X.date[X.date.between(*TWO_Y)]))}
d = lib.daily(); d = d[d.symbol == "SPY"].copy(); d["date"] = d.date.astype(str)
OC = (d.set_index("date").close / d.set_index("date").open - 1) * 100
DTYPE = lambda x: "na" if pd.isna(x) else ("up" if x > 0.25 else ("down" if x < -0.25 else "flat"))
def run(v):
    out = {}
    for test, cand in CAND.items():
        t = sim.book(sim.trades(cand, v, get), v)
        t["split"] = t.date.map(split); t["dt"] = t.date.map(OC).map(DTYPE)
        out[test] = t
    return out
