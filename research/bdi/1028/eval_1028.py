"""bdi1028: score the 8 Leader / Laggard Spread configs of PLAN.md. Costs in; locked block never read; no holdout.
Basket R per day = mean of all legs; a day counts only if both sides have >= N/2 legs.
Usage: python eval_1028.py > eval_out.txt     Educational only - not financial advice."""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402
HERE = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1028")
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
NL = 753 + 8; BAR = round(math.sqrt(2 * math.log(NL)), 2)
T = pd.read_parquet(SCR / "trades.parquet")
T["date"] = pd.to_datetime(T["date"]).dt.date
assert not ((T.date >= LOCK[0]) & (T.date <= LOCK[1])).any()
T = T[T["filled"]].copy(); T["cfg"] = T["cfg"].astype(str)
reg = lib.regimes()["regime"]
rows = []
for cfg, x in T.groupby("cfg"):
    N = int(cfg.split("|")[2][1:])
    cnt = x.groupby(["date", "side"]).size().unstack(fill_value=0)
    ok = cnt.index[(cnt.get(1, 0) >= N / 2) & (cnt.get(-1, 0) >= N / 2)]
    x = x[x.date.isin(ok)]
    d = x.groupby("date").r.mean().to_frame("b")
    d["split"] = np.where(pd.Index(d.index) <= pd.Timestamp("2025-12-31").date(), "train", "valid")
    d["regime"] = d.index.map(reg)
    d["month"] = pd.to_datetime(pd.Series(d.index, index=d.index)).dt.strftime("%Y-%m")
    t = d.b.mean() / (d.b.std(ddof=1) / math.sqrt(len(d)))
    best = d.b.idxmax()
    r = {"cfg": cfg, "legs": len(x), "days": len(d), "basket": round(d.b.mean(), 4), "t_day": round(t, 2),
         "wo_best_day": round(d.b.drop(best).mean(), 4),
         "best_share": round(d.b.max() / d.b.sum(), 3) if d.b.sum() > 0 else None,
         "wf_pos_months": round((d.groupby("month").b.mean() > 0).mean(), 2)}
    for sp in ("train", "valid"):
        r[f"{sp}_b"] = round(d[d.split == sp].b.mean(), 4)
        y = x[x.date.isin(d[d.split == sp].index)]
        for s, nm in ((1, "L"), (-1, "S")):
            z = y[y.side == s]; r[f"{sp}_{nm}"] = round(z.r.mean(), 4); r[f"{sp}_{nm}ctl"] = round(z.ctrl.mean(), 4)
    for rg in ("up", "flat", "down"):
        r[f"{rg}_b"] = round(d[d.regime == rg].b.mean(), 4)
    g1 = r["train_b"] > 0 and r["valid_b"] > 0
    g2 = all(r[f"{sp}_{nm}"] > r[f"{sp}_{nm}ctl"] for sp in ("train", "valid") for nm in ("L", "S"))
    g3 = r["up_b"] > 0 and r["down_b"] > 0
    g4 = r["t_day"] >= BAR
    r["gates"] = "".join(str(int(v)) for v in (g1, g2, g3, g4)); r["pass"] = g1 and g2 and g3 and g4
    r["near_miss"] = (not r["pass"]) and g2 and g3
    rows.append(r)
R = pd.DataFrame(rows).set_index("cfg")
pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
print(f"bdi1028 LLS: 8 configs, lineage N {NL}, bar {BAR}; costs in; locked block not read; no holdout")
print("gates = (1) basket train&valid > 0, (2) long & short legs beat same-minute random in train&valid, (3) up&down > 0, (4) t_day >= bar\n")
print(R.to_string()); R.to_csv(HERE / "results.csv")
c = {"configs": 8, "lineage_N": NL, "bar": BAR, "passes": int(R["pass"].sum()), "near_misses": int(R["near_miss"].sum()),
     "locked_block_read": False, "holdout_scored": False}
json.dump(c, open(HERE / "counts.json", "w"), indent=1); print(json.dumps(c))
print("\nEducational only - not financial advice.")
