import pandas as pd, numpy as np
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
t = pd.read_parquet(X + "live_all.parquet")
for c in ("entry_time", "exit_time"):
    t[c] = pd.to_datetime(t[c], utc=True, format="mixed")
t["hold"] = (t.exit_time - t.entry_time).dt.total_seconds() / 60
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.dt.strftime("%Y-%m-%d %H:%M")
t["ex"] = t.exit_reason.str.replace("scaled+", "", regex=False).replace({"breakeven": "stop", "timestop": "flatten/time", "flatten": "flatten/time", "spy_exit": "flatten/time"})
t["tgt_r"] = (t.target - t.entry).abs() / (t.entry - t.stop).abs()
t["side_s"] = np.where(t.side == 1, "long", "short")
t["cost_bps"] = t.cost_usd / t.notional * 1e4
d = t.drop_duplicates("k").copy()
d = d[d.r.notna() & np.isfinite(d.r)]
print("dedup trades", len(d), "of", len(t))

def card(g):
    o = {"n": len(g), "setups": g.strategy.nunique(), "symbols": g.symbol.nunique(), "avgR": g.r.mean(), "grossR": g.gross_r.mean(),
         "win": (g.r > 0).mean(), "costR": g.cost_r.mean(), "cost_bps": g.cost_bps.median(), "cost_usd": g.cost_usd.mean(),
         "tgt_dist_R_med": g.tgt_r.median(),
         "pct_target": (g.ex == "target").mean(), "pct_stop": (g.ex == "stop").mean(), "pct_flat": (g.ex == "flatten/time").mean(),
         "hold_med": g.hold.median(), "min_to_target_med": g.loc[g.ex == "target", "hold"].median(),
         "min_to_stop_med": g.loc[g.ex == "stop", "hold"].median(), "mfe_med": g.mfe_r.median(), "mae_med": g.mae_r.median(),
         "mfe_mean": g.mfe_r.mean(), "R_per_10min_winners": (g.loc[g.r > 0, "gross_r"] / g.loc[g.r > 0, "hold"].clip(lower=1) * 10).median()}
    return pd.Series(o)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print("\n== ALL accounts dedup ==\n", d.groupby("side_s").apply(card).T.round(3))
print("\n== excl graveyard ==\n", d[d.account != "graveyard"].groupby("side_s").apply(card).T.round(3))
print("\n== Primary only ==\n", t[t.account == "primary"].groupby("side_s").apply(card).T.round(3))
print("\n== Primary+Testing1+Testing2 ==\n", d[d.account.isin(["primary", "testing", "testing2"])].groupby("side_s").apply(card).T.round(3))
# setup-weighted: per-setup avg then median across setups (>= 20 trades)
ps = d.groupby(["side_s", "strategy"]).agg(n=("r", "size"), avgR=("r", "mean"), win=("r", lambda x: (x > 0).mean()),
                                           hold=("hold", "median"), tmin=("hold", "median"))
ps = ps[ps.n >= 20]
print("\n== per-setup (>=20 trades) ==\n", ps.groupby("side_s").agg(setups=("n", "size"), med_avgR=("avgR", "median"),
      share_pos=("avgR", lambda x: (x > 0).mean()), med_win=("win", "median"), med_hold=("hold", "median")).round(3))
# same target geometry: target ~1R
for lo, hi in ((0.4, 0.6), (0.9, 1.1)):
    s = d[(d.tgt_r > lo) & (d.tgt_r < hi)]
    print(f"\n== target {lo}-{hi}R only ==\n", s.groupby("side_s").apply(card).T.round(3).loc[["n", "avgR", "win", "pct_target", "pct_stop", "pct_flat", "hold_med", "min_to_target_med", "min_to_stop_med", "mfe_med"]])
# by entry-time bucket
d["et"] = d.entry_time.dt.tz_convert("America/New_York").dt.hour
print("\n== hold med by entry hour ==\n", d.pivot_table(index="et", columns="side_s", values="hold", aggfunc="median").round(1))
print(d.pivot_table(index="et", columns="side_s", values="r", aggfunc=["mean", "size"]).round(3))
d.to_parquet(X + "live_dedup.parquet")
