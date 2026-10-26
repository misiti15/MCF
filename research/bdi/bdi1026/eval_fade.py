"""bdi1026: score the 8 Coil Burst Fade configs (PLAN.md addendum). Costs in; locked block never read; no holdout.
Usage: python eval_fade.py > eval_fade_out.txt     Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402

HERE = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1026")
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
N = 1323 + 8
BAR = round(math.sqrt(2 * math.log(N)), 2)
T = pd.read_parquet(SCR / "fade_trades.parquet")
T["date"] = pd.to_datetime(T["date"]).dt.date
assert not ((T.date >= LOCK[0]) & (T.date <= LOCK[1])).any()
T = T[T["filled"]].copy()
T["split"] = np.where(T.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
T["regime"] = T.date.map(lib.regimes()["regime"])
T["n_bar"] = T.groupby(["setup", "date", "sig_tod"], observed=True)["r"].transform("size")


def day_t(x):
    g = x.groupby("date")["r"].agg(["sum", "size"])
    m = g["sum"].sum() / g["size"].sum()
    se = np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / g["size"].sum()
    return m / se if se > 0 else np.nan


rows = []
for s, P in T.groupby("setup", observed=True):
    for k in (1, 5, 10, 15):
        x = P[P.n_bar >= k]
        r = {"setup": s, "n_bar_min": k, "n": len(x), "days": x.date.nunique()}
        for sp in ("train", "valid"):
            y = x[x.split == sp]; r[f"{sp}_n"] = len(y); r[f"{sp}_exp"] = round(y.r.mean(), 4); r[f"{sp}_ctrl"] = round(y.ctrl.mean(), 4)
        for rg in ("up", "flat", "down"):
            r[f"{rg}_exp"] = round(x[x.regime == rg].r.mean(), 4)
        r["t_all"] = round(day_t(x), 2)
        g = x.groupby("date")["r"].sum(); b = g.idxmax()
        r["exp_wo_best_day"] = round(x[x.date != b].r.mean(), 4); r["best_day_share"] = round(g.max() / g.sum(), 3) if g.sum() > 0 else None
        g1 = r["train_exp"] > 0 and r["valid_exp"] > 0
        g3 = r["train_exp"] > r["train_ctrl"] and r["valid_exp"] > r["valid_ctrl"]
        g4 = r["up_exp"] > 0 and r["down_exp"] > 0
        r["gates"] = "".join(str(int(v)) for v in (g1, g3, g4, r["t_all"] >= BAR))
        r["pass"] = bool(g1 and g3 and g4 and r["t_all"] >= BAR)
        rows.append(r)
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(f"bdi1026 Coil Burst Fade: 8 configs, lineage N {N}, bar {BAR}; costs in; locked block not read; no holdout\n")
print(R.to_string(index=False))
R.to_csv(HERE / "results_fade.csv", index=False)
c = json.load(open(HERE / "counts.json"))
c.update({"configs_fade": len(R), "passes_fade": int(R["pass"].sum()), "configs_total": c["configs"] + len(R), "lineage_N_after_fade": N})
json.dump(c, open(HERE / "counts.json", "w"), indent=1)
print("\nEducational only - not financial advice.")
