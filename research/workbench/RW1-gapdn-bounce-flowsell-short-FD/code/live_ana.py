"""RW1-FD live component analysis (diagnosis only): live trades joined to the replay lab frame at their signal bar
(SPY since 09:50, cost/R, 1R % of price, RSI(5), VWAP distance, heat, bp, gap ...), plus the parent's replay parity.
Educational only - not financial advice."""
import numpy as np, pandas as pd
import sim_rw1 as sim
SPY = sim.spy_table("spy1m.parquet")
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF.tod.astype(int); RF["date"] = RF.date.astype(str)
RF = RF.merge(SPY, on=["date", "tod"], how="left")
t = pd.read_parquet("live_trades.parquet")
risk = (t.entry - t.stop).abs() * t.shares
t["R"] = np.where(risk > 0, t.pnl_adj.fillna(t.pnl) / risk, t.r_multiple)
st = pd.to_datetime(t.signal_time, utc=True).dt.tz_convert("America/New_York")
et = pd.to_datetime(t.entry_time, utc=True).dt.tz_convert("America/New_York")
xt = pd.to_datetime(t.exit_time, utc=True).dt.tz_convert("America/New_York")
# signal bar close HHMM = the 5-min bar that closed at/just before the entry
t["tod"] = [(x.hour * 60 + x.minute) // 5 * 5 for x in et]
t["tod"] = [(m // 60) * 100 + m % 60 for m in t.tod]
t["hold"] = (xt - et).dt.total_seconds() / 60
t["rpct"] = (t.entry - t.stop).abs() / t.entry * 100
t["costr"] = (2 * (0.01 + 1e-4 * t.entry) + 0.02) / (t.entry - t.stop).abs()
f = RF[["symbol", "date", "tod", "spy950", "rsi5", "rsi", "vwapDistPct", "heat", "buyPressure", "gap", "fromOpen", "atr_d", "close",
        "sma20_slope_pct", "dist_lod_atr"]]
t = t.merge(f, on=["symbol", "date", "tod"], how="left")
print("joined", t.spy950.notna().sum(), "/", len(t))
t.drop(columns=[c for c in t if t[c].dtype == object and c not in ("symbol", "date", "acct", "exit_reason")]).to_parquet("live_feat.parquet")
def grp(col, bins):
    g = t.groupby(pd.cut(t[col], bins), observed=True).R.agg(["size", "mean", "sum"])
    print(f"--- {col}\n{g.round(3).to_string()}")
grp("spy950", [-9, -0.5, -0.2, 0, 0.2, 0.3, 9])
grp("costr", [0, 0.05, 0.10, 0.15, 1])
grp("rpct", [0, 0.4, 0.6, 1.0, 9])
grp("rsi5", [0, 50, 70, 80, 90, 101])
grp("rsi", [54, 58, 60, 62, 66])
grp("vwapDistPct", [-20, -1, -0.5, 0, 0.5, 20])
grp("heat", [-200, -40, -30, -25, -20])
grp("buyPressure", [-2, -0.6, -0.5, -0.4, -0.35])
grp("gap", [-50, -3, -1.5, -0.5, 0])
grp("tod", [0, 1030, 1100, 1200, 1300, 1400, 1600])
grp("hold", [0, 30, 60, 120, 180, 400])
grp("mfe_r", [-1, 0.25, 0.5, 0.75, 1.01, 9])
lo = t[t.exit_reason == "stop"]
print("stops with MFE >= 0.5R:", (lo.mfe_r >= 0.5).sum(), "/", len(lo))
fl = t[t.exit_reason == "flatten"]; print("flatten trades", len(fl), "avg", round(fl.R.mean(), 3), "MFE>=0.5", (fl.mfe_r >= 0.5).sum())
# parent replay parity
v = sim.BASE
r1 = pd.read_parquet("replay_1min.parquet")
mk = lambda df: (np.asarray(df.index.hour * 60 + df.index.minute), df.open.values, df.high.values, df.low.values, df.close.values)
RP = {k: mk(g) for k, g in r1.groupby(["symbol", "date"])}
rp = sim.book(sim.trades(RF[RF.date <= "2026-11-13"], v, lambda s, d: RP.get((s, d))), v)
print("replay parent", len(rp), round(rp.r.mean(), 3), round(rp.r.sum(), 1), "| live (<=11-13)", (t.date <= "2026-11-13").sum(),
      round(t[t.date <= "2026-11-13"].R.mean(), 3))
k = set(zip(rp.symbol, rp.date)); lk = set(zip(t.symbol, t.date))
print("symbol-days live&replay", len(k & lk), "replay only", len(k - lk), "live only", len(lk - k))
