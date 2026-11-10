"""Observer: Setup Generator feature-level live tally (Lead lead-20261109-1658-4). Descriptive, 0 configs.
For every condition in config/account_gen.yaml gen.spec (feature + direction), pool the live paper trades (mcf-data-gen journal,
run_id 1) of all GEN setups that use it: setups, trades, days, avg R, total R, avg R without its best day, best-day share.
Also by side, window, geometry. Words overlap (a setup has 2-4 conditions), so rows are NOT independent.
usage: python genfeat.py <gen_journal.db> [max_date]. Educational only - not financial advice."""
import sys, sqlite3, yaml, numpy as np, pandas as pd
db = sys.argv[1]; MAXD = sys.argv[2] if len(sys.argv) > 2 else "2099-01-01"
Y = yaml.safe_load(open("config/account_gen.yaml"))["strategies"]
t = pd.read_sql("select strategy, date, entry, stop, shares, pnl_adj from trades where run_id=1 and date<=?", sqlite3.connect(db), params=(MAXD,))
t["R"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares).replace(0, np.nan); t = t[t.R.notna()]
print(f"GEN live paper trades {len(t)}, {t.date.min()}..{t.date.max()}, setups traded {t.strategy.nunique()}")
tags = []
for k, v in Y.items():
    sp = (v.get("gen") or {}).get("spec")
    if not k.startswith("GEN-") or not sp: continue
    for f, op, val in sp.get("conds", []):
        tags.append((k, f"{f} {'>=' if op in ('>=', '>') else '<=' if op in ('<=', '<') else op}"))
    tags += [(k, f"side={sp.get('side')}"), (k, f"window={sp.get('window')}"), (k, f"geom={sp.get('geom')}")]
Tg = pd.DataFrame(tags, columns=["strategy", "word"])
untagged = sorted(set(t.strategy) - set(Tg.strategy)); print("traded setups without gen.spec (excluded):", untagged)
X = Tg.merge(t, on="strategy")
def agg(g):
    day = g.groupby("date").R.sum(); best = day.idxmax(); r = g[g.date != best].R
    tot = g.R.sum()
    return pd.Series(dict(setups=g.strategy.nunique(), n=len(g), days=g.date.nunique(), avg=g.R.mean(), total=tot,
                          avg_wo_best=r.mean() if len(r) else np.nan, best_share=day.max() / tot if tot > 0 else np.nan))
A = X.groupby("word").apply(agg)
book = t.R.mean(); A["vs_book"] = A.avg - book
print(f"GEN book avg R {book:+.3f} (all {len(t)} trades)")
ismeta = A.index.str.match(r"^(side|window|geom)=")
meta = A[ismeta].sort_values("avg")
print("\nby side / window / geometry:\n", meta.round(3).to_string())
F = A[~ismeta]
F = F[(F.setups >= 3) & (F.n >= 30)].sort_values("avg")
print(f"\nconditions used by >= 3 setups and >= 30 trades ({len(F)} of {(~ismeta).sum()}), worst first:\n", F.round(3).to_string())
print("\ncarriers (avg > 0 and avg_wo_best > 0):", F[(F.avg > 0) & (F.avg_wo_best > 0)].index.tolist())
print("drains (avg_wo_best <= -0.30):", F[F.avg_wo_best <= -0.30].index.tolist())
