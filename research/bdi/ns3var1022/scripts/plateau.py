"""ns3var1022 plateau check around X2 (post-hoc, counted: 19 new rows; declared in NOTES.md before it ran):
stop {1.25, 1.5, 2.0}x at the same $ risk x target {same price, scaled with the stop} x last entry bar {11:00, 11:30,
12:00}, refire cd1 (18, one of them = X2), plus refire off at 11:30 with the 1.5x stop (2). Rule 18: the winner must sit
on a plateau (neighbours positive in train and valid). Educational only - not financial advice."""
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
    c = json.load(open(HERE / "counts.json"))
    n_study = c["configs_counted_total"] + 19
    n_lin = V.N_LINEAGE_PRIOR + n_study
    tod = df["tod"].to_numpy()
    p0m = df["p0"].to_numpy()
    rows = []
    grid = []
    for end in (1100, 1130, 1200):
        for k in (1.25, 1.5, 2.0):
            for tg in ("same", "scaled"):
                grid.append((end, k, tg, True))
    grid += [(1130, 1.5, "same", False), (1130, 1.5, "scaled", False)]
    for end, k, tg, rf in grid:
        name = f"PL end{end} stop{k}x tgt-{tg}" + ("" if rf else " no-refire")
        sp = {"fam": "PL", "mask": p0m & (tod <= end), "exit": {**V.DEF_EXIT, "kd": k, "ku": 1.0 if tg == "same" else k},
              "run": {**V.DEF_RUN, "refire": rf}, "entry": 0, "desc": name}
        t = V.as_run(df, P, Q, sp)
        o = V.stats(t, p0)
        rows.append({"variant": name, "fam": "PL", "desc": name, "end": end, "stop_x": k, "target": tg, "refire": rf,
                     **o, **V.judge(o, pst, n_study, n_lin)})
        print(name, len(t), round(o["train_avg"], 4), round(o["valid_avg"], 4), round(o["best_day_share"], 3), flush=True)
        if name == "PL end1130 stop1.5x tgt-same":
            pd.to_pickle(t, V.NV / "x2_trades.pkl")
    pd.DataFrame(rows).to_csv(HERE / "plateau.csv", index=False, float_format="%.4f")
    new = len(grid) - 1      # end1130 / 1.5x / same / refire = X2, already counted
    c.update({"plateau_post_hoc": new, "configs_counted_total": c["configs_counted_total"] + new,
              "study_bar_total": round(V.t_req(c["configs_counted_total"] + new), 3),
              "lineage_N_total": V.N_LINEAGE_PRIOR + c["configs_counted_total"] + new,
              "lineage_bar_total": round(V.t_req(V.N_LINEAGE_PRIOR + c["configs_counted_total"] + new), 3)})
    json.dump(c, open(HERE / "counts.json", "w"), indent=1)


if __name__ == "__main__":
    main()
