"""swing1022 report: merge results, apply the pre-declared Testing bar and the owner's near-miss merit rule
(2026-10-22), write results.csv / finalists.csv / counts.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run import HERE, SCR  # noqa: E402
from prep import split_of  # noqa: E402
from mcf.research import gates  # noqa: E402

R21 = 183          # reddit1021 configurations (same lineage: Reddit level studies)
R12LIQ = 7718      # reddit1012liq level-sweep study


def day_share(T, cfg):
    t = T[T.cfg == cfg]
    if not len(t):
        return np.nan
    g = t.groupby("date").r.sum()
    tot = g.sum()
    return float(g.max() / tot) if tot > 0 else np.nan


def main():
    parts, trades = [], {}
    for grp in ("idx", "lev", "stk"):
        for st in ("s1", "s2"):
            f = HERE / f"results_{grp}_{st}.csv"
            if f.exists():
                parts.append(pd.read_csv(f).assign(stage=st))
                tp = SCR / f"trades_{grp}_{st}.parquet"
                if tp.exists():
                    trades[(grp, st)] = pd.read_parquet(tp, columns=["cfg", "date", "r"])
    R = pd.concat(parts, ignore_index=True)
    N = int(len(R))
    bar = gates.t_required(N)
    bar_lin = gates.t_required(N + R21)
    bar_lin2 = gates.t_required(N + R21 + R12LIQ)
    rows = []
    for i, r in R.iterrows():
        nmin = 150 if r.group == "stk" else 30
        ok = {
            "train_pos": r.get("train_exp", np.nan) > 0,
            "valid_pos": r.get("valid_exp", np.nan) > 0,
            "train_gt_ctrl": r.get("train_exp", np.nan) > r.get("train_ctrl", np.nan),
            "valid_gt_ctrl": r.get("valid_exp", np.nan) > r.get("valid_ctrl", np.nan),
            "valid_t>=1.5": (r.get("valid_t", np.nan) or 0) >= 1.5,
            f"n_train>={nmin}": r.get("train_n", 0) >= nmin,
            "ex_best>0": (r.get("all_ex_best", np.nan) or -1) > 0,
        }
        fails = [k for k, v in ok.items() if not bool(v)]
        ds = day_share(trades.get((r.group, r.stage), pd.DataFrame(columns=["cfg", "date", "r"])), r.cfg)
        merit = (ok["train_pos"] and ok["valid_pos"] and ok["train_gt_ctrl"] and ok["valid_gt_ctrl"]
                 and r.get("train_n", 0) >= 30 and r.get("valid_n", 0) >= 20 and np.isfinite(ds) and ds <= 0.25)
        R.loc[i, "testing_fails"] = ";".join(fails)
        R.loc[i, "testing_pass"] = not fails
        R.loc[i, "near_miss"] = len(fails) == 1
        R.loc[i, "max_day_share"] = round(ds, 3) if np.isfinite(ds) else np.nan
        R.loc[i, "owner_merit"] = bool(merit)
        R.loc[i, "both_neg"] = bool(r.get("train_exp", 0) < 0 and r.get("valid_exp", 0) < 0)
    R.to_csv(HERE / "results.csv", index=False)
    F = R[(R.testing_pass) | (R.near_miss) | (R.owner_merit)].copy()
    F.to_csv(HERE / "finalists.csv", index=False)
    cnt = {g: int((R.group == g).sum()) for g in ("idx", "lev", "stk")}
    cnt.update({"total": N, "study_bar": bar, "lineage_bar_with_reddit1021": bar_lin,
                "lineage_bar_with_reddit1021_and_reddit1012liq": bar_lin2,
                "expected_false_positives_p05": round(0.05 * N, 1),
                "testing_pass": int(R.testing_pass.sum()), "near_miss": int(R.near_miss.sum()),
                "owner_merit": int(R.owner_merit.sum()),
                "max_all_t_n30": float(np.nanmax(R[R.all_n >= 30].all_t.to_numpy(float)))})
    json.dump(cnt, open(HERE / "counts.json", "w"), indent=1)
    print(json.dumps(cnt, indent=1))
    cols = ["group", "cfg", "train_n", "train_exp", "train_t", "train_ctrl", "valid_n", "valid_exp", "valid_t",
            "valid_ctrl", "all_t", "all_ex_best", "max_day_share", "testing_fails", "owner_merit"]
    pd.set_option("display.width", 260)
    print(F[cols].to_string())


if __name__ == "__main__":
    main()
