"""RW7 live trades (Testing 1 / On Deck, run 1, 10-12..11-13) joined to the replay lab frame at the signal bar -> component buckets."""
import pandas as pd, numpy as np, sys
sys.path.insert(0, "code"); import sim2
T = pd.read_parquet("live_trades.parquet")
T["r"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares)
st = pd.to_datetime(T.signal_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
m = st.dt.hour * 60 + st.dt.minute
T["tod"] = (m // 5 * 5); T["tod"] = (T.tod // 60) * 100 + T.tod % 60   # bar close = floor to 5-min
T["em"] = st.dt.hour * 60 + st.dt.minute
et = pd.to_datetime(T.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York"); T["hold"] = (et - st).dt.total_seconds() / 60
F = pd.read_parquet("replay_frames.parquet"); F["tod"] = F.tod.astype(int); F["date"] = F.date.astype(str)
S = sim2.spy_table("spy1m.parquet")
F = F.merge(S, on=["date", "tod"], how="left")
F["costr"] = sim2.costr(F, 0.25)
X = T.merge(F, on=["symbol", "date", "tod"], how="left", suffixes=("", "_f"))
print("joined", X.heat.notna().sum(), "of", len(X))
ok = X[X.heat.notna()]
mm = ((ok.heat <= -20) & (ok.buyPressure < -0.15) & ok.rsi.between(55, 65) & (ok.gap < 0))
print("frame mask parity at signal bar", mm.mean())
def bk(col, bins):
    g = X.groupby(pd.cut(X[col], bins), observed=True).r
    print(f"\n{col}"); print(g.agg(["size", "mean", "sum"]).round(3).to_string())
bk("spy950", [-9, -0.5, -0.2, 0, 0.2, 0.5, 9])
bk("tod", [0, 1015, 1100, 1200, 1300, 1400, 1500])
bk("costr", [0, 0.05, 0.08, 0.10, 0.15, 9])
bk("heat", [-200, -60, -40, -30, -20])
bk("buyPressure", [-9, -0.5, -0.3, -0.2, -0.15])
bk("rsi", [55, 57.5, 60, 62.5, 65.01])
bk("rsi5", [0, 50, 60, 70, 80, 90, 101])
bk("gap", [-99, -3, -1.5, -0.75, -0.3, 0])
bk("fromOpen", [-99, -2, -1, -0.5, 0, 0.5, 1, 99])
bk("vwapDistPct", [-99, -1, -0.5, -0.2, 0, 0.2, 0.5, 99])
bk("sma20_slope_pct", [-99, -0.2, -0.1, 0, 0.1, 0.2, 99])
bk("dist_lod_atr", [-1, 0.1, 0.2, 0.3, 0.5, 9])
bk("dist_hod_atr", [-1, 0.1, 0.2, 0.3, 0.5, 9])
bk("atrPct", [0, 2, 3, 4, 6, 99])
bk("close", [0, 10, 20, 50, 100, 9999])
bk("pricePosition", [-1, 0.2, 0.4, 0.6, 0.8, 2])
bk("volumeRatio", [0, 0.7, 1, 1.5, 2.5, 99])
bk("hold", [0, 15, 30, 60, 120, 240, 999])
print("\nexit mix"); print(X.groupby("exit_reason").r.agg(["size", "mean", "sum"]).round(3))
print("\nflatten trades mfe>=0.5:", ((X.exit_reason == "flatten") & (X.mfe_r >= 0.5)).sum(), "stops that had mfe>=0.5:", ((X.exit_reason == "stop") & (X.mfe_r >= 0.5)).sum())
print("stops with mfe < 0.2:", ((X.exit_reason == "stop") & (X.mfe_r < 0.2)).sum(), "of", (X.exit_reason == "stop").sum())
X.to_parquet("live_joined.parquet")
