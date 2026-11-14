"""OBS-LR8 (Observer 2026-11-14): how LR8 (live cost model in pnl_adj from 2026-11-12) shifts live R, per account and
by exit kind. Input: scripts/recompute_pnl_adj.py CSV (journals read-only) for Primary, Testing A, Gen, Graveyard.
Columns r_raw (pnl / risk), r_booked (pnl_adj as booked), r_lr8 (as if LR8 applied). 0 configs.
Educational only - not financial advice. usage: python lr8check.py <pnl_adj_lr8.csv>"""
import sys, pandas as pd
d = pd.read_csv(sys.argv[1]); d["post"] = d.date >= "2026-11-12"; d["cost"] = d.r_raw - d.r_lr8
d["acct"] = d.journal.str.extract(r"(mcf-data[\w-]*)")[0]
d["kind"] = d.exit_reason.where(d.exit_reason.isin(["stop", "target", "flatten"]), "other")
g = d.groupby(["acct", "post"]).agg(n=("r_raw", "size"), raw=("r_raw", "mean"), booked=("r_booked", "mean"), lr8=("r_lr8", "mean"))
g["booked_minus_lr8"] = g.booked - g.lr8; print(g.round(4).to_string())
p = d[d.post]; print(f"post-11-12: share |booked - lr8| > 0.01R = {((p.r_booked - p.r_lr8).abs() > 0.01).mean():.3f}")
print(d.groupby(["kind", "post"]).agg(n=("cost", "size"), lr8_cost=("cost", "mean"), med=("cost", "median")).round(4).to_string())
pre, post = d[~d.post], d[d.post]; w = pre.kind.value_counts(normalize=True)
print("exit mix pre/post:", pre.kind.value_counts(normalize=True).round(3).to_dict(), post.kind.value_counts(normalize=True).round(3).to_dict())
print(f"LR8 cost per trade: pre {pre.cost.mean():.4f}; post {post.cost.mean():.4f}; post at PRE exit mix {(post.groupby('kind').cost.mean() * w).sum():.4f}")
