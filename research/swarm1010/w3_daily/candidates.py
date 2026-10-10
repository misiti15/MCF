"""Extra checks for the 4 gate-passing configurations (no new configurations: same rules, more statistics).
Walk-forward share (gates.walk_forward, 3m/1m, locked months excluded), ex-best-session, busiest-session share,
2x-cost sensitivity, and the live-probation bar items that apply to daily holds. Writes candidates.csv and
data/trades_<id>.parquet (git-ignored). Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd

import study as S
from mcf.research.gates import walk_forward

LK = ["2024-11", "2024-12", "2025-01", "2025-02"]
above = (S.C > S.sma200).to_numpy()
CANDS = {
    "F2_rsi3_5_O_SMA5_L": lambda: S.make_trades(above & (S.rsi3 < 5).to_numpy(), 1, "O", "SMA5", elig=S.ELIG200),
    "F2_rsi3_5_C_SMA5_L": lambda: S.make_trades(above & (S.rsi3 < 5).to_numpy(), 1, "C", "SMA5", elig=S.ELIG200),
    "F2_rsi3_5_O_K5_L": lambda: S.make_trades(above & (S.rsi3 < 5).to_numpy(), 1, "O", "K", k=5, elig=S.ELIG200),
    "F3_rev5_bot_k20_L": lambda: S.make_trades(S.xs_decile(S.ret5, S.ELIG200, False), 1, "C", "K", k=20, elig=S.ELIG200),
}
rows = []
for cid, fn in CANDS.items():
    t = fn()
    t["excess"] = t.gross - S.bench(t)
    t["symbol"] = S.syms[t.j.to_numpy()]
    t["cost"] = t.gross - t.net
    t[["date", "symbol", "ep", "xp", "gross", "net", "excess", "hold"]].assign(exit_date=S.dates[t.xi.to_numpy()]) \
        .to_parquet(S.HERE / "data" / f"trades_{cid}.parquet", index=False)
    tr = pd.DataFrame({"date": t.date, "r": t.net})
    wf = walk_forward(tr, exclude_months=LK)
    wfx = walk_forward(pd.DataFrame({"date": t.date, "r": t.excess}), exclude_months=LK)
    g = t.groupby("date")["net"].agg(["sum", "size"])
    b = g["sum"].idxmax()
    ex_best = (g["sum"].sum() - g.loc[b, "sum"]) / (len(t) - g.loc[b, "size"])
    v2 = t[t.date >= "2025-03-01"]
    rows.append({"id": cid, "n": len(t), "exp_bps": round(t.net.mean() * 1e4, 1),
                 "exp_bps_2x_cost": round((t.net - t.cost).mean() * 1e4, 1),
                 "valid2_exp_bps_2x_cost": round((v2.net - v2.cost).mean() * 1e4, 1),
                 "excess_bps": round(t.excess.mean() * 1e4, 1), "avg_cost_bps": round(t.cost.mean() * 1e4, 1),
                 "wf_share_pos": wf["share_positive"], "wf_folds": wf["n_folds"], "wf_share_pos_excess": wfx["share_positive"],
                 "ex_best_session_bps": round(ex_best * 1e4, 1), "busiest_session_share": round(g["size"].max() / len(t), 4),
                 "busiest_session": str(g["size"].idxmax().date()), "median_price": round(float(t.ep.median()), 1),
                 "max_entries_one_session": int(pd.Series(1, index=t.index).groupby(t.date).sum().max())})
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(S.HERE / "candidates.csv", index=False)
