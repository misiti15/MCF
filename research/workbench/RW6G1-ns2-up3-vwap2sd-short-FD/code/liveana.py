import sys, pandas as pd, numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-rw5/code")
from sim2 import spy_table
S = spy_table("spy1m.parquet")
t = pd.read_parquet("live_trades.parquet")
et = pd.to_datetime(t.entry_time, utc=True).dt.tz_convert("America/New_York")
st = pd.to_datetime(t.signal_time, utc=True).dt.tz_convert("America/New_York").dt.floor("5min")
t["tod"] = st.dt.hour * 100 + st.dt.minute
t["hold"] = (pd.to_datetime(t.exit_time, utc=True) - pd.to_datetime(t.entry_time, utc=True)).dt.total_seconds() / 60
t = t.merge(S, on=["date", "tod"], how="left")
F = pd.read_parquet("parent_replay.parquet")[["symbol", "date", "tod", "fromOpen", "rsi", "vwapDistPct", "z5", "atr_d", "close"]]
t = t.merge(F, on=["symbol", "date", "tod"], how="left")
t["onepct"] = 0.25 * t.atr_d / t.close * 100
pd.set_option("display.width", 200)
def b(col, bins):
    g = t.groupby(pd.cut(t[col], bins), observed=True).agg(n=("r", "size"), avg=("r", "mean"), tot=("r", "sum"), mfe=("mfe_r", "mean"))
    print("--", col); print(g.round(3).to_string())
b("tod", [900, 1200, 1300, 1400, 1430, 1500])
b("spy950", [-5, -0.3, 0, 0.3, 5]); b("fromOpen", [0, 4, 5, 7, 100]); b("rsi", [0, 65, 70, 100]); b("z5", [-5, 0, 0.5, 1.5, 5])
b("onepct", [0, 0.4, 0.6, 1, 10]); b("hold", [0, 30, 60, 120, 400])
print(t.groupby("exit_reason").agg(n=("r", "size"), avg=("r", "mean"), mfe=("mfe_r", "mean"), hold=("hold", "median")).round(3))
print("flatten with mfe >= 0.5:", ((t.exit_reason == "flatten") & (t.mfe_r >= 0.5)).sum(), "of", (t.exit_reason == "flatten").sum())
print("stops that had mfe >= 0.5:", ((t.exit_reason == "stop") & (t.mfe_r >= 0.5)).sum(), "of", (t.exit_reason == "stop").sum())
print("matched features:", t.fromOpen.notna().sum(), "/", len(t))
t.to_parquet("live_ctx.parquet")
