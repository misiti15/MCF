"""Mechanic GEN-261027-01: all-trades component analysis of the parent with the 1-minute engine (2y). Educational only - not financial advice."""
import pandas as pd, numpy as np
from sim import *
T = pd.read_pickle(OUT + "final_trades.pkl"); C2 = pd.read_parquet(OUT + "cand2y.parquet")
t = T[("parent", "2y")].copy()
for c in ["macd_hist", "ret3_atr", "breadth", "br_chg", "spy950", "adv20", "atr_d_pct", "sma20_slope_pct", "vwap_atr", "day_pos", "dist_hod_atr", "close", "adx7", "rsi5"]:
    t[c] = C2.loc[t.idx, c].to_numpy()
t["sp"] = np.where(t.date <= "2025-12-31", "T", "V")
def tab(col, bins):
    x = pd.cut(t[col], bins)
    g = t.groupby(x, observed=True).agg(n=("r", "size"), avg=("r", "mean"), stop=("why", lambda w: (w == "stop").mean()),
        T=("r", lambda r: r[t.loc[r.index, "sp"] == "T"].mean()), V=("r", lambda r: r[t.loc[r.index, "sp"] == "V"].mean()))
    print(f"== {col}"); print(g.round(3).to_string())
tab("tod", [1355, 1410, 1420, 1430, 1440, 1450, 1500])
tab("macd_hist", [0.11, 0.14, 0.18, 0.25, 9]); tab("ret3_atr", [-9, -0.15, -0.1, -0.08, -0.068])
tab("breadth", [0.5, 0.6, 0.7, 0.8, 1]); tab("br_chg", [-1, 0, 0.1, 0.2, 0.3, 1]); tab("spy950", [-9, -0.3, 0, 0.5, 1.2, 9])
tab("adv20", [0, 50e6, 100e6, 300e6, 1e12]); tab("atr_d_pct", [0, 3.5, 5, 8, 100]); tab("close", [0, 10, 30, 100, 1e5])
tab("sma20_slope_pct", [-9, 0, 0.25, 0.5, 9]); tab("vwap_atr", [-9, -0.17, 0, 0.3, 9]); tab("day_pos", [0, 0.27, 0.5, 0.75, 1]); tab("dist_hod_atr", [0, 0.4, 1.08, 99])
print(t.groupby("why").agg(n=("r", "size"), avg=("r", "mean"), mfe=("mfe", "median"), mae=("mae", "median"), hold=("hold", "median")).round(3))
st_ = t[t.why == "stop"]; print("stops that first reached +0.3R:", round((st_.mfe >= 0.3).mean(), 3), "| time exits with MFE >= 0.4R:", round((t[t.why == 'time'].mfe >= 0.4).mean(), 3))
print("trades/day dist", t.groupby("date").size().describe().round(1).to_dict())
