"""bdi1027 rework A-R (PLAN.md addendum): 4 configs = 2 A rows x breadth_open at the trigger bar >= 0.5 / 0.6.
Post-filter of scan_1027 trades. Costs in; locked block never read; no holdout. Educational only - not financial advice."""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402
HERE = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1027")
N = 753; BAR = round(math.sqrt(2 * math.log(N)), 2)
T = pd.read_parquet(SCR / "trades.parquet"); T["date"] = pd.to_datetime(T["date"]).dt.date
T = T[T.filled & T.cfg.astype(str).isin(["A|d0.20|k1.0|t1s1", "A|d0.40|k1.0|t1s1"])].copy(); T["cfg"] = T.cfg.astype(str)
assert not ((T.date >= pd.Timestamp("2024-11-01").date()) & (T.date <= pd.Timestamp("2025-02-28").date())).any()
ctx = pd.concat([lib.load_context(m)[["date", "tod", "breadth_open"]] for m in sorted({f"{d:%Y-%m}" for d in T.date})])
T = T.merge(ctx.rename(columns={"tod": "sig_tod"}), on=["date", "sig_tod"], how="left")
T["split"] = np.where(T.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
T["regime"] = T.date.map(lib.regimes()["regime"])
def day_t(x):
    g = x.groupby("date")["r"].agg(["sum", "size"]); m = g["sum"].sum() / g["size"].sum()
    se = np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / g["size"].sum(); return m / se if se > 0 else np.nan
rows = []
for cfg, x0 in T.groupby("cfg"):
    for b in (0.5, 0.6):
        x = x0[x0.breadth_open >= b]
        r = {"cfg": f"{cfg}|bo{b}", "n": len(x), "days": x.date.nunique(), "kept": round(len(x) / len(x0), 2)}
        for sp in ("train", "valid"):
            y = x[x.split == sp]; r[f"{sp}_exp"] = round(y.r.mean(), 4); r[f"{sp}_ctrl"] = round(y.ctrl.mean(), 4)
        for rg in ("up", "flat", "down"):
            y = x[x.regime == rg]; r[f"{rg}_n"] = len(y); r[f"{rg}_exp"] = round(y.r.mean(), 4)
        r["t_all"] = round(day_t(x), 2); g = x.groupby("date").r.sum(); bd = g.idxmax()
        r["exp_wo_best_day"] = round(x[x.date != bd].r.mean(), 4); r["best_day_share"] = round(g.max() / g.sum(), 3) if g.sum() > 0 else None
        gs = [r["train_exp"] > 0 and r["valid_exp"] > 0, r["train_exp"] > r["train_ctrl"] and r["valid_exp"] > r["valid_ctrl"],
              r["up_exp"] > 0 and r["down_exp"] > 0, r["t_all"] >= BAR]
        r["gates"] = "".join(str(int(v)) for v in gs); r["pass"] = all(gs); rows.append(r)
R = pd.DataFrame(rows); pd.set_option("display.width", 300)
print(f"bdi1027 rework A-R: 4 configs, lineage N {N}, bar {BAR}; costs in; locked block not read; no holdout\n"); print(R.to_string(index=False))
R.to_csv(HERE / "results_rework.csv", index=False)
c = json.load(open(HERE / "counts.json")); c.update({"configs_rework": 4, "passes_rework": int(R["pass"].sum()), "configs_total": 20, "lineage_N_A_after_rework": N})
json.dump(c, open(HERE / "counts.json", "w"), indent=1); print("\nEducational only - not financial advice.")
