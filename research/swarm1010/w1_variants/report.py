"""W1 report: results.csv (every configuration), per-family summary (summary.csv) and markdown tables (data/tables.md).
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(HERE)]
from mcf.research.gates import t_required  # noqa: E402

import families as FM  # noqa: E402


def prior_tries():
    d = {s["name"]: s["prior_tries"] for s in FM.all_specs()}
    for nm in ("L3-gap-slope-fromopen", "L3-gap-slope-lowdist", "L3-gap-slope-rsi5hi"):
        d[nm] = 274247
    return d


def main():
    parts = [pd.read_csv(HERE / "data" / "configs.csv")]
    if (HERE / "data" / "configs_l3.csv").exists():
        parts.append(pd.read_csv(HERE / "data" / "configs_l3.csv"))
    x = pd.concat(parts, ignore_index=True)
    for c in ("plateau", "plateau_n", "nb_up", "nb_down"):
        if c not in x:
            x[c] = np.nan
    pt = prior_tries()
    cnt = x.groupby("family").size()
    x["n_this"] = x["family"].map(cnt)
    x["t_required"] = [t_required(pt.get(f, 0) + n) for f, n in zip(x["family"], x["n_this"])]
    x["probation"] = ((x["n"] >= 150) & x["both_pos"].fillna(False).astype(bool) & (x["t"] >= 2.0) & (x["wf"] >= 0.6)
                      & (x["ex_best_day"] > 0) & (x["maxday"] <= 0.10) & (x["plateau"] > 0))
    x["asym_changed"] = ((x["n"] >= 150) & x["both_pos"].fillna(False).astype(bool) & (x["robust"] >= 1.0)
                         & (x["nb_up"] > 0) & (x["nb_down"] > 0))
    num = x.select_dtypes("number").columns
    out = x.copy()
    out[num] = out[num].round(4)
    out.drop(columns=["params"]).to_csv(HERE / "results.csv", index=False)
    out[["family", "variant", "params"]].to_csv(HERE / "data" / "params.csv", index=False)

    rows = []
    for f, g in x.groupby("family", sort=False):
        b = g[g["stage"] == "base"].iloc[0]
        v = g[g["stage"] != "base"]
        rk = v[(v["n"] >= 150) & (v["robust"] > -99)].sort_values("robust", ascending=False)
        bp = v[(v["n"] >= 150) & v["both_pos"].fillna(False).astype(bool)]
        sp = v[(v["n"] >= 150) & v["spread"].notna()]
        flips = int((np.sign(sp["spread"]) != np.sign(b["spread"])).sum()) if np.isfinite(b["spread"]) else 0
        top = rk.iloc[0] if len(rk) else None
        rows.append({
            "family": f, "group": b["group"], "lineage": b["lineage"], "side": b["side"], "configs": len(g),
            "t_required": b["t_required"],
            "base_n": b["n"], "base_exp": b["exp"], "base_t": b["t"], "base_up": b["exp_up"], "base_down": b["exp_down"],
            "base_spread": b["spread"], "base_robust": b["robust"],
            "variants_n150": len(sp), "both_pos_n150": len(bp),
            "min_abs_spread": float(sp["spread"].abs().min()) if len(sp) else np.nan, "spread_flips": flips,
            "best_variant": top["variant"] if top is not None else "", "best_n": top["n"] if top is not None else np.nan,
            "best_exp": top["exp"] if top is not None else np.nan, "best_t": top["t"] if top is not None else np.nan,
            "best_up": top["exp_up"] if top is not None else np.nan,
            "best_down": top["exp_down"] if top is not None else np.nan,
            "best_robust": top["robust"] if top is not None else np.nan, "best_wf": top["wf"] if top is not None else np.nan,
            "best_exp_overall": float(v.loc[v["n"] >= 150, "exp"].max()) if (v["n"] >= 150).any() else np.nan,
            "probation_passers": int(g["probation"].sum()), "asym_changed": int(g["asym_changed"].sum()),
        })
    s = pd.DataFrame(rows)
    s.round(4).to_csv(HERE / "summary.csv", index=False)
    print("configs", len(x), "families", len(s), "passers", int(x["probation"].sum()),
          "asym_changed", int(x["asym_changed"].sum()))
    print(s.groupby("group")[["configs", "probation_passers", "asym_changed", "both_pos_n150", "variants_n150"]].sum())
    print(x.groupby("stage").size())


if __name__ == "__main__":
    main()
