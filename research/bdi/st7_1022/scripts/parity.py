"""st7_1022 parity checks (PLAN.md): (1) P0 reproduces regime1022 k26; (2) the simulator's t1s1 / t05s1 / t1s05 equal the
frames' lab outcomes; (3) production-cost R equals gates1021 prod_r_tier. Writes parity.json. Educational only."""
import json
import numpy as np
import pandas as pd
from core import load, first_per_symday, p0_cond, simulate, net_r, exit_r
from sc import HERE, RG22, SLIP_PS, gates

cand, part, pc, pp = load()
i0 = first_per_symday(cand, p0_cond(cand))
c0 = cand.loc[i0]
out = {"p0_n": len(i0)}
k = pd.read_parquet(RG22 / "asrun.parquet")
k = k[k.skey == "k26"]
a = set(zip(c0.symbol, c0.date.astype(str), c0.tod)); b = set(zip(k.symbol, k.date.astype(str), k.tod))
out["k26_n"] = len(k); out["same_signals"] = len(a & b)
for g, kw in (("t1s1", {}), ("t05s1", {"ku": 0.5}), ("t1s05", {"kd": 0.5})):
    E = c0.close.to_numpy(float); D = 0.25 * c0.atr_d.to_numpy(float)
    gr, xc, _, _ = simulate(E, D, pc["H"][i0], pc["L"][i0], pc["C"][i0], pc["T"][i0], **({"ku": 1.0} | kw))
    lab = gr - 2 * SLIP_PS / D
    fr = c0[f"r_long_{g}"].to_numpy(float)
    ok = np.isfinite(fr) & np.isfinite(lab)
    out[f"lab_match_{g}"] = round(float((np.abs(lab[ok] - fr[ok]) < 1e-3).mean()), 4)
    out[f"lab_mean_sim_{g}"] = round(float(lab[ok].mean()), 4); out[f"lab_mean_frame_{g}"] = round(float(fr[ok].mean()), 4)
# production R vs prod_r_tier on frame outcome
fr = c0["r_long_t1s1"].to_numpy(float); win = c0["win_long_t1s1"].to_numpy(float)
cl = c0.close.to_numpy(float); atr = c0.atr_d.to_numpy(float); tod = c0.tod.to_numpy(float)
p = gates.prod_r(fr, win, cl, atr, "t1s1", tod=tod)
R = 0.25 * atr; gross = fr + 2 * SLIP_PS / R
t3 = np.where((np.abs(c0.gap.to_numpy(float)) >= 20) | (cl < 5), 3.0, 1.0)
prod = gross - t3 * (gross - p)
sim = exit_r(cand, pc, "t1s1", i0)
out["prod_match_t1s1"] = round(float((np.abs(prod - sim) < 1e-3).mean()), 4)
out["prod_mean_frame"] = round(float(prod.mean()), 4); out["prod_mean_sim"] = round(float(np.nanmean(sim)), 4)
kk = k.set_index(["symbol", "tod"]).assign(d=k.date.astype(str).values)
out["k26_mean_r"] = round(float(k.r.mean()), 4)
mis = np.flatnonzero(np.abs(prod - sim) >= 1e-3)
out["mismatch_examples"] = c0.iloc[mis[:5]][["symbol", "date", "tod"]].astype(str).values.tolist()
print(json.dumps(out, indent=1))
json.dump(out, open(HERE / "parity.json", "w"), indent=1)
