"""Mechanic GEN-261023-09: sensor values of the 10 live trades at their signal bar (replay lab frames, live pipeline) and
which copy keeps each. Educational only - not financial advice."""
import pandas as pd
from common import OUT
L = pd.read_pickle(OUT + "live.pkl"); C = pd.read_parquet(OUT + "cand_replay.parquet")
m = L[["symbol", "date", "tod", "entry", "exit", "r", "exit_reason", "mfe_r", "mae_r"]].merge(C, on=["symbol", "date", "tod"], how="left", suffixes=("", "_c"))
m["costR"] = (2 * (0.01 + m.close * 1e-4) + 0.02) / (0.25 * m.atr_d)
m["CF"] = m.costR <= 0.15; m["W"] = m.tod >= 1430; m["RA"] = m.ret3_atr >= 0.20; m["MH"] = m.macd_hist >= 0.10
m["WB4"] = m.W & m.RA & m.MH & m.CF
cols = ["symbol", "tod", "r", "exit_reason", "mfe_r", "breadth", "ret3", "ret3_atr", "macd_hist", "atr_d_pct", "spy950", "br_chg", "adv20", "costR", "CF", "W", "RA", "MH", "WB4"]
print(m[cols].sort_values("r").round(3).to_string())
for c in ("CF", "W", "RA", "MH", "WB4"):
    print(c, "keeps", m[m[c]].r.agg(["count", "mean", "sum"]).round(3).to_dict(), "skips", m[~m[c]].r.agg(["count", "mean", "sum"]).round(3).to_dict())
m.to_parquet(OUT + "live_sensors.parquet")
