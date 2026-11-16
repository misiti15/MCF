"""Mechanic GEN-261027-01: the signal bar of each live trade (latest 5-min bar close at or before the signal time that
meets macd_hist / ret3_atr) with its sensor values. Educational only - not financial advice."""
import pandas as pd, numpy as np
from common import OUT
L = pd.read_csv(OUT + "live.csv")
L["sig"] = pd.to_datetime(L.signal_time).dt.tz_convert("America/New_York")
L["sigtod"] = L.sig.dt.hour * 100 + (L.sig.dt.minute // 5) * 5
A = pd.concat([pd.read_parquet(OUT + "cand_rep.parquet"), pd.read_parquet(OUT + "live_off_frames.parquet")], ignore_index=True)
out = []
for r in L.itertuples():
    g = A[(A.symbol == r.symbol) & (A.date == r.date) & (A.tod <= r.sigtod)].sort_values("tod")
    g = g[(g.macd_hist >= 0.12) & (g.ret3_atr <= -0.069)]
    if not len(g): out.append({}); continue
    out.append(g.iloc[-1].to_dict())
F = pd.DataFrame(out).add_prefix("f_")
L = pd.concat([L.reset_index(drop=True), F], axis=1)
L.to_parquet(OUT + "live_feat.parquet")
cols = ["symbol", "date", "acct", "sigtod", "R", "exit_reason", "mfe_r", "mae_r", "f_tod", "f_macd_hist", "f_ret3_atr", "f_breadth",
        "f_ret12", "f_vwap_atr", "f_day_pos", "f_rsi5", "f_fromOpen_atr", "f_from_pc_atr", "f_adx7", "f_atr_d_pct", "f_dist_lod_atr", "f_close"]
pd.set_option("display.width", 300)
print(L.sort_values("R")[cols].round(3).to_string())
