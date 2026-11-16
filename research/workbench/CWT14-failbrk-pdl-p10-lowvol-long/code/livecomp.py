"""All-live-trades component analysis. Educational only - not financial advice."""
import sys, json, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/"
L = pd.read_parquet(S + "live.parquet")
L["risk"] = (L.entry - L.stop).abs()
L["costR"] = (2 * (0.01 + L.entry * 1e-4) + 0.02) / L.risk
L["px"] = L.entry
st = pd.to_datetime(L.signal_time, utc=True).dt.tz_convert("America/New_York")
L["tod"] = st.dt.hour * 100 + st.dt.minute // 5 * 5
L["mins_held"] = (pd.to_datetime(L.exit_time, utc=True) - pd.to_datetime(L.entry_time, utc=True)).dt.total_seconds() / 60
L["atrpct"] = L.risk / 0.25 / L.entry  # approximate (1R = 0.25 ATR at signal; fill drift ignored)
def show(col, bins, lab=None):
    g = L.groupby(pd.cut(L[col], bins), observed=True).R.agg(["count", "mean", "sum"])
    print(f"--- {col}"); print(g.round(3).to_string())
print("exit mix", L.groupby("exit_reason").R.agg(["count", "mean"]).round(3).to_string())
show("costR", [0, .05, .08, .10, .15, 1])
show("px", [0, 10, 20, 50, 100, 1e5])
show("tod", [949, 1000, 1030, 1100, 1200, 1300, 1400, 1501])
show("atrpct", [0, .015, .02, .03, .05, 1])
show("mins_held", [0, 5, 15, 30, 60, 120, 400])
# stops that first reached >= +0.3R (live mfe_r where present)
s = L[L.exit_reason == "stop"]
print("stops n", len(s), "mfe_r notna", s.mfe_r.notna().sum(), "mfe>=0.3R", (s.mfe_r >= 0.3).sum())
d = L.groupby("date").R.agg(["count", "sum", "mean"]); print(d.round(2).to_string())
