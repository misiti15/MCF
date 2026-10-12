import sys; import pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 30)
S = sys.argv[1]
T = pd.read_csv(f"{S}/trades_all.csv")
def agg(g):
    return pd.Series({"n": len(g), "win%": round(100*(g.pnl > 0).mean()), "avgR": round(g.r_multiple.mean(), 3), "pnl": round(g.pnl.sum(), 2),
        "adj": round(g.pnl_adj.sum(), 2), "stop": (g.exit_reason == "stop").sum(), "tgt": (g.exit_reason == "target").sum(),
        "flat": (g.exit_reason == "flatten").sum(), "mfe": round(g.mfe.mean(), 2), "mae": round(g.mae.mean(), 2),
        "gb": round(g.giveback.mean(), 2), "tmfe": round(g.t_mfe.median(), 1), "hold": round(g.hold_min.median(), 1),
        "first": g.entry_hhmm.min(), "last": g.entry_hhmm.max()})
for a in ("p", "t1", "t2"):
    d = T[T.acct == a]
    print("=====", a); print(d.groupby("strategy").apply(agg).sort_values("pnl").to_string())
    print(agg(d).to_dict())
    print("-- by exit"); print(d.groupby(d.exit_reason.rename("ex")).apply(agg)[["n", "avgR", "pnl", "mfe", "mae", "hold"]].to_string())
    print("-- by side"); print(d.groupby(d.side.rename("sd")).apply(agg)[["n", "win%", "avgR", "pnl", "stop", "tgt", "flat"]].to_string())
    print("-- by 30m bucket"); print(d.groupby("bucket").apply(agg)[["n", "win%", "avgR", "pnl", "stop", "tgt"]].to_string())
    print("-- winners vs losers"); d2 = d.assign(w=np.where(d.pnl > 0, "win", np.where(d.pnl < 0, "loss", "zero")))
    print(d2.groupby("w").agg(n=("pnl", "size"), lat=("lat_s", "median"), spread=("spread_bps", "median"), slip=("slip_bps", "median"),
          mfe=("mfe", "mean"), mae=("mae", "mean"), tmfe=("t_mfe", "median"), hold=("hold_min", "median"), riskpct=("risk", lambda x: (x / d.loc[x.index, "entry"] * 100).median())).round(2).to_string())
    print("losers that reached >=0.5R MFE:", ((d.pnl < 0) & (d.mfe >= 0.5)).sum(), "of", (d.pnl < 0).sum(), " stops with MFE<0.1R:", ((d.exit_reason == "stop") & (d.mfe < 0.1)).sum(), "of", (d.exit_reason == "stop").sum())
    print("stop R dist (stops):", d[d.exit_reason == "stop"].r_multiple.describe().round(2).to_dict())
