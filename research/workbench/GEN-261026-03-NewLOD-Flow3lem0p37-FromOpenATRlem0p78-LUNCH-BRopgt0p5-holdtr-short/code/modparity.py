"""Mechanic GEN-261026-03: the copies' own modules (mask()) on lab frames rebuilt as live for every replay symbol with a
harness candidate vs the harness selection (same breadth_open column). Educational only - not financial advice."""
import importlib.util, numpy as np, pandas as pd
from common import OUT, SETUP, WT
from mcf.report import engine as E
C = pd.read_parquet(OUT + "cand_replay.parquet"); B = pd.read_parquet(OUT + "rep_breadth.parquet")
syms = sorted(set(C[(C.adv20 >= 150e6)].symbol))
m1 = pd.read_parquet(OUT + "rep_1min_raw.parquet", filters=[("symbol", "in", syms)])
m1 = m1.set_index(pd.DatetimeIndex(m1.ts).tz_convert(E.TZ))
dl = pd.read_parquet(OUT + "rep_daily.parquet"); dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date
adv = C.groupby(["symbol", "date"]).adv20.first()
M = {}
for wb in ("WB1", "WB2", "WB3"):
    sp = importlib.util.spec_from_file_location(wb, f"{WT}/research/workbench/{SETUP}/modules/{SETUP}-{wb}.py")
    M[wb] = importlib.util.module_from_spec(sp); sp.loader.exec_module(M[wb])
hits = {k: set() for k in M}
for sym, g in m1.groupby("symbol"):
    g = E._rth(g[["open", "high", "low", "close", "volume"]].astype(float).sort_index())
    dd = dl[dl.symbol == sym].set_index("d")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    f = E.lab_frame(g)
    for day in sorted(set(C[C.symbol == sym].date)):
        if adv.get((sym, day), 0) < 150e6: continue
        prior = dd[dd.index < pd.Timestamp(day).date()]
        fd = E.apply_daily(f, prior, day); fd = fd[fd.index.date == pd.Timestamp(day).date()].copy()
        a = fd["atr_d"]; lod = fd["low"].cummin(); hod = fd["high"].cummax()
        fd["dist_lod_atr"] = (fd.close - lod) / a; fd["dist_hod_atr"] = (hod - fd.close) / a
        fd["date"] = day; fd["symbol"] = sym
        fd = fd.reset_index(drop=True).merge(B[["date", "tod", "breadth_open"]], on=["date", "tod"], how="left")
        for wb, mod in M.items():
            mk = mod.mask(fd)
            if mk.any(): hits[wb].add((sym, day, int(fd.tod[np.argmax(mk)])))
F = C[C.adv20 >= 150e6]
for wb, extra, hi in (("WB1", True, 1400), ("WB2", False, 1300), ("WB3", True, 1300)):
    x = F[(F.tod >= 1130) & (F.tod <= hi) & (F.flow3 <= -0.37) & (F.fromOpen_atr <= -0.78) & (F.new_lod == 1) & (F.breadth_open > 0.5)]
    if extra: x = x[x.from_pc_atr <= -1.3]
    mine = set(x.sort_values("tod").groupby(["symbol", "date"]).head(1)[["symbol", "date", "tod"]].itertuples(index=False, name=None))
    print(wb, "module", len(hits[wb]), "harness", len(mine), "match", len(hits[wb] & mine), "module-only", sorted(hits[wb] - mine)[:5], "harness-only", sorted(mine - hits[wb])[:5])
