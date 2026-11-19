"""Top-10 pick from the live record (owner 2026-11-19): every setup with >= 20 live trades, all accounts pooled (incl.
Primary), R after costs on the one LR8 basis (r_multiple of the journal export used by every ultimate_1119 round,
2026-10-06..11-18). GEN-* setups are eligible only when their record is not a one-day record (best-day share < 50%).
Rank by total R (the pick) and show the avg-R rank beside it.
    python research/ultimate_1119/top10/live10.py LIVE_TRADES_PARQUET  -> live_top10.json
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
d = pd.read_parquet(sys.argv[1])
rows = []
for s, g in d.groupby("strategy"):
    if len(g) < 20:
        continue
    day = g.groupby("date").r_multiple.sum()
    tot = float(g.r_multiple.sum())
    best = day.idxmax()
    share = float(day.max() / tot) if tot > 0 else None
    rows.append(dict(setup=s, trades=len(g), sessions_traded=int(day.size), first=str(g.date.min()), last=str(g.date.max()),
                     accounts=g.groupby("account").size().to_dict(), win=round(float((g.r_multiple > 0).mean()), 3),
                     avg_r=round(float(g.r_multiple.mean()), 4),
                     avg_r_wo_best_day=round(float(g[g.date != best].r_multiple.mean()), 4), best_day=str(best),
                     best_day_share=round(share, 3) if share is not None else None, total_r=round(tot, 2),
                     worst_day=round(float(day.min()), 2), one_day=bool(share is not None and share >= 0.5),
                     gen=s.startswith("GEN-")))
x = pd.DataFrame(rows)
x["eligible"] = ~(x.gen & x.one_day)
e = x[x.eligible].copy()
e["rank_total_r"] = e.total_r.rank(ascending=False, method="min").astype(int)
e["rank_avg_r"] = e.avg_r.rank(ascending=False, method="min").astype(int)
e = e.sort_values("rank_total_r")
top = e.head(10)
out = {"note": "Educational only - not financial advice. Live record 2026-10-06..2026-11-18, all accounts pooled, LR8 cost basis.",
       "n_with_20_trades": int(len(x)), "n_eligible": int(len(e)),
       "excluded_gen_one_day_above_cut": x[(~x.eligible) & (x.total_r >= top.total_r.min())].sort_values("total_r", ascending=False)[
           ["setup", "trades", "total_r", "avg_r", "best_day_share"]].to_dict("records"),
       "top10": top.to_dict("records"), "next5": e.iloc[10:15].to_dict("records"),
       "top10_by_avg_r_among_eligible": e.sort_values("rank_avg_r").head(10)[["setup", "trades", "avg_r", "total_r",
                                                                                "rank_total_r"]].to_dict("records")}
(HERE / "live_top10.json").write_text(json.dumps(out, indent=1, default=str))
pd.set_option("display.width", 250)
print(top[["setup", "trades", "sessions_traded", "total_r", "avg_r", "avg_r_wo_best_day", "best_day_share", "rank_total_r",
           "rank_avg_r", "worst_day"]].to_string(index=False))
print(pd.DataFrame(out["excluded_gen_one_day_above_cut"]).to_string(index=False))
print(pd.DataFrame(out["top10_by_avg_r_among_eligible"]).to_string(index=False))
