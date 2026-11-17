"""Mechanic GEN-261023-09: the parent's and the copies' own modules (mask()) on lab frames rebuilt as live (lab_frame +
apply_daily, breadth column from the replay universe) for every replay symbol-day with a harness candidate at adv20 >= $150M,
vs the harness selection (first qualifying bar; account cost filter off - it is an account part, not a module part).
Educational only - not financial advice."""
import importlib.util, numpy as np, pandas as pd
from common import OUT, SETUP, WT
from mcf.report import engine as E
from sim import select, PARENT
C = pd.read_parquet(OUT + "cand_replay.parquet"); B = pd.read_parquet(OUT + "rep_breadth.parquet")
C = C[C.adv20 >= 150e6]
syms = sorted(set(C.symbol))
m1 = pd.read_parquet(OUT + "rep_1min_raw.parquet", filters=[("symbol", "in", syms)])
m1 = m1.set_index(pd.DatetimeIndex(m1.ts).tz_convert(E.TZ))
dl = pd.read_parquet(OUT + "rep_daily.parquet"); dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date
paths = {"parent": f"{WT}/research/generator/modules/GEN-261023-09-orbfaildn-late-short.py"}
for wb in ("WB1", "WB2", "WB3", "WB4"): paths[wb] = f"{WT}/research/workbench/{SETUP}/modules/{SETUP}-{wb}.py"
M = {}
for k, p in paths.items():
    sp = importlib.util.spec_from_file_location(k, p); M[k] = importlib.util.module_from_spec(sp); sp.loader.exec_module(M[k])
hits = {k: set() for k in M}
for sym, g in m1.groupby("symbol"):
    g = E._rth(g[["open", "high", "low", "close", "volume"]].astype(float).sort_index())
    dd = dl[dl.symbol == sym].set_index("d")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    f = E.lab_frame(g)
    for day in sorted(set(C[C.symbol == sym].date)):
        fd = E.apply_daily(f, dd[dd.index < pd.Timestamp(day).date()], day); fd = fd[fd.index.date == pd.Timestamp(day).date()].copy()
        fd["date"] = day; fd["symbol"] = sym
        fd = fd.reset_index(drop=True).merge(B[["date", "tod", "breadth"]], on=["date", "tod"], how="left")
        for k, mod in M.items():
            mk = mod.mask(fd)
            if mk.any(): hits[k].add((sym, day, int(fd.tod[np.argmax(mk)])))
R = [("ret3_atr", ">=", 0.20)]; A = [("adx7", ">=", 44.0)]
H = {"parent": {}, "WB1": {"lo": 1430}, "WB2": {"extra": tuple(R)}, "WB3": {"lo": 1430, "extra": tuple(R)}, "WB4": {"lo": 1430, "extra": tuple(R + A)}}
for k, v in H.items():
    s = select(C, {**PARENT, **v, "cf": None})
    mine = set(s[["symbol", "date", "tod"]].itertuples(index=False, name=None))
    print(k, "module", len(hits[k]), "harness", len(mine), "match", len(hits[k] & mine), "module-only", sorted(hits[k] - mine)[:6], "harness-only", sorted(mine - hits[k])[:6], flush=True)
