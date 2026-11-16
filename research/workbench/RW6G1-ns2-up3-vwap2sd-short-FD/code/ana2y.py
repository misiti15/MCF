import sys, pandas as pd, numpy as np
sys.path.insert(0, "code")
T = pd.read_pickle(sys.argv[1] if len(sys.argv) > 1 else "trades_ROUND1.pkl")
import sim3
exec(open("code/load.py").read().split("P2 = pickle")[0].split("R1 = pd.read_parquet")[0])  # SPY only
C = pd.read_parquet("cand2y.parquet"); C["tod"] = C.tod.astype(int)
B = pd.read_parquet("band2y.parquet")
t = T[sys.argv[2] if len(sys.argv) > 2 else "PARENT"]["2y"].merge(C[["symbol", "date", "tod", "fromOpen", "rsi", "vwapDistPct", "atr_d", "close", "sma20_slope_pct", "dist_hod_atr", "gap", "rsi5", "heat", "adv20", "volumeRatio"]], on=["symbol", "date", "tod"], how="left")
t = t.merge(B[["symbol", "date", "tod", "z5"]], on=["symbol", "date", "tod"], how="left", suffixes=("", "_b"))
t["rpct"] = 0.25 * t.atr_d / t.close * 100
nday = t.groupby("date").r.transform("size"); t["nday"] = nday
pd.set_option("display.width", 200)
def b(col, bins):
    g = t.groupby(pd.cut(t[col], bins), observed=True).agg(n=("r", "size"), avg=("r", "mean"), tot=("r", "sum"), mfe=("mfe", "mean"))
    print("--", col); print(g.round(3).to_string())
b("tod", [900, 1100, 1200, 1300, 1400, 1430, 1500])
b("spy950", [-9, -0.5, -0.2, 0, 0.2, 0.5, 9]); b("fromOpen", [0, 4, 5, 7, 10, 100]); b("rsi", [0, 63, 66, 70, 75, 100])
b("z5", [-9, 0, 0.5, 1, 1.5, 2, 9]); b("rpct", [0, 0.3, 0.4, 0.6, 1, 10]); b("dist_hod_atr", [-1, 0.1, 0.25, 0.5, 1, 9])
b("gap", [-50, -2, 0, 2, 5, 100]); b("sma20_slope_pct", [-9, 0, 0.1, 0.2, 0.4, 9]); b("nday", [0, 3, 10, 30, 1000]); b("adv20", [0, 150e6, 300e6, 1e9, 1e13])
b("volumeRatio", [0, 0.8, 1.2, 2, 100]); b("rsi5", [0, 60, 70, 80, 90, 101])
print(t.groupby("kind").agg(n=("r", "size"), avg=("r", "mean"), mfe=("mfe", "mean")).round(3))
d = t.groupby("date").r.agg(["size", "sum"]).sort_values("sum"); print(d.head(8)); print(d.tail(5))
