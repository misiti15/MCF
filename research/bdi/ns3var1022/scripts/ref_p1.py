"""ns3var1022 reference rows (NOT counted, PLAN.md): P1 = the windowed parent NS3-failed-vwap-reclaim-short as it runs
in Testing 1 (09:50-11:30, no refire, t1s1, 3 lots); and the extra numbers for the near-miss V1 (by year, days,
without the best day, trades per day). Educational only - not financial advice."""
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
    tod = df["tod"].to_numpy()
    p1 = V.as_run(df, P, Q, {**S["P0"], "mask": df["p0"].to_numpy() & (tod <= 1130), "run": {**V.DEF_RUN, "refire": False}})
    v1 = V.as_run(df, P, Q, {**S["P0"], "mask": df["p0"].to_numpy() & (tod <= 1130),
                              "exit": {**V.DEF_EXIT, "kd": 2.0, "ku": 1.0}})
    out = {}
    for name, t in (("P0", p0), ("P1 parent NS3 (Testing 1 shape)", p1), ("V1 NS3V1-am-widestop-short", v1)):
        o = V.stats(t, p0)
        y = pd.to_datetime(t["date"]).dt.year
        dd = t.groupby("date")["r"].sum()
        b = dd.idxmax()
        out[name] = {"n": len(t), "days": int(dd.size), "per_day": round(len(t) / 431, 2),
                     "train_avg": round(o["train_avg"], 4), "valid_avg": round(o["valid_avg"], 4), "t": round(o["all_t"], 2),
                     "excess_train": round(o["train_excess"], 4), "excess_valid": round(o["valid_excess"], 4),
                     "by_year_avg": {int(k): round(float(g.mean()), 4) for k, g in t["r"].groupby(y)},
                     "by_year_n": {int(k): int(g.size) for k, g in t["r"].groupby(y)},
                     "total_r": round(float(t["r"].sum()), 1), "best_day": str(b), "best_day_r": round(float(dd.max()), 1),
                     "avg_ex_best_day": round(float(t.loc[t["date"] != b, "r"].mean()), 4),
                     "worst_day": str(dd.idxmin()), "worst_day_r": round(float(dd.min()), 1),
                     "win_rate": round(float((t["r"] > 0).mean()), 3),
                     "regime_avg_2y": {g: round(o[f"all_{g}_avg"], 4) for g in V.REG},
                     "regime_n_2y": {g: int(o[f"all_{g}_n"]) for g in V.REG},
                     "regime_avg_train": {g: round(o[f"train_{g}_avg"], 4) for g in V.REG},
                     "regime_avg_valid": {g: round(o[f"valid_{g}_avg"], 4) for g in V.REG}}
    json.dump(out, open(HERE / "reference_rows.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
    pd.to_pickle(v1, V.NV / "v1_trades.pkl")


if __name__ == "__main__":
    main()
