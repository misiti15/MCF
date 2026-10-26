"""bdi1026: score the 12 pre-declared burst-skip configs (PLAN.md) on the parent coil trades from scan_coil.py.
Costs in (scan_1021 sim). Locked block never read. Usage: python eval_burst.py > eval_out.txt
Educational only - not financial advice."""
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
N_LINEAGE = 1311 + 12
BAR = round(math.sqrt(2 * math.log(N_LINEAGE)), 2)

T = pd.read_parquet(SCR / "coil_trades.parquet")
T["date"] = pd.to_datetime(T["date"]).dt.date
assert not ((T.date >= LOCK[0]) & (T.date <= LOCK[1])).any()
T = T[T["filled"]].copy()
T["split"] = np.where(T.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
T["regime"] = T.date.map(lib.regimes()["regime"])
ctx = pd.concat([lib.load_context(m) for m in lib.months()], ignore_index=True).sort_values(["date", "tod"])
ctx["qqq_run_hi"] = ctx.groupby("date")["qqq_fo"].cummax()
ctx["qqq_at_hi"] = (ctx.qqq_fo >= ctx.qqq_run_hi - 0.10) & (ctx.qqq_fo >= 0.5)
T = T.merge(ctx[["date", "tod", "qqq_at_hi"]].rename(columns={"tod": "sig_tod"}), on=["date", "sig_tod"], how="left")
T["qqq_at_hi"] = T["qqq_at_hi"].fillna(False).astype(bool)
T["n_bar"] = T.groupby(["setup", "date", "sig_tod"], observed=True)["r"].transform("size")
rng = np.random.default_rng(20261026)
T["rk"] = rng.random(len(T))
T["rank_bar"] = T.groupby(["setup", "date", "sig_tod"], observed=True)["rk"].rank(method="first")

CONF = {"A5": lambda t: t.n_bar < 5, "A10": lambda t: t.n_bar < 10, "A15": lambda t: t.n_bar < 15,
        "B3": lambda t: t.rank_bar <= 3, "C": lambda t: ~t.qqq_at_hi, "D": lambda t: ~(t.qqq_at_hi & (t.n_bar >= 5))}


def day_delta(par, keep):
    """delta per parent trade = (kept R - parent R) per day / parent n; day-clustered t."""
    a = par.groupby("date")["r"].agg(["sum", "size"])
    b = par[keep].groupby("date")["r"].sum().reindex(a.index, fill_value=0.0)
    D = b - a["sum"]; n = a["size"].sum(); dl = D.sum() / n
    se = np.sqrt(((D - dl * a["size"]) ** 2).sum()) / n
    return dl, (dl / se if se > 0 else np.nan)


def best_day(x):
    g = x.groupby("date")["r"].sum()
    if len(g) == 0 or g.sum() == 0:
        return np.nan, np.nan
    b = g.idxmax(); rest = x[x.date != b]
    return rest.r.mean(), g.max() / g.sum() if g.sum() > 0 else np.nan


rows = []
print(f"bdi1026 burst-skip: lineage N {N_LINEAGE}, bar {BAR}; locked block not read; no holdout scored\n")
for s, P in T.groupby("setup", observed=True):
    P = P.reset_index(drop=True)
    print(f"== {s}: parent n {len(P)}, exp {P.r.mean():+.4f}R (train {P[P.split=='train'].r.mean():+.4f} / "
          f"valid {P[P.split=='valid'].r.mean():+.4f}); bars with n_bar>=10: {(P.groupby(['date','sig_tod']).size()>=10).sum()}")
    nb = pd.cut(P.n_bar, [0, 1, 4, 9, 14, 999], labels=["1", "2-4", "5-9", "10-14", "15+"])
    print(P.groupby([nb, "split"], observed=True).agg(n=("r", "size"), exp=("r", "mean"), ctrl=("ctrl", "mean")).unstack().round(4).to_string())
    print(P.groupby(["qqq_at_hi", "split"]).agg(n=("r", "size"), exp=("r", "mean")).unstack().round(4).to_string())
    for c, f in CONF.items():
        k = f(P).to_numpy()
        row = {"setup": s, "config": c, "kept": round(k.mean(), 3)}
        for sp in ("train", "valid"):
            m = (P.split == sp).to_numpy()
            row[f"{sp}_n"] = int((k & m).sum()); row[f"{sp}_exp"] = round(P.r[k & m].mean(), 4)
            row[f"{sp}_ctrl"] = round(P.ctrl[k & m].mean(), 4)
            row[f"{sp}_delta"] = round(day_delta(P[m], k[m])[0], 4)
        for rg in ("up", "flat", "down"):
            m = (P.regime == rg).to_numpy()
            row[f"{rg}_exp"] = round(P.r[k & m].mean(), 4)
        dl, t = day_delta(P, k); row["delta_all"] = round(dl, 4); row["t_all"] = round(t, 2)
        ex, sh = best_day(P[k]); row["exp_wo_best_day"] = round(ex, 4); row["best_day_share"] = None if not np.isfinite(sh) else round(sh, 3)
        g1 = row["train_exp"] > 0 and row["valid_exp"] > 0
        g2 = row["train_delta"] > 0 and row["valid_delta"] > 0
        g3 = row["train_exp"] > row["train_ctrl"] and row["valid_exp"] > row["valid_ctrl"]
        g4 = row["up_exp"] > 0 and row["down_exp"] > 0
        g5 = row["kept"] >= 0.5; g6 = t >= BAR
        row["pass"] = bool(g1 and g2 and g3 and g4 and g5 and g6)
        # delta per parent trade is > 0 for any skip of a losing setup, so a near-miss also needs the kept trades'
        # avg R above the parent's in train and valid (PLAN.md addendum)
        better = all(row[f"{sp}_exp"] > P.r[(P.split == sp).to_numpy()].mean() for sp in ("train", "valid"))
        row["kept_better"] = bool(better)
        row["near_miss"] = bool(g2 and g3 and better and not row["pass"])
        row["gates"] = "".join(str(int(g)) for g in (g1, g2, g3, g4, g5, g6))
        rows.append(row)
    print()
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(R.to_string(index=False))
R.to_csv(HERE / "results.csv", index=False)
json.dump({"configs": len(R), "lineage_N": N_LINEAGE, "bar": BAR, "passes": int(R["pass"].sum()),
           "near_misses": int(R["near_miss"].sum()), "locked_block_read": False, "holdout_scored": False},
          open(HERE / "counts.json", "w"), indent=1)
print("\nEducational only - not financial advice.")
