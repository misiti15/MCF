"""Tightening diagnostics (NOTES.md 1.9): large-cap top-300 universe, corporate-action artifact filter, 2x costs,
one-day execution delay. Imports study.py (which re-runs from its simulation cache), changes one global at a time,
re-simulates the stock long-only configs and their benchmark, and appends `diag_*` rows to diag.csv.
The locked block stays zeroed (study.py). Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import study as S  # noqa: E402

BASE_ELIG = S.ELIG.copy()
BASE_COST = S.COST_O.copy()
STOCK = [c for c in S.CONFIGS if c["family"] in ("S1", "S2", "S3", "S4", "S5", "S6")]

# top 300 eligible by adv20 at each t
adv = np.where(BASE_ELIG, S.adv20, -np.inf)
rank = (-adv).argsort(axis=1).argsort(axis=1)
TOP300 = BASE_ELIG & (rank < 300)
# artifact filter: any |close-to-close| move > +300 % or < -75 % in the last 252 sessions
rr = S.C.pct_change(fill_method=None)
bad = ((rr > 3.0) | (rr < -0.75)).astype(float).rolling(252, min_periods=1).max().fillna(0).to_numpy() > 0
CLEAN = BASE_ELIG & ~bad


def shift_targets(tg):
    return {t + 1: w for t, w in tg.items() if t + 1 < S.T - 1}


VARIANTS = {
    "diag_top300": dict(elig=TOP300),
    "diag_artifact": dict(elig=CLEAN),
    "diag_cost2x": dict(cost=2.0),
    "diag_delay1": dict(delay=True),
}
rows = []
for name, v in VARIANTS.items():
    S.ELIG = v.get("elig", BASE_ELIG)
    S.COST_O = BASE_COST * v.get("cost", 1.0)
    bench = S.simulate(S.ew_universe_targets())
    S.SER[f"{name}__BENCH_EW"] = bench
    for c in STOCK:
        tg = c["fn"]()
        if v.get("delay"):
            tg = shift_targets(tg)
        sid = f"{c['id']}__{name}"
        S.SER[sid] = S.simulate(tg)
        S.BENCH_OF[sid] = f"{name}__BENCH_EW"
        for p in ("train", "valid", "valid2", "trval"):
            d = S.stats(sid, p)
            d.update(base=c["id"], diag=name)
            rows.append(d)
        print(name, c["id"], flush=True)
    for p in ("train", "valid", "valid2", "trval"):
        d = S.stats(f"{name}__BENCH_EW", p)
        d.update(base="BENCH_EW", diag=name)
        rows.append(d)
S.ELIG, S.COST_O = BASE_ELIG, BASE_COST
out = pd.DataFrame(rows)
out.to_csv(S.HERE / "diag.csv", index=False, float_format="%.5f")
piv = out[out.period != "trval"].pivot_table(index=["base"], columns=["diag", "period"], values="active")
print(piv.round(3).to_string())
