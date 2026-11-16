"""Run parent + every pre-declared variant on (A) live-session replay and (B) 2-year lab (E90 borrow proxy).
Usage: python run.py  -> results.csv, daily_<test>.parquet. Educational only - not financial advice."""
import sys, json, functools
import numpy as np, pandas as pd
sys.path.insert(0, ".")
import sim
from variants_decl import VARIANTS

LOCK = ("2024-11-01", "2025-02-28")
split = lambda d: "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else "FWD")


def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)


# ---- (A) replay
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
R1 = pd.read_parquet("replay_1min.parquet")
RP = {k: mk_path(g) for k, g in R1.groupby(["symbol", "date"])}
getA = lambda s, d: RP.get((s, d))

# ---- (B) 2-year
C = pd.read_parquet("cand2y.parquet"); C["tod"] = C.tod.astype(int)
assert not C.date.between(*LOCK).any()
rate = pd.read_parquet("etb_rate.parquet").rate
C = C[C.symbol.map(rate) >= 0.9].reset_index(drop=True)


import pickle
P2 = pickle.load(open("paths2y.pkl", "rb"))
getB = lambda s, d: P2.get((s, d))
C = C.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)

rows, daily = [], []
base = {}
for name, ch in [("PARENT", {})] + list(VARIANTS.items()):
    v = dict(sim.PARENT, **ch)
    for test, cand, get in (("replay", RF, getA), ("2y", C, getB)):
        t = sim.book(sim.trades(cand, v, get), v)
        if test == "2y":
            t["split"] = t.date.map(split)
        t["cfg"] = name; daily.append(t)
        if name == "PARENT":
            base[test] = t
        days = sorted(set(cand.date))
        parts = [("ALL", t, base[test])] + ([(s, t[t.split == s], base[test][base[test].split == s]) for s in ("TRAIN", "VALID", "FWD")] if test == "2y" else [])
        for sp, tt, bb in parts:
            dd = [d for d in days if sp == "ALL" or split(d) == sp]
            tv, dR = sim.paired_t(bb, tt, dd)
            rows.append(dict(cfg=name, test=test, split=sp, **sim.stats(tt), t_vs_parent=tv, dR_vs_parent=dR))
        print(name, test, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in rows[-1 if test == "replay" else -4].items()}, flush=True)
pd.DataFrame(rows).to_csv("results.csv", index=False, float_format="%.4f")
pd.concat(daily).to_parquet("trades_all.parquet")
