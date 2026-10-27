"""bdi1027: score the 16 configs of PLAN.md (12 A + 4 B; B parents for reference). Costs in; locked block never read;
no holdout scored.  Usage: python eval_1027.py > eval_out.txt     Educational only - not financial advice."""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402
HERE = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1027")
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
NA, NB = 737 + 12, 800 + 4
BAR = {"A": round(math.sqrt(2 * math.log(NA)), 2), "B": round(math.sqrt(2 * math.log(NB)), 2)}
T = pd.read_parquet(SCR / "trades.parquet")
T["date"] = pd.to_datetime(T["date"]).dt.date
assert not ((T.date >= LOCK[0]) & (T.date <= LOCK[1])).any()
T = T[T["filled"]].copy(); T["cfg"] = T["cfg"].astype(str)
T["split"] = np.where(T.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
T["regime"] = T.date.map(lib.regimes()["regime"])
T["month"] = pd.to_datetime(T.date).dt.strftime("%Y-%m")


def day_t(x):
    g = x.groupby("date")["r"].agg(["sum", "size"])
    m = g["sum"].sum() / g["size"].sum()
    se = np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / g["size"].sum()
    return m / se if se > 0 else np.nan


par = {}
rows = []
for cfg, x in T.groupby("cfg"):
    idea = cfg[0]
    r = {"cfg": cfg, "n": len(x), "days": x.date.nunique(), "exp": round(x.r.mean(), 4), "ctrl": round(x.ctrl.mean(), 4)}
    for sp in ("train", "valid"):
        y = x[x.split == sp]; r[f"{sp}_n"] = len(y); r[f"{sp}_exp"] = round(y.r.mean(), 4); r[f"{sp}_ctrl"] = round(y.ctrl.mean(), 4)
    for rg in ("up", "flat", "down"):
        r[f"{rg}_exp"] = round(x[x.regime == rg].r.mean(), 4)
    r["t_all"] = round(day_t(x), 2)
    g = x.groupby("date")["r"].sum(); b = g.idxmax()
    r["exp_wo_best_day"] = round(x[x.date != b].r.mean(), 4); r["best_day_share"] = round(g.max() / g.sum(), 3) if g.sum() > 0 else None
    mo = x.groupby("month").r.mean(); r["wf_pos_months"] = round((mo > 0).mean(), 2)
    rows.append(r)
R = pd.DataFrame(rows).set_index("cfg")
for cfg in R.index:
    if cfg.endswith("|parent"):
        R.loc[cfg, "gates"] = "parent"; continue
    r = R.loc[cfg]; idea = cfg[0]
    g1 = r.train_exp > 0 and r.valid_exp > 0
    g2 = r.train_exp > r.train_ctrl and r.valid_exp > r.valid_ctrl
    g3 = r.up_exp > 0 and r.down_exp > 0
    g4 = r.t_all >= BAR[idea]
    gs = [g1, g2, g3, g4]
    if idea == "B":
        p = R.loc[cfg.rsplit("|", 1)[0] + "|parent"]
        g5 = r.train_exp > p.train_exp and r.valid_exp > p.valid_exp and r.n >= 0.5 * p.n
        R.loc[cfg, "keep"] = round(r.n / p.n, 2); gs.append(g5)
    R.loc[cfg, "gates"] = "".join(str(int(v)) for v in gs)
    R.loc[cfg, "pass"] = all(gs)
    R.loc[cfg, "near_miss"] = (not all(gs)) and g2 and g3 and (gs[4] if idea == "B" else True)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print(f"bdi1027: 16 configs (A 12, lineage N {NA}, bar {BAR['A']}; B 4, lineage N {NB}, bar {BAR['B']}); costs in; locked block not read; no holdout")
print("gates = (1) train&valid > 0, (2) beats same-minute random long in both, (3) up&down sessions > 0, (4) t >= bar, [B: (5) beats parent in both, keeps >= 50%]\n")
print(R.to_string())
R.to_csv(HERE / "results.csv")
c = {"configs": 16, "configs_A": 12, "configs_B": 4, "lineage_N_A": NA, "bar_A": BAR["A"], "lineage_N_B": NB, "bar_B": BAR["B"],
     "passes": int(R["pass"].fillna(False).astype(bool).sum()), "near_misses": int(R["near_miss"].fillna(False).astype(bool).sum()),
     "locked_block_read": False, "holdout_scored": False}
json.dump(c, open(HERE / "counts.json", "w"), indent=1); print(json.dumps(c))
print("\nEducational only - not financial advice.")
