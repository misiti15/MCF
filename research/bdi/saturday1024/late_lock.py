"""saturday1024 addendum L: late profit lock (PLAN.md). For every cached signal of the scored books still open at T,
walk its 1-min path (data/cache_hist, locked block dropped on read): once a bar closes with open profit >= +0.5R at or after T, the stop moves to entry + 0.25R; a later
bar through that level exits there (stop costs). Writes the new R per signal for L1500 / L1430; book_sim.py scores them
(rule key L). Locked months are never loaded. Usage: python late_lock.py <exits.parquet> <out.parquet>
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "gates1021" / "scripts"))
from common import lib, no_locked  # noqa: E402
from load import load_sig  # noqa: E402
from mcf.research.gates import GEOMK, SLIP_BPS, SLIP_PS, STOP_EXTRA, tod_cost_mult  # noqa: E402

U = pd.read_csv(HERE.parent / "gates1021" / "setups_scored.csv").set_index("setup")
ASG = json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"]
members = sorted({s for k in ("primary", "testing", "testing2") for s in ASG[k] if s in U.index})
sig = load_sig(members)
ex = pd.read_parquet(sys.argv[1]); ex["date"] = pd.to_datetime(ex["date"]).dt.date
sig = sig.merge(ex[["setup", "symbol", "date", "tod", "exit_sim"]].drop_duplicates(["setup", "symbol", "date", "tod"]),
                on=["setup", "symbol", "date", "tod"], how="left")
sig["exit_tod"] = sig["exit_tod"].fillna(sig["exit_sim"]).fillna(1555)
sig["month"] = pd.to_datetime(sig["date"]).dt.strftime("%Y-%m")
LOCKS = {"L1500": 1500, "L1430": 1430}
res = {k: sig["r"].to_numpy(float).copy() for k in LOCKS}
hits = {k: 0 for k in LOCKS}
LK0, LK1 = pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date()
CACHE = ROOT / "data" / "cache_hist" / "1Min"
todo = sig[sig["exit_tod"] > 1430]
for n_sym, (sy, g) in enumerate(todo.groupby("symbol")):
    p = CACHE / f"{sy}.parquet"
    if not p.exists():
        continue
    b = pd.read_parquet(p, columns=["high", "low", "close"])
    dd = b.index.date
    b = b[~((dd >= LK0) & (dd <= LK1))]            # the locked block is dropped on read, never used
    no_locked(pd.Series(b.index.date).unique())
    mins = (b.index.hour * 100 + b.index.minute).to_numpy()
    mins = (mins // 100) * 100 + mins % 100 + 1      # bar end, HHMM (minute 59 -> xx60, fine for ordering)
    H, L, C = (b[c].to_numpy() for c in ("high", "low", "close"))
    di = pd.Series(np.arange(len(b))).groupby(b.index.date).indices
    for j, d, tod, px, atr, st, xt in zip(g.index, g.date, g.tod, g.close, g.atr_d, g.setup, g.exit_tod):
        ix = di.get(d)
        if ix is None or not np.isfinite(atr):
            continue
        side = 1 if U.loc[st, "side"] == "long" else -1
        R = 0.25 * atr
        tm = mins[ix]
        for name, T0 in LOCKS.items():
            k = ix[(tm > max(tod, T0)) & (tm <= min(xt, 1555))]
            armed = False
            lvl = px + side * 0.25 * R
            for q in k:
                if armed and ((side == 1 and L[q] <= lvl) or (side == -1 and H[q] >= lvl)):
                    cost = (SLIP_PS + px * SLIP_BPS) * float(tod_cost_mult(np.array([tod]))[0]) \
                        + SLIP_PS + px * SLIP_BPS + STOP_EXTRA
                    res[name][j] = 0.25 - cost / R
                    hits[name] += 1
                    break
                if not armed and side * (C[q] - px) >= 0.5 * R:
                    armed = True
    if n_sym % 200 == 0:
        print(n_sym, sy, hits, flush=True)
out = sig[["setup", "symbol", "date", "tod"]].copy()
for k in LOCKS:
    out[k] = res[k]
out.to_parquet(sys.argv[2])
print("locked exits", hits)
print("Educational only - not financial advice.")
