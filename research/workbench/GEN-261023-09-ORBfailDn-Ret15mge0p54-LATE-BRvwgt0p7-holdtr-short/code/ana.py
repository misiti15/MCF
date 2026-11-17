"""Mechanic GEN-261023-09: all-trades component analysis of the parent on the 2-year backtest (and Gen-style, no cost
filter). Educational only - not financial advice."""
import sys, pickle, pandas as pd, numpy as np
from sim import *
import lib
C = pd.read_parquet(OUT + "cand2y.parquet"); P = pickle.load(open(OUT + "paths2y.pkl", "rb"))
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d")
for nm, v in (("parent (cf 0.15, as Testing E)", {}), ("parent, no cost filter (as Gen)", {"cf": None})):
    t = trades(C, P, v); print(nm, stats(t), "T", round(t[t.date <= "2025-12-31"].r.mean(), 3), "V", round(t[t.date > "2025-12-31"].r.mean(), 3))
t = trades(C, P, {})
t = t.join(C[[c for c in C.columns if c not in t.columns]], on="idx")
t["sp"] = np.where(t.date <= "2025-12-31", "T", "V")
t = t.merge(reg[["date", "regime"]], on="date", how="left")
t.to_parquet(OUT + "parent2y.parquet")
def tab(col, bins=None, q=None):
    x = t[col] if bins is None and q is None else (pd.cut(t[col], bins) if bins is not None else pd.qcut(t[col], q, duplicates="drop"))
    g = t.groupby([x], observed=True).agg(n=("r", "size"), avg=("r", "mean"), win=("r", lambda r: (r > 0).mean()),
        stop=("why", lambda w: (w == "stop").mean()), T=("r", lambda r: r[t.loc[r.index, "sp"] == "T"].mean()),
        V=("r", lambda r: r[t.loc[r.index, "sp"] == "V"].mean()))
    print(f"\n== {col}"); print(g.round(3).to_string())
tab("tod", [1355, 1415, 1430, 1445, 1500]); tab("regime")
cols = ["breadth", "breadth_open", "br950", "br_chg", "spy950", "ret3", "ret1", "ret6", "ret12", "rsi5", "rsi7", "vwap_atr", "day_pos",
        "fromOpen_atr", "from_pc_atr", "atr_d_pct", "adx7", "di_diff7", "rvol_day", "z12", "dist_hod_atr", "dist_lod_atr", "gap_atr",
        "ret_since950_atr", "flow3", "bars_since_hod", "bars_since_lod", "volumeRatio", "day_range_atr", "eff6", "upper_wick",
        "bar_range_atr", "macd_hist", "sma20_dist_pct", "emaDiff", "or_low_dist_atr", "or_high_dist_atr", "dist_pdh_atr", "ret3_atr",
        "vwap_cross_n", "bb_pctb12", "close", "adv20"]
for c in cols:
    if c in t: tab(c, q=5)
t["costR"] = (2 * (0.01 + t.close * 1e-4) + 0.02) / (0.25 * t.atr_d); tab("costR", q=4)
t["mo"] = t.date.str[:7]; print(t.groupby("mo").r.agg(["count", "mean", "sum"]).round(2).to_string())
d = t.groupby("date").r.agg(["count", "sum"]).sort_values("sum"); print(d.head(8)); print(d.tail(8))
print(t.groupby("why").agg(n=("r", "size"), avg=("r", "mean"), mfe=("mfe", "median"), mae=("mae", "median"), hold=("hold", "median")).round(3))
st_ = t[t.why == "stop"]; print("stops: mfe>=0.5 first", round((st_.mfe >= 0.5).mean(), 2), "mfe>=0.8", round((st_.mfe >= 0.8).mean(), 2), "n", len(st_))
tm = t[t.why == "time"]; print("flat exits: avg r", round(tm.r.mean(), 3), "mfe med", tm.mfe.median(), "share mfe>=1", round((tm.mfe >= 1).mean(), 2))
print("trades per day", t.groupby("date").size().describe().round(2).to_dict())
dd = t.groupby("date").agg(n=("r", "size"), s=("r", "sum"))
dd["nb"] = pd.cut(dd.n, [0, 2, 5, 10, 20, 1000]); print(dd.groupby("nb", observed=True).agg(days=("s", "size"), R=("s", "sum"), perday=("s", "mean")).round(2))
print("by trade's rank within its day (entry order):")
t = t.sort_values(["date", "ent", "symbol"]); t["k"] = t.groupby("date").cumcount() + 1
tab("k", [0, 3, 5, 10, 20, 1000])
