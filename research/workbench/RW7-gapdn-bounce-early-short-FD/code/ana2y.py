import sys; sys.path.insert(0, "code")
from load import *
import sim2, decl
cfg = sys.argv[1] if len(sys.argv) > 1 else "PARENT"
allc = {**decl.ROUND1, **decl.ROUND2, **getattr(decl, "ROUND3", {})}
v = allc[cfg]
t = sim2.book(sim2.trades(C, v, getB), v)
t["split"] = t.date.map(split)
t["costr"] = (2 * (0.01 + 1e-4 * t.close) + 0.02) / (0.25 * t.atr_d)
t["rpct"] = 0.25 * t.atr_d / t.close * 100
S = pd.read_parquet("spy1m.parquet"); S.index = S.index.tz_convert("America/New_York"); S["d"] = S.index.strftime("%Y-%m-%d")
oc = S.groupby("d").apply(lambda g: (g.close.iloc[-1] / g.open.iloc[0] - 1) * 100)
t["spyday"] = t.date.map(oc)
t.to_parquet(f"t2y_{cfg[:3].strip()}.parquet")
def bk(col, bins):
    g = t.groupby(pd.cut(t[col], bins), observed=True).r
    print(f"\n{col}"); print(g.agg(["size", "mean", "sum"]).round(3).T.to_string())
print(cfg, sim2.stats(t))
d = t.groupby("date").r.agg(["sum", "size"]).sort_values("sum"); print(d.head(8).round(1).T.to_string()); print(d.tail(4).round(1).T.to_string())
bk("spyday", [-9, -1, -0.25, 0.25, 1, 9]); bk("spy950", [-9, -0.5, -0.2, 0, 0.1, 0.2, 0.5, 9])
bk("tod", [0, 1015, 1100, 1200, 1300, 1400, 1500]); bk("gap", [-99, -3, -1.5, -0.75, -0.5, -0.25, 0])
bk("fromOpen", [-99, -2, -1, -0.5, 0, 0.5, 1, 99]); bk("vwapDistPct", [-99, -1, -0.5, -0.2, 0, 0.2, 0.5, 99])
bk("rsi5", [0, 50, 60, 70, 80, 90, 101]); bk("rsi", [55, 57.5, 60, 62.5, 65.01]); bk("heat", [-200, -40, -30, -25, -20])
bk("buyPressure", [-9, -0.5, -0.3, -0.2, -0.15]); bk("sma20_slope_pct", [-99, -0.2, -0.1, -0.05, 0, 0.05, 0.1, 0.2, 99])
bk("rpct", [0, 0.3, 0.4, 0.5, 0.75, 1, 99]); bk("costr", [0, 0.05, 0.08, 0.1, 0.15]); bk("close", [0, 10, 20, 50, 100, 9999])
bk("pricePosition", [-1, 0.2, 0.4, 0.6, 0.8, 2]); bk("flow3", [-99, -0.5, -0.3, -0.15, 0, 99]); bk("upper_wick", [-1, 0.1, 0.25, 0.5, 9])
bk("dist_lod_atr", [-1, 0.1, 0.2, 0.3, 0.5, 1, 99]); bk("dist_hod_atr", [-1, 0.1, 0.2, 0.3, 0.5, 1, 99]); bk("volumeRatio", [0, 0.7, 1, 1.5, 2.5, 99])
print("\nkind"); print(t.groupby("kind").r.agg(["size", "mean"]).round(3).T.to_string())
