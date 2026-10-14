"""swarm1013 backtest step 4: PLAN section 2 gates, routing and finalists on results.csv.
Writes results.csv (with gate columns), finalists.csv, summary.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
N_STUDY = 402
T_REQ = max(1.5, math.sqrt(2 * math.log(N_STUDY)))

df = pd.read_csv(HERE / "results.csv")
df = df[[c for c in df.columns if not c.startswith(("G", "route", "plateau"))]]

NB = {  # PLAN section 2, G6 neighbours (by family; variant -> neighbours)
    "E1": {"A": ["AK25"], "K25": ["K50"], "K50": ["K25"], "AK25": ["AK50", "A"], "AK50": ["AK25"]},
    "E2": {"NT075": ["NT100"], "NT100": ["NT075"], "P-T05": ["P-BAR"], "P-BAR": ["P-T05"]},
    "E3": {f"{i}-{c}": [f"{j}-{c}" for j in ("QQQ", "SMH", "SECT") if j != i] for i in ("QQQ", "SMH", "SECT") for c in ("any", "aln")},
    "E4": {"T20": ["T30"], "T30": ["T20", "T45"], "T45": ["T30"], "BE03": ["T30+BE"], "T20+BE": ["T30+BE", "T20"],
           "T30+BE": ["T20+BE", "T45+BE", "T30", "BE03"], "T45+BE": ["T30+BE", "T45"]},
    "E5": {"rho0.35 c2": ["rho0.50 c2", "rho0.35 c1"], "rho0.50 c2": ["rho0.35 c2", "rho0.50 c1"],
           "rho0.35 c1": ["rho0.50 c1", "rho0.35 c2"], "rho0.50 c1": ["rho0.35 c1", "rho0.50 c2"], "SECT2": ["rho0.35 c2"]},
}


def e6_nb(v):
    fam = v.rsplit(" ", 1)[0]
    if v.startswith("MF5-a"):
        return {"MF5-a fo>0&vd>=0.10": ["MF5-a fo>0&vd>=0.20", "MF5-a fo>0", "MF5-a vd>=0.10"],
                "MF5-a fo>0": ["MF5-a fo>0&vd>=0.10"], "MF5-a vd>=0.10": ["MF5-a fo>0&vd>=0.10"],
                "MF5-a fo>0&vd>=0.20": ["MF5-a fo>0&vd>=0.10"]}[v]
    return [x for x in df.loc[(df.family == "E6") & df.variant.str.startswith(fam), "variant"].unique() if x != v]


key = df.set_index(["family", "variant", "scope"])["open_delta"]


def plateau(r):
    if r.family == "REF":
        return np.nan
    nbs = e6_nb(r.variant) if r.family == "E6" else NB[r.family][r.variant]
    vals = [key.get((r.family, v, r.scope), np.nan) for v in nbs]
    vals = [v for v in vals if np.isfinite(v)]
    return min(vals) if vals else np.nan


df["plateau_min_nb_delta"] = df.apply(plateau, axis=1)
df["G1"] = df.n_base >= 150
df["G2"] = (df.train_delta > 0) & (df.valid_delta > 0)
df["G3"] = df.open_delta_t >= T_REQ
df["G4"] = (df.up_delta > 0) & (df.down_delta > 0)
df["G5"] = (df.delta_ex_best > 0) & (df.delta_wf_share >= 0.6)
df["G6"] = df.plateau_min_nb_delta > 0
df["G7"] = (df.open_exp > 0) & (df.up_exp > 0) & (df.down_exp > 0)
gcols = [f"G{i}" for i in range(1, 8)]
ref = df.family == "REF"
df.loc[ref, gcols] = False
allp = df[gcols].all(1)
t1 = df.G1 & df.G2 & df.G4 & df.G6 & (df.open_delta_t >= 2.0) & ~allp
df["route"] = np.where(ref, "reference", np.where(allp, "primary-candidate (lead locked look)", np.where(t1, "testing-1", "backlog")))
df.to_csv(HERE / "results.csv", index=False, float_format="%.4f")

fin = []
for fam in ("E1", "E2", "E3", "E4", "E5", "E6"):
    x = df[(df.family == fam) & df.G1 & (df.train_delta > 0)].sort_values("train_delta_t", ascending=False).head(3)
    fin.append(x.assign(why="top-3 train delta t"))
    fin.append(df[(df.family == fam) & df.G1 & df.G2 & df.G3 & df.G4].assign(why="passes G1-G4"))
fin = pd.concat(fin).drop_duplicates(["family", "variant", "scope"], keep="first")
fin.to_csv(HERE / "finalists.csv", index=False, float_format="%.4f")

summ = {"n_configs": int(len(df)), "N_STUDY": N_STUDY, "t_required": round(T_REQ, 3),
        "per_family": df.groupby("family").size().to_dict(),
        "routes": df.route.value_counts().to_dict(),
        "pass_G1_G4": df[df.G1 & df.G2 & df.G3 & df.G4][["family", "variant", "scope"]].values.tolist(),
        "testing1": df[df.route == "testing-1"][["family", "variant", "scope"]].values.tolist(),
        "primary": df[df.route.str.startswith("primary")][["family", "variant", "scope"]].values.tolist()}
json.dump(summ, open(HERE / "summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
pd.set_option("display.width", 250, "display.max_rows", 500, "display.max_columns", 40)
show = ["family", "variant", "scope", "n_base", "n_kept", "train_n", "train_exp", "train_delta", "train_delta_t", "valid_n",
        "valid_exp", "valid_delta", "valid_delta_t", "open_exp", "open_t", "open_delta", "open_delta_t", "up_delta",
        "down_delta", "delta_wf_share", "plateau_min_nb_delta", "route"]
print(fin[show + ["why"]].round(3).to_string(index=False))
