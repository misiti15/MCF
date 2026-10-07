"""Collect PRE-ALLOCATION candidate trades for the live setups and the 2026-10-07 variants.
Production engine (Backtester + simulate) and config/default.yaml; variants are added as extra
strategies under new names, so the production setups are untouched. Allocation is done later in
analyse.py, once per configuration.

Data: data/cache only, end='2026-09-16' (exclusive): the Sep 16 - Oct 5 holdout is never read.
Bars before 2026-07-15 (cache starts 2026-06-15) are used only as warm-up for prior-day stats
(ATR, ADV, rvol profile, prior 5-min bars); trades are kept for sessions 2026-07-15..2026-09-15.

usage: python research/nightly/2026-10-07/collect.py GROUP CHUNK NCHUNKS
  GROUP = heat  : heat_fade_short (+ start 09:55 / 10:00 variants), heat_fade_long,
                  exhaustion_short (+ window end 14:00 / 14:30 variants)   -- symbol chunks
  GROUP = core  : orb20_a (+ entry_until 10:30 / 11:00 variants), intraday_momentum -- full universe
Educational only - not financial advice.
"""
import sys, time, copy
from dataclasses import asdict
sys.path.insert(0, ".")
import numpy as np
import pandas as pd
from mcf.backtest.engine import Backtester
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.setups import build_strategies, HeatStrategy, LabStrategy

OUT = "research/nightly/2026-10-07/"
END = "2026-09-16"
FIRST = pd.Timestamp("2026-07-15").date()


class HeatStart(HeatStrategy):
    """heat_fade_short with a later first allowed bar close (tod >= start). Same score, same rules."""
    def __init__(self, name, start, **params):
        super().__init__(name=name, **params)
        orig = self.mod.score
        self.mod.score = lambda df: np.where(df["tod"].to_numpy() >= start, orig(df), np.nan)


class LabEnd(LabStrategy):
    """exhaustion_short with an earlier last allowed bar close (tod <= end)."""
    def __init__(self, name, end, **params):
        super().__init__(name=name, **params)
        orig = self.mod.mask
        self.mod.mask = lambda df: np.asarray(orig(df), bool) & (df["tod"].to_numpy() <= end)


class Collect(Backtester):
    def allocate(self, cands):
        self.cands = cands
        return pd.DataFrame()


def strategies(cfg, group):
    S = cfg["strategies"]
    live = {k for k, v in S.items() if v.get("enabled")}
    keep = {"heat": {"heat_fade_short", "heat_fade_long", "exhaustion_short"},
            "core": live - {"heat_fade_short", "heat_fade_long", "exhaustion_short"}}[group]
    c = copy.deepcopy(cfg)
    for k in list(c["strategies"]):
        if k not in keep:
            c["strategies"][k]["enabled"] = False
    if group == "core":
        for until in ("10:30", "11:00"):
            c["strategies"][f"orb20_a__until{until.replace(':', '')}"] = {**S["orb20_a"], "entry_until": until}
    out = build_strategies(c)
    if group == "heat":
        exits = cfg.get("exits", {})
        def params(name):
            p = {**exits, **S[name]}
            p.pop("enabled"); p.pop("type")
            return p
        for st in (955, 1000):
            out.append(HeatStart(f"heat_fade_short__start{st}", st, **params("heat_fade_short")))
        for en in (1400, 1430):
            out.append(LabEnd(f"exhaustion_short__end{en}", en, **params("exhaustion_short")))
    return out


if __name__ == "__main__":
    group, chunk, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    cfg = load_config()
    store = BarStore(cfg["data"]["cache_dir"])
    syms = store.symbols()[chunk::n]
    t0 = time.time()
    data = store.load_many(syms, end=END)
    print(group, chunk, "symbols", len(data), round(time.time() - t0), "s", flush=True)
    strats = strategies(cfg, group)
    print([s.name for s in strats], flush=True)
    bt = Collect(strats, cfg)
    bt.run(data, progress=True)
    df = pd.DataFrame([asdict(x) for x in bt.cands])
    df = df[pd.to_datetime(df["date"]).dt.date >= FIRST]
    df.to_pickle(OUT + f"cands_{group}_{chunk}of{n}.pkl")
    print("done", len(df), round(time.time() - t0), "s", flush=True)
