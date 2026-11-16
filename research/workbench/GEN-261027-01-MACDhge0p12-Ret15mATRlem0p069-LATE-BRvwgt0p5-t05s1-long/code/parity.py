"""Mechanic GEN-261027-01: each module's own mask() vs the engine's selection (same frames, adv / price floor, first bar
per symbol-day; account cost filter off on both sides). Educational only - not financial advice."""
import importlib.util, pandas as pd, numpy as np
from sim import *
import lib
S = "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"
WT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-gen27101/"
MODS = {"parent": (WT + "research/generator/modules/GEN-261027-01-macdh-hi-late-long.py", {}, 20e6)}
V = {1: {"hi": 1430}, 2: {"adv": 100e6}, 3: {"extra": (("br_chg", "<=", 0.2),)}, 4: {"hi": 1430, "extra": (("br_chg", "<=", 0.2),)},
     5: {"hi": 1430, "adv": 100e6, "extra": (("br_chg", "<=", 0.2),)}}
for n, v in V.items():
    MODS[f"WB{n}"] = (WT + f"research/workbench/{S}/modules/{S}-WB{n}.py", v, v.get("adv", 20e6))
C = pd.concat([pd.read_parquet(OUT + "cand2y.parquet"), pd.read_parquet(OUT + "cand_rep.parquet")])
for m in ("2025-04", "2026-06", "2026-10"):
    df = lib.load_month(m, context=True); df["date"] = df.date.astype(str)
    c = C[C.date.str[:7] == m]
    for name, (path, v, adv) in MODS.items():
        sp = importlib.util.spec_from_file_location("x", path); mod = importlib.util.module_from_spec(sp); sp.loader.exec_module(mod)
        k = mod.mask(df) & (df.adv20.to_numpy() >= adv) & (df.close.to_numpy() >= 5)
        a = df[k].groupby(["symbol", "date"]).head(1)
        b = select(c, {**PARENT, **v, "cf": None})
        ka = set(zip(a.symbol, a.date, a.tod)); kb = set(zip(b.symbol, b.date, b.tod.astype(int)))
        print(m, name, "module", len(ka), "engine", len(kb), "same", len(ka & kb))
