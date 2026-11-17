"""Mechanic NM-RWN5: all-trades component analysis of the parent (2y). Educational only - not financial advice."""
import sys, pandas as pd, numpy as np
from sim import *
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib
D = load(False)
t = trades(*D["y2"], {}); t["sp"] = np.where(t.date <= "2025-12-31", "T", "V")
reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.strftime("%Y-%m-%d")
t = t.merge(reg[["date", "regime"]], on="date", how="left")
t.to_parquet(OUT + "parent2y.parquet")
print("2y", stats(t)); print("T/V", t.groupby("sp").r.agg(["count", "mean"]).round(3).to_dict())
def tab(col, bins=None, q=None):
    x = t[col] if bins is None and q is None else (pd.cut(t[col], bins) if bins is not None else pd.qcut(t[col], q, duplicates="drop"))
    g = t.groupby([x], observed=True).agg(n=("r", "size"), avg=("r", "mean"), win=("r", lambda r: (r > 0).mean()),
        stop=("why", lambda w: (w == "stop").mean()), T=("r", lambda r: r[t.loc[r.index, "sp"] == "T"].mean()),
        V=("r", lambda r: r[t.loc[r.index, "sp"] == "V"].mean()))
    print(f"\n== {col}"); print(g.round(3).to_string())
tab("tod", [945, 1000, 1015, 1030, 1100, 1130]); tab("regime")
t["rs"] = t.fromOpen - t.spy_fo; t["from_pc"] = ((1 + t.gap / 100) * (1 + t.fromOpen / 100) - 1) * 100
t["costR"] = (2 * (0.01 + t.close * 1e-4) + 0.02) / (0.25 * t.atr_d)
for c in ["fromOpen", "rs", "spy_fo", "spy950", "fo950", "sma50_dist_pct", "sma20_dist_pct", "sma20_slope_pct", "vwapDistPct",
          "rsi", "rsi5", "heat", "flow3", "volumeRatio", "atrPct", "dist_lod_atr", "dist_hod_atr", "dist_pdl_atr", "gap", "from_pc",
          "buyPressure", "macdPct", "upper_wick", "breadth", "breadth_open", "close", "adv20", "costR", "risk"]:
    if c in t: tab(c, q=4)
t["mo"] = t.date.str[:7]; print(t.groupby("mo").r.agg(["count", "mean", "sum"]).round(2).to_string())
d = t.groupby("date").r.agg(["count", "sum"]).sort_values("sum"); print(d.head(6)); print(d.tail(6))
print(t.groupby("why").agg(n=("r", "size"), avg=("r", "mean"), mfe=("mfe", "median"), mae=("mae", "median")).round(3))
st = t[t.why == "stop"]; print("stops: mfe>=0.5 first", (st.mfe >= 0.5).mean().round(2), "n", len(st))
tm = t[t.why == "time"]; print("flat exits: avg r", tm.r.mean().round(3), "mfe med", tm.mfe.median())
print("trades per day", t.groupby("date").size().describe().round(2).to_dict())
t["hold"] = [mdiff(a, b) for a, b in zip(t.xt, t.ent)]; print("hold median", t.hold.median())
# Monday part: same rules on the other weekdays
for dw in range(5):
    x = trades(*D["y2"], {"dows": (dw,)}); print("dow", dw, stats(x), "T", round(x[x.date <= "2025-12-31"].r.mean(), 3), "V", round(x[x.date > "2025-12-31"].r.mean(), 3))
