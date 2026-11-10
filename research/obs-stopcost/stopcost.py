"""Observer: where would a minimum stop width (STOPW) bite first? Per-setup stop width and cost share, live paper journals
(all 7 accounts, run_id 1, 2026-10-06..11-06, trades joined to their signal as in research/skeptic-20261109/costgap.py).
Lab cost model copied from costgap.py (entry (1c+1bp)xtod + 4.4bp x tod; exit 1c+1bp; stops +2c). Descriptive, 0 configs.
Also: entry slip by entry type / fill tag, to see whether paper fills flatter tight-stop setups.
usage: python stopcost.py <journal_dir>. Educational only - not financial advice."""
import sys, glob, os, json, sqlite3, numpy as np, pandas as pd
pd.set_option("display.width", 250)
TOD = ((935, 3.8), (950, 2.1), (1030, 1.4))
mult = lambda t: next((m for e, m in TOD if t < e), 1.0)
R = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.db"))):
    if "_" in os.path.basename(f): continue
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("journal", "primary"); c = sqlite3.connect(f)
    t = pd.read_sql("select t.date,t.symbol,t.strategy,t.side,t.entry,t.stop,t.exit,t.exit_reason,t.shares,t.pnl,t.pnl_adj,t.meta,"
                    "s.ref_price,s.entry_type,s.info from trades t join signals s on s.broker_order_id=t.broker_order_id "
                    "where t.run_id=1 and s.run_id=1 and t.date between '2026-10-06' and '2026-11-06' and t.exit is not null", c)
    t["acct"] = a; R.append(t)
T = pd.concat(R, ignore_index=True)
info = T["info"].map(lambda s: json.loads(s) if s else {})
T["bar_time"] = info.map(lambda d: int(d.get("bar_time") or 0))
T["risk"] = (T.entry - T.stop).abs(); T = T[(T.risk > 0) & T.ref_price.notna()].copy()
T["stop_bps"] = T.risk / T.entry * 1e4
T["stop_x"] = T.exit_reason.fillna("").str.contains("stop")
T["lab_cost"] = ((0.01 + T.entry * 1e-4) * T.bar_time.map(mult) + 4.4e-4 * T.entry * T.bar_time.map(mult)
                 + 0.01 + T.entry * 1e-4 + np.where(T.stop_x, 0.02, 0)) / T.risk
T["e_slip_R"] = T.side * (T.entry - T.ref_price) / T.risk
T["e_bps"] = T.side * (T.entry - T.ref_price) / T.ref_price * 1e4
T["net"] = T.pnl_adj / (T.risk * T.shares)
T["x_slip_R"] = np.where(T.stop_x, T.side * (T.stop - T.exit), 0.0) / T.risk
T["live_cost"] = T.e_slip_R + T.x_slip_R + (T.pnl - T.pnl_adj) / T.shares / T.risk   # paper cost already inside net (costgap.py)
T["fill_tag"] = T.meta.fillna("").str.extract(r";(\w+)$")[0].fillna("none")
print(f"trades {len(T)}, {T.date.min()}..{T.date.max()}, setups {T.strategy.nunique()}")
print("\n[A] entry slip by entry type x fill tag (bps, + = adverse), and by stop quartile:")
T["q"] = pd.qcut(T.stop_bps, 4, labels=["Q1 tight", "Q2", "Q3", "Q4 wide"])
# note: touch_fill = target exits (reconcile.py), so its net is winners by construction
print(T.groupby(["entry_type", "fill_tag"]).agg(n=("e_bps", "size"), e_bps_mean=("e_bps", "mean"), e_bps_med=("e_bps", "median"), net=("net", "mean")).query("n>=50").round(3).to_string())
print(T.groupby(["q", "entry_type"], observed=True).agg(n=("e_bps", "size"), e_bps_mean=("e_bps", "mean"), share_neg_slip=("e_bps", lambda x: (x < -1).mean())).round(3).to_string())
g = T.groupby("strategy").agg(n=("net", "size"), accts=("acct", lambda s: ",".join(sorted(set(s)))), stop_bps_med=("stop_bps", "median"),
                              lt60=("stop_bps", lambda x: (x < 60).mean()), lt100=("stop_bps", lambda x: (x < 100).mean()),
                              lab_cost=("lab_cost", "mean"), live_cost=("live_cost", "mean"), net=("net", "mean"), days=("date", "nunique"))
g["gross"] = g.net + g.live_cost             # before the paper costs already inside net
g["net_lab"] = g.gross - g.lab_cost          # what the same trades would net under the (heavier) lab cost model
g["cost_share"] = np.where(g.gross > 0, g.lab_cost / g.gross, np.nan)
G = g[g.n >= 30].sort_values("stop_bps_med")
print(f"\n[B] setups with >= 30 trades: {len(G)}; tightest 25 by median stop (gross = net + paper cost; net_lab = gross - lab cost):")
print(G.head(25)[["n", "accts", "stop_bps_med", "lt60", "lt100", "lab_cost", "live_cost", "gross", "net", "net_lab"]].round(3).to_string())
print("\n[C] where STOPW bites (share of each setup's trades with stop < 60 / 100 bp), top 15 by trades affected at 100bp:")
G["aff100"] = G.n * G.lt100
print(G.sort_values("aff100", ascending=False).head(15)[["n", "accts", "stop_bps_med", "lt60", "lt100", "lab_cost", "live_cost", "gross", "net", "net_lab"]].round(3).to_string())
print("\n[D] 'cost-killed': gross (before costs) > 0 but net under the lab cost model < 0:")
K = G[(G.gross > 0) & (G.net_lab < 0)].sort_values("lab_cost", ascending=False)
print(K[["n", "accts", "stop_bps_med", "lt100", "lab_cost", "live_cost", "gross", "net", "net_lab", "cost_share"]].round(3).to_string())
print("\n[E] setups that lose BEFORE costs (gross <= 0): wider stops cannot fix these:", int((G.gross <= 0).sum()), "of", len(G),
      "| trades", int(G[G.gross <= 0].n.sum()), "of", int(G.n.sum()))
print("\n[F] by stop quartile (all trades): live cost, lab cost, gross, net")
print(T.assign(gross=T.net + T.live_cost).groupby("q", observed=True).agg(n=("net", "size"), stop_bps=("stop_bps", "median"), live_cost=("live_cost", "mean"),
      lab_cost=("lab_cost", "mean"), gross=("gross", "mean"), net=("net", "mean")).round(3).to_string())
print(f"\ncost-killed setups: {len(K)} of {len(G)}; their median stop {K.stop_bps_med.median():.0f}bp vs all {G.stop_bps_med.median():.0f}bp")
print("Educational only - not financial advice.")
