"""regime1022 Part C add-on (NOT in PLAN.md; added after the first Part C run, labelled exploratory and counted):
for the two setups the owner named, trade ONLY when the tape looks bearish at entry (a whitelist, the opposite of the
pre-declared block-gates), plus the hindsight Bear-only upper bound (reference, not a rule). 2 rules x 2 setups = 4
configurations. Writes explore.csv. Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

from asrun import sequence
from part_c import add_state, summ
from rc import HERE, SCR

SETUPS = ("L3-gap-slope-fromopen-FD", "NS3-failed-vwap-reclaim-short-FD")


def main():
    A = add_state(pd.read_parquet(SCR / "asrun.parquet"))
    meta = pd.read_csv(HERE / "setups_scored.csv")
    out = []
    for name in SETUPS:
        k = meta[meta["names"].str.split(",").apply(lambda x: name in x)]["skey"].iloc[0]
        s = A[A["skey"] == k].reset_index(drop=True)
        par = s[s["asrun"]]
        rules = {"X0 parent (as-run)": None,
                 "X1 only when SPY <= -0.25% from open and below its VWAP": (s["spy_fo"] <= -0.25) & (s["spy_vwap"] < 0),
                 "X2 only when SPY <= 0 from open": s["spy_fo"] <= 0,
                 "XH hindsight: only on Bear sessions (reference, not a rule)": s["regime"] == "Bear"}
        for rn, allow in rules.items():
            if allow is None:
                x = par
            else:
                idx = np.flatnonzero(allow.fillna(False).to_numpy())
                sub = s.iloc[idx]
                kk = sequence(sub["date"].astype(str).to_numpy(), sub["tod"].to_numpy(), sub["symbol"].to_numpy(),
                              sub["exit_tod"].to_numpy())
                x = sub[kk]
            r = {"setup": name, "rule": rn}
            for sp in ("train", "valid", "all"):
                xx = x if sp == "all" else x[x["split"] == sp]
                pp = par if sp == "all" else par[par["split"] == sp]
                sm = summ(xx)
                r.update({f"{sp}_n": sm["n"], f"{sp}_kept_pct": round(100 * sm["n"] / max(1, len(pp)), 1),
                          f"{sp}_avg_r": sm["avg_r"], f"{sp}_t": sm["t"], f"{sp}_total_R": round(float(xx["r"].sum()), 1)})
            for lab in ("Bull", "Bear", "Choppy", "Quiet"):
                r[f"{lab}_R"] = round(float(x[x["regime"] == lab]["r"].sum()), 1)
            out.append(r)
    df = pd.DataFrame(out)
    df.to_csv(HERE / "explore.csv", index=False)
    print(df.to_string())


if __name__ == "__main__":
    main()
