"""Winner/loser autopsy per setup for 2026-10-15 (trades.csv): MFE/MAE, never-worked, give-back, time to MFE, entry clusters
(trades per setup in the same 5-min poll), entry latency (signal bar close -> fill) and slippage. SIP 1-min bars. Educational only."""
import sys, pandas as pd, numpy as np
S = sys.argv[1]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
T = pd.read_csv("trades.csv")
for c in ("nt", "et"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
T["st"] = pd.to_datetime(T.signal_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
T["lat"] = (T.nt - T.st).dt.total_seconds()
bars = {}
def bar(s):
    if s not in bars:
        b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York"); bars[s] = b
    return bars[s]
tmfe = []
for r in T.itertuples():
    b = bar(r.symbol); w = b[(b.index >= r.nt.floor("1min")) & (b.index <= r.et.floor("1min"))]
    if w.empty: tmfe.append(np.nan); continue
    i = w.high.idxmax() if r.side == 1 else w.low.idxmin()
    tmfe.append((i - r.nt.floor("1min")).total_seconds() / 60)
T["t_mfe"] = tmfe
T["poll"] = T.st.dt.floor("5min")
T["cluster"] = T.groupby(["acct", "strategy", "poll"]).id.transform("size")
T["never"] = (T.pnl <= 0) & (T.mfe < 0.2)
T["hold"] = (T.et - T.nt).dt.total_seconds() / 60
def agg(d):
    w, l = d[d.pnl > 0], d[d.pnl <= 0]
    return pd.Series(dict(n=len(d), win=round(100 * (d.pnl > 0).mean()), pnl=round(d.pnl.sum(), 2), avgR=round(d.r_multiple.mean(), 3),
        mfe_w=round(w.mfe.median(), 2), mae_w=round(w.mae.median(), 2), mfe_l=round(l.mfe.median(), 2), mae_l=round(l.mae.median(), 2),
        never=int(d.never.sum()), never_pnl=round(d[d.never].pnl.sum(), 2), lost_after_half=int(((d.pnl <= 0) & (d.mfe >= 0.5)).sum()),
        giveback_w=round((w.mfe - w.r_multiple).median(), 2), tmfe_w=round(w.t_mfe.median(), 1), hold_l=round(l.hold.median(), 1),
        maxclust=int(d.cluster.max()), in_clust5=int((d.cluster >= 5).sum()), lat_med=round(d.lat.median()), lat_p90=round(d.lat.quantile(.9)),
        slip=round(d.slip_bps.mean(), 1), stop_gt11=int((d.r_multiple < -1.1).sum())))
for a in ("p", "t1", "t2"):
    d = T[T.acct == a]
    print("=====", a); print(agg(d).to_string().replace("\n", "; "))
    g = pd.DataFrame({k: agg(x) for k, x in d.groupby("strategy")}).T.sort_values("pnl")
    print(g[g.n >= 2].to_string())
    print("cluster size (same setup, same poll):"); print(pd.DataFrame({k: agg(x) for k, x in d.groupby(pd.cut(d.cluster, [0, 1, 4, 9, 100]))}).T[["n", "win", "pnl", "avgR", "never"]].to_string())
    print("polls (all setups):"); print(pd.DataFrame({k.strftime("%H:%M"): agg(x) for k, x in d.groupby("poll")}).T[["n", "win", "pnl", "avgR", "never"]].to_string())
T.to_csv("autopsy_trades.csv", index=False)
