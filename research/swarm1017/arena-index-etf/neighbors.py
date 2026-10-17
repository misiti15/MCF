"""Amendment-1 neighbour grid around the single quality pass (54 configurations, counted). Educational only - not financial advice."""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine import Panel, cond_mat, first_trades, stats_split, trade_frame  # noqa: E402

from mcf.research import gates  # noqa: E402

P = Panel(sys.argv[1])
A = P.A
tr = (pd.to_datetime(A["date"]).dt.strftime("%Y-%m") <= "2025-12").to_numpy()
q = lambda n, p: float(np.nanquantile(A.loc[tr, n].to_numpy(float), p))
cache, out = {}, []
R3 = {"a1": [0.05, 0.2], "a2": [-0.7977116525173187, -1.2]}[sys.argv[2]]
for r3, di, atr, g in itertools.product(R3, [0.5, 0.8, None], [0.5, 0.8, 0.95], ["t05s1", "t1s1", "t1s05"]):
    cs = [("ret3", "<=", q("ret3", r3) if r3 > 0 else r3), ("atr_d_pct", ">=", q("atr_d_pct", atr))]
    if di is not None:
        cs.append(("di_diff7", ">=", q("di_diff7", di)))
    M = P.win_mask((1400, 1500))[None, :]
    for c in cs:
        M = M & cond_mat(P, cache, c)
    sd, k, r, c, e = first_trades(P, M, f"long_{g}")
    t = trade_frame(P, sd, k, r, c, e)
    a, b = stats_split(P, sd, r, c, e, 0), stats_split(P, sd, r, c, e, 1)
    reg = gates.regime_split(t[["date", "r"]], P.regimes_df)
    wf = gates.walk_forward(t[["date", "r"]], exclude_months=("2024-11", "2024-12", "2025-01", "2025-02"))
    out.append({"ret3_q": r3, "di_q": di, "atr_q": atr, "geom": g, "tr_n": a["n"], "tr_exp": a["exp"], "tr_t": a["t"],
                "va_n": b["n"], "va_exp": b["exp"], "va_t": b["t"], "va_exc_e": b.get("exc_e"),
                "up": reg["up"].get("exp_r"), "down": reg["down"].get("exp_r"), "wf": wf["share_positive"]})
X = pd.DataFrame(out)
X.to_csv(HERE / f"neighbors_{sys.argv[2]}.csv", index=False, float_format="%.4g")
pd.set_option("display.width", 200)
print(X.to_string())
print("valid>0:", int((X.va_exp > 0).sum()), "of", len(X), "| train>0 & valid>0 & up>0 & down>0:",
      int(((X.tr_exp > 0) & (X.va_exp > 0) & (X.up > 0) & (X.down > 0)).sum()))
