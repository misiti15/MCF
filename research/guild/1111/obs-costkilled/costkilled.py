"""Observer: the cost-killed setups, lab cost charge vs what live paper fills actually cost them (Lead lead-20261110-2100-2).
Same join and cost model as research/skeptic-20261109/costgap.py and obs-stopcost (journals, all 7 accounts, run_id 1, trades joined to
their signal). Per setup: n, days, gross (= net + paper cost already inside net), live paper cost, lab cost charge, lab net (= gross - lab
cost), live net, live net without its best day, best-day share. 'Cost-killed' = gross > 0 and lab net < 0 (obs-stopcost definition),
recomputed on the window given. Descriptive, 0 configs. usage: python costkilled.py <journal_dir> <start> <end>. Educational only - not financial advice."""
import sys, glob, os, json, sqlite3, numpy as np, pandas as pd
pd.set_option("display.width", 250)
J, A, B = sys.argv[1], sys.argv[2], sys.argv[3]
TOD = ((935, 3.8), (950, 2.1), (1030, 1.4)); mult = lambda t: next((m for e, m in TOD if t < e), 1.0)
R = []
for f in sorted(glob.glob(os.path.join(J, "*.db"))):
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("mcf-data", "primary")
    t = pd.read_sql("select t.date,t.symbol,t.strategy,t.side,t.entry,t.stop,t.exit,t.exit_reason,t.shares,t.pnl,t.pnl_adj,"
                    "s.ref_price,s.info from trades t join signals s on s.broker_order_id=t.broker_order_id "
                    f"where t.run_id=1 and s.run_id=1 and t.date between '{A}' and '{B}' and t.exit is not null", sqlite3.connect(f))
    t["acct"] = a; R.append(t)
T = pd.concat(R, ignore_index=True)
T["bar_time"] = T["info"].map(lambda s: int((json.loads(s) if s else {}).get("bar_time") or 0))
T["risk"] = (T.entry - T.stop).abs(); T = T[(T.risk > 0) & T.ref_price.notna()].copy()
stop_x = T.exit_reason.fillna("").str.contains("stop")
T["net"] = T.pnl_adj / (T.risk * T.shares)
T["e_cost"] = T.side * (T.entry - T.ref_price) / T.risk
T["x_cost"] = np.where(stop_x, T.side * (T.stop - T.exit), 0.0) / T.risk
T["adj_cost"] = (T.pnl - T.pnl_adj) / T.shares / T.risk
T["live_cost"] = T.e_cost + T.x_cost + T.adj_cost
T["lab_cost"] = ((0.01 + T.entry * 1e-4) * T.bar_time.map(mult) + 4.4e-4 * T.entry * T.bar_time.map(mult) + 0.01 + T.entry * 1e-4 + np.where(stop_x, 0.02, 0)) / T.risk
T["gross"] = T.net + T.live_cost; T["lab_net"] = T.gross - T.lab_cost
def agg(g):
    d = g.groupby("date").net.sum(); best = d.idxmax(); wo = g[g.date != best].net
    return pd.Series(dict(n=len(g), days=g.date.nunique(), accts=",".join(sorted(set(g.acct))), stop_bps=(g.risk / g.entry * 1e4).median(),
                          gross=g.gross.mean(), e_cost=g.e_cost.mean(), x_cost=g.x_cost.mean(), adj_cost=g.adj_cost.mean(), live_cost=g.live_cost.mean(),
                          lab_cost=g.lab_cost.mean(), lab_net=g.lab_net.mean(), live_net=g.net.mean(), live_net_wo_best=wo.mean(),
                          best_share=d.max() / d.sum() if d.sum() > 0 else np.nan, total_live=g.net.sum()))
S = T.groupby("strategy").apply(agg); S = S[S.n >= 30]
K = S[(S.gross > 0) & (S.lab_net < 0)].sort_values("live_net", ascending=False)
print(f"trades {len(T)}, {T.date.min()}..{T.date.max()}, setups with >= 30 trades {len(S)}; cost-killed (gross > 0, lab net < 0): {len(K)}")
print(K.round(3).to_string())
print(f"\ncost-killed pooled: trades {int(K.n.sum())}, live cost {np.average(K.live_cost, weights=K.n):+.3f}R vs lab {np.average(K.lab_cost, weights=K.n):+.3f}R; "
      f"live net {np.average(K.live_net, weights=K.n):+.3f}R; live net > 0: {int((K.live_net > 0).sum())} of {len(K)}; also > 0 w/o best day: {int(((K.live_net > 0) & (K.live_net_wo_best > 0)).sum())}")
print("\nReading: live_cost < lab_cost means paper fills cost less than the lab charges; live_net is net of paper costs only (paper fills are a LOWER")
print("bound on real cost, RESEARCH_RULES 7). Educational only - not financial advice.")
# rule-change context (ledger 2026-10-29-testing-cost-filter-cf, effective 10-30: Testing 1/2 skip entries with stop round-trip cost > 0.15R)
print("\nsurvivors by period around the Owner CF cost filter (effective 2026-10-30, Testing 1/2):")
for s in K[(K.live_net > 0) & (K.live_net_wo_best > 0)].index:
    g = T[T.strategy == s]
    for lab, x in (("before 10-30", g[g.date < "2026-10-30"]), ("from 10-30", g[g.date >= "2026-10-30"])):
        if len(x): print(f"   {s:40s} {lab}: n {len(x)}, days {x.date.nunique()}, gross {x.gross.mean():+.3f}, live cost {x.live_cost.mean():+.3f}, live net {x.net.mean():+.3f}, lab cost {x.lab_cost.mean():+.3f}")
    d = g.groupby("date").net.sum(); print(f"   {s:40s} days positive {int((d > 0).sum())} of {len(d)}; worst day {d.min():+.2f}R, best {d.max():+.2f}R, total {d.sum():+.2f}R")
