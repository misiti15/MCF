"""gates1021 Part B: B1 short list (market state at entry, stable split) and B2 one check-gate per short-listed
setup. 14 fixed candidate gates x every covered live setup (PLAN.md). Writes results_B.csv (every evaluation),
shortlist_B1.csv, finalists_B2.csv, counts.json. Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import HERE, gates
from load import day_delta, load_sig


def gate_masks(s: pd.DataFrame) -> dict:
    spy, qqq, br, d2, pv = (s[k].to_numpy(float) for k in ("spy_fo", "qqq_fo", "breadth", "d2", "spy_prev"))
    with np.errstate(invalid="ignore"):
        return {
            "U1 spy_fo>=+0.50": spy >= 0.5,
            "U2 spy_fo>=+0.25 & breadth rising": (spy >= 0.25) & (d2 > 0),
            "U3 qqq_fo>=+0.50": qqq >= 0.5,
            "U4 qqq_fo>=+0.25 & breadth rising": (qqq >= 0.25) & (d2 > 0),
            "U5 breadth>=0.65": br >= 0.65,
            "U6 breadth d2>=+0.10": d2 >= 0.10,
            "U7 prior day SPY>=+0.5% & spy_fo>=+0.25": (pv >= 0.5) & (spy >= 0.25),
            "D1 spy_fo<=-0.50": spy <= -0.5,
            "D2 spy_fo<=-0.25 & breadth falling": (spy <= -0.25) & (d2 < 0),
            "D3 qqq_fo<=-0.50": qqq <= -0.5,
            "D4 qqq_fo<=-0.25 & breadth falling": (qqq <= -0.25) & (d2 < 0),
            "D5 breadth<=0.35": br <= 0.35,
            "D6 breadth d2<=-0.10": d2 <= -0.10,
            "D7 prior day SPY<=-0.5% & spy_fo<=-0.25": (pv <= -0.5) & (spy <= -0.25),
        }


def evaluate(s: pd.DataFrame, blk: np.ndarray, ccol: str) -> dict:
    out = {}
    for sp in ("train", "valid", "all"):
        m = np.ones(len(s), bool) if sp == "all" else (s["split"].to_numpy() == sp)
        par = s[m]
        b = blk[m]
        kept = par[~b]
        n = len(par)
        out[f"{sp}_n"] = n
        out[f"{sp}_blocked_pct"] = round(100 * b.mean(), 2) if n else None
        out[f"{sp}_parent_exp"] = round(float(par["r"].mean()), 4) if n else None
        out[f"{sp}_gated_exp"] = round(float(kept["r"].mean()), 4) if len(kept) else None
        out[f"{sp}_in_state_exp"] = round(float(par["r"][b].mean()), 4) if b.any() else None
        dd = day_delta(kept, par)
        out[f"{sp}_delta"], out[f"{sp}_delta_t"] = dd["delta"], dd["t"]
        sm = gates.summary(kept[["date", "r"]]) if len(kept) else {}
        out[f"{sp}_gated_t"] = sm.get("t")
        out[f"{sp}_parent_t"] = gates.summary(par[["date", "r"]]).get("t") if n else None
        w = par["r"].to_numpy() > 0
        out[f"{sp}_winners_blocked_pct"] = round(100 * (b & w).sum() / max(1, w.sum()), 2)
        # same gate on the same-minute random control: how much of the delta is plain market beta
        c = par[ccol].to_numpy(float)
        ok = np.isfinite(c)
        out[f"{sp}_ctrl_delta"] = round(float(-(c * b)[ok].sum() / max(1, ok.sum())), 4)
    ch = s["choppy"].to_numpy(bool)
    par = s[ch]
    out["choppy_n"] = int(ch.sum())
    out["choppy_blocked_pct"] = round(100 * blk[ch].mean(), 2) if ch.any() else None
    out["choppy_delta"] = day_delta(par[~blk[ch]], par)["delta"] if ch.any() else None
    for reg in ("up", "flat", "down"):
        m = s["regime"].to_numpy() == reg
        out[f"{reg}_delta"] = day_delta(s[m & ~blk], s[m])["delta"] if m.any() else None
    kept = s[~blk]
    out["gated_ex_best_day"] = gates.summary(kept[["date", "r"]]).get("ex_best_day") if len(kept) else None
    return out


def main():
    us = pd.read_csv(HERE / "setups_scored.csv")
    sig = load_sig()
    rows = []
    for _, u in us.iterrows():
        s = sig[sig["setup"] == u["setup"]].sort_values(["date", "tod", "symbol"]).reset_index(drop=True)
        if not len(s):
            rows.append({"setup": u["setup"], "gate": "(no trades)"})
            continue
        ccol = f"c_{u['side']}_{u['geom']}"
        for gname, blk in gate_masks(s).items():
            r = {"setup": u["setup"], "names": u["names"], "accounts": u["accounts"], "side": u["side"],
                 "geom": u["geom"], "module": u["module"], "window": u["window"], "min_adv": u["min_adv"],
                 "refire": u["refire"], "gate": gname, **evaluate(s, np.asarray(blk, bool), ccol)}
            rows.append(r)
    res = pd.DataFrame(rows)
    n_setups = int(res.loc[res["gate"] != "(no trades)", "setup"].nunique())
    N = 32 + 14 * n_setups
    bar = gates.t_required(N)
    # B1: real, stable split
    b1 = (res["train_blocked_pct"] >= 3) & (res["valid_blocked_pct"] >= 3) & (res["train_delta"] > 0) & \
         (res["valid_delta"] > 0) & (res["train_delta_t"] >= 2.0) & (res["valid_delta_t"] >= 1.0)
    res["B1_stable_split"] = b1
    # B2: one gate per short-listed setup = highest train delta t among B1 states blocking <= 20% of train trades
    res["B2_pick"] = False
    for sname, g in res[b1 & (res["train_blocked_pct"] <= 20)].groupby("setup"):
        res.loc[g["train_delta_t"].idxmax(), "B2_pick"] = True
    res["acc_participation"] = (res["train_blocked_pct"] <= 20) & (res["valid_blocked_pct"] <= 20)
    res["acc_beats_parent"] = (res["train_gated_exp"] > res["train_parent_exp"]) & \
                              (res["valid_gated_exp"] > res["valid_parent_exp"])
    res["acc_bar"] = res["all_delta_t"] >= bar
    res["verdict"] = np.where(res["B2_pick"] & res["acc_participation"] & res["acc_beats_parent"] & res["acc_bar"],
                              "finalist", np.where(res["B2_pick"] & res["acc_participation"] & res["acc_beats_parent"],
                                                   "near-miss (t below bar)", ""))
    res.to_csv(HERE / "results_B.csv", index=False)
    res[b1].to_csv(HERE / "shortlist_B1.csv", index=False)
    res[res["B2_pick"]].to_csv(HERE / "finalists_B2.csv", index=False)
    json.dump({"part_a_configs": 32, "part_b_setups_scored": n_setups, "part_b_gates_per_setup": 14,
               "part_b_configs": 14 * n_setups, "N_total": N, "bar": bar,
               "b1_states_stable": int(b1.sum()), "b1_setups": int(res.loc[b1, "setup"].nunique()),
               "b2_picks": int(res["B2_pick"].sum()), "finalists": int((res["verdict"] == "finalist").sum())},
              open(HERE / "counts.json", "w"), indent=1)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(json.load(open(HERE / "counts.json")))
    print(res[b1][["setup", "gate", "train_blocked_pct", "valid_blocked_pct", "train_parent_exp", "train_gated_exp",
                   "valid_parent_exp", "valid_gated_exp", "train_delta_t", "valid_delta_t", "all_delta_t", "choppy_delta",
                   "valid_ctrl_delta", "B2_pick", "verdict"]].to_string())


if __name__ == "__main__":
    main()
