"""Extra checks (no new configurations) for the A/B finalists picked by the NOTES 1.8 rule and their closest
full-sample runners-up: ex-best-session, busiest-session share, 2x cost, per-year net, and the trades the filter
removed from the parent (same sample). Writes checks_ab.csv. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import study_ab as AB  # noqa: E402

S = AB.S
above = (AB.C > S["sma200"]).to_numpy()
b35 = above & (S["rsi3"] < 5).to_numpy()
rev5 = S["xs_decile"](S["ret5"], AB.ELIG200, False)
FA = AB.filters("A"); FB = AB.filters("B")
mat = AB.as_mat


def A(sig):
    return S["make_trades"](sig, 1, "O", "SMA5", elig=AB.ELIG200)


def B(sig):
    return S["make_trades"](sig, 1, "C", "K", k=20, elig=AB.ELIG200)


D19 = AB.D19[:, None]
CANDS = {
    "A_b35_VP30": (lambda: A(b35 & mat(FA["VP30"][0])), lambda: A(b35), 5, False),
    "A_b35_TR90": (lambda: A(b35 & mat(FA["TR90"][0])), lambda: A(b35), 5, False),
    "B_k20_TR95+SV20": (lambda: B(rev5 & mat(FB["TR95"][0]) & FB["SV20"][0] & D19), lambda: B(rev5 & D19), 20, True),
    "B_k20_TR90": (lambda: B(rev5 & mat(FB["TR90"][0])), lambda: B(rev5), 20, False),
}
rows = []
for cid, (fn, parent_fn, hold, u19) in CANDS.items():
    t, p = fn(), parent_fn()
    t["excess"] = t.gross - S["bench"](t)
    p["excess"] = p.gross - S["bench"](p)
    t["cost"] = t.gross - t.net
    g = t.groupby("date")["net"].agg(["sum", "size"])
    b = g["sum"].idxmax()
    ex_best = (g["sum"].sum() - g.loc[b, "sum"]) / (len(t) - g.loc[b, "size"])
    key = ["i", "j"]
    removed = p.merge(t[key], on=key, how="left", indicator=True)
    removed = removed[removed._merge == "left_only"]
    yrs = {f"net_{y}": round(float(x.net.mean() * 1e4), 1) for y, x in t.groupby(t.date.dt.year)}
    rows.append({"id": cid, "sample": "2019+" if u19 else "2016+", "n": len(t), "exp_bps": round(t.net.mean() * 1e4, 1),
                 "excess_bps": round(t.excess.mean() * 1e4, 1), "exp_2x_cost_bps": round((t.net - t.cost).mean() * 1e4, 1),
                 "ex_best_session_bps": round(ex_best * 1e4, 1), "busiest_session_share": round(g["size"].max() / len(t), 4),
                 "busiest_session": str(g["size"].idxmax().date()), "active_sessions": int(t.i.nunique()),
                 "parent_n": len(p), "parent_exp_bps": round(p.net.mean() * 1e4, 1),
                 "parent_excess_bps": round(p.excess.mean() * 1e4, 1),
                 "removed_n": len(removed), "removed_exp_bps": round(removed.net.mean() * 1e4, 1),
                 "removed_excess_bps": round(removed.excess.mean() * 1e4, 1), **yrs})
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(AB.HERE / "checks_ab.csv", index=False)
