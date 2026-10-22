"""ns3var1022 exploratory rows, added AFTER the pre-declared grid was scored (counted: 3; PLAN.md lists 73):
X1 stop 2.0x wider at the same $ risk, same price target (does the B7 trend continue?); X2 the parent window
09:50-11:30 (D4) with the 1.5x stop (B7); X3 daily ATR >= 3% (A6, the best single filter by diff-t) with the 1.5x stop.
Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import variants as V
from load import build
from nv import HERE


def main():
    df, P, Q = build()
    S = V.specs(df, P)
    p0 = V.as_run(df, P, Q, S["P0"])
    pst = V.stats(p0, p0)
    n_study = 76
    n_lin = V.N_LINEAGE_PRIOR + n_study
    b7 = S["B7 stop1.5x same tgt"]["exit"]
    X = {
        "X1 stop2.0x same tgt": {**S["P0"], "fam": "X", "exit": {**V.DEF_EXIT, "kd": 2.0, "ku": 1.0},
                                 "desc": "stop 2x wider, same $ risk, same price target (post-hoc)"},
        "X2 D4 0950-1130 + B7 stop1.5x same tgt": {**S["D4 0950-1130"], "fam": "X", "exit": b7,
                                                   "desc": "parent window 09:50-11:30 with refire + 1.5x stop (post-hoc)"},
        "X3 A6 atr%>=3 + B7 stop1.5x same tgt": {**S["A6 atr%>=3"], "fam": "X", "exit": b7,
                                                 "desc": "daily ATR >= 3% + 1.5x stop (post-hoc)"},
    }
    rows = []
    for name, sp in X.items():
        t = V.as_run(df, P, Q, sp)
        o = V.stats(t, p0)
        rows.append({"variant": name, "fam": "X", "desc": sp["desc"], **o, **V.judge(o, pst, n_study, n_lin)})
        print(name, len(t), round(o["train_avg"], 4), round(o["valid_avg"], 4), flush=True)
    pd.DataFrame(rows).to_csv(HERE / "explore.csv", index=False, float_format="%.4f")
    c = json.load(open(HERE / "counts.json"))
    c.update({"exploratory_post_hoc": 3, "configs_counted_total": c["configs_counted"] + 3,
              "study_bar_total": round(V.t_req(c["configs_counted"] + 3), 3),
              "lineage_N_total": V.N_LINEAGE_PRIOR + c["configs_counted"] + 3,
              "lineage_bar_total": round(V.t_req(V.N_LINEAGE_PRIOR + c["configs_counted"] + 3), 3)})
    json.dump(c, open(HERE / "counts.json", "w"), indent=1)


if __name__ == "__main__":
    main()
