"""Robustness for the finalists: per half-year expectancy, deflated Sharpe at the lineage N, quarter table.
Educational only - not financial advice."""
import ast
import json

import numpy as np
import pandas as pd

from common import F, HERE, WM, core, pick, trades
from mcf.research import gates

FN = pd.read_csv(HERE / "finalists.csv")
J = json.load(open(HERE / "gate_summary.json"))
out = []
for i, r in FN.iterrows():
    m = core(r.parent, ast.literal_eval(r.th))
    if isinstance(r.filters, str):
        for f in r.filters.split("+"):
            m = m & F[f]
    idx = pick(m & WM[r.win], r.side, r.geom, bool(r.refire))
    t = trades(idx, r.side, r.geom)
    h = pd.to_datetime(t.date)
    half = np.where(h < "2025-07-01", "25H1", np.where(h < "2026-01-01", "25H2", np.where(h < "2026-07-01", "26H1", "26H2")))
    hs = t.groupby(half)["r"].agg(["mean", "size"]).round(3)
    daily = t.groupby("date")["r"].sum()
    ds = gates.deflated_sharpe(daily.to_numpy(), J["n_lineage"])
    per_day = len(t) / 426
    out.append({"i": i, "parent": r.parent, "filters": r.filters, "th": r.th, "geom": r.geom, "win": r.win,
                "halves": {k: (float(v["mean"]), int(v["size"])) for k, v in hs.iterrows()}, "dsr": ds["dsr"],
                "per_day": round(per_day, 2)})
    print(out[-1])
json.dump(out, open(HERE / "robust.json", "w"), indent=1, default=str)
