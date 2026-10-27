"""bdi1027 C (PLAN.md addendum 2): CWT14 pdl long parents, skip bars with >= 5 / >= 10 same-setup entries. Post-filter of
scan_1027 B parent trades; costs in; locked block never read; no holdout. Educational only - not financial advice."""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402
HERE = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bdi1027")
N = 808; BAR = round(math.sqrt(2 * math.log(N)), 2)
T = pd.read_parquet(SCR / "trades.parquet"); T["cfg"] = T.cfg.astype(str); T["date"] = pd.to_datetime(T["date"]).dt.date
T = T[T.filled & T.cfg.str.endswith("|parent")].copy()
T["n_bar"] = T.groupby(["cfg", "date", "sig_tod"]).r.transform("size")
T["split"] = np.where(T.date <= pd.Timestamp("2025-12-31").date(), "train", "valid"); T["regime"] = T.date.map(lib.regimes()["regime"])
def day_t(x):
    g = x.groupby("date")["r"].agg(["sum", "size"]); m = g["sum"].sum() / g["size"].sum()
    se = np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / g["size"].sum(); return m / se if se > 0 else np.nan
rows = []
for cfg, p in T.groupby("cfg"):
    for k in (5, 10):
        x = p[p.n_bar < k]
        r = {"cfg": cfg.replace("|parent", f"|skip_nbar{k}"), "n": len(x), "kept": round(len(x) / len(p), 2)}
        for sp in ("train", "valid"):
            y = x[x.split == sp]; q = p[p.split == sp]
            r[f"{sp}_exp"] = round(y.r.mean(), 4); r[f"{sp}_ctrl"] = round(y.ctrl.mean(), 4); r[f"{sp}_parent"] = round(q.r.mean(), 4)
        for rg in ("up", "down"):
            r[f"{rg}_exp"] = round(x[x.regime == rg].r.mean(), 4)
        r["t_all"] = round(day_t(x), 2); r["burst_exp(n_bar>=k)"] = round(p[p.n_bar >= k].r.mean(), 4)
        gs = [r["train_exp"] > 0 and r["valid_exp"] > 0, r["train_exp"] > r["train_ctrl"] and r["valid_exp"] > r["valid_ctrl"],
              r["up_exp"] > 0 and r["down_exp"] > 0, r["t_all"] >= BAR,
              r["train_exp"] > r["train_parent"] and r["valid_exp"] > r["valid_parent"] and r["kept"] >= 0.5]
        r["gates"] = "".join(str(int(v)) for v in gs); r["pass"] = all(gs); rows.append(r)
R = pd.DataFrame(rows); pd.set_option("display.width", 300)
print(f"bdi1027 C cluster skip: 4 configs, lineage N {N}, bar {BAR}; costs in\n"); print(R.to_string(index=False))
R.to_csv(HERE / "results_cluster.csv", index=False)
c = json.load(open(HERE / "counts.json")); c.update({"configs_cluster": 4, "passes_cluster": int(R["pass"].sum()), "configs_flatten_look": 1, "configs_total": 25})
json.dump(c, open(HERE / "counts.json", "w"), indent=1); print("\nEducational only - not financial advice.")
