"""gates1021: concentration checks for the B2 picks and the best Part A tweaks: days in the blocked state, the gate
delta without its single best day, by-quarter sign share, and the delta on random same-minute entries (market-beta
share). Writes robust.csv. Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import HERE
from load import load_sig
from part_b import gate_masks


def main():
    picks = pd.read_csv(HERE / "results_B.csv")
    picks = picks[picks["B2_pick"]]
    sig = load_sig(list(picks["setup"]))
    rows = []
    for _, p in picks.iterrows():
        s = sig[sig["setup"] == p["setup"]].reset_index(drop=True)
        blk = np.asarray(gate_masks(s)[p["gate"]], bool)
        ccol = f"c_{p['side']}_{p['geom']}"
        contrib = pd.Series(-s["r"].to_numpy() * blk).groupby(s["date"].to_numpy()).sum()
        n = len(s)
        best = contrib.idxmax()
        q = pd.PeriodIndex(pd.to_datetime(pd.Series(contrib.index)), freq="Q")
        byq = contrib.groupby(q.to_numpy()).sum()
        c = s[ccol].to_numpy(float)
        ctrl = float(np.nansum(-c * blk) / n)
        rows.append({"setup": p["setup"], "gate": p["gate"], "verdict": p["verdict"],
                     "blocked_days": int(pd.Series(s["date"][blk]).nunique()), "days": int(s["date"].nunique()),
                     "delta_all": round(float(contrib.sum() / n), 4),
                     "delta_ex_best_day": round(float((contrib.sum() - contrib[best]) / n), 4), "best_day": str(best),
                     "best_day_share": round(float(contrib[best] / contrib.sum()), 3) if contrib.sum() > 0 else None,
                     "quarters_positive": f"{int((byq > 0).sum())}/{len(byq)}",
                     "ctrl_delta_all": round(ctrl, 4),
                     "beta_share": round(ctrl / float(contrib.sum() / n), 2) if contrib.sum() > 0 else None,
                     "gated_exp_all": round(float(s["r"][~blk].mean()), 4), "parent_exp_all": round(float(s["r"].mean()), 4)})
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "robust.csv", index=False)
    pd.set_option("display.width", 250)
    print(df.to_string())


if __name__ == "__main__":
    main()
