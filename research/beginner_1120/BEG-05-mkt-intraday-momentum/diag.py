"""FIT-only diagnosis of BEG-05 base losers (which part: signal direction, stop, window, filter, cost filter).
Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
import run as R
import beg05 as G

S = R.sessions("t1")
raw = pd.read_parquet(R.WORK / "raw_base_fit.parquet")
bk = pd.read_parquet(R.WORK / "bk_base_fit.parquet")
print("booked", len(bk), "avgR", bk.r.mean().round(3), "gross", bk.r_gross.mean().round(3),
      "cost R/trade", (bk.r_gross - bk.r).mean().round(3))
print("by exit kind:\n", bk.groupby("kind").r.agg(["count", "mean", "sum"]).round(3))
print("by symbol:\n", bk.groupby("symbol").r.agg(["count", "mean", "sum"]).round(3))
print("by side:\n", bk.groupby("side").r.agg(["count", "mean", "sum"]).round(3))
print("worst 15:\n", bk.nsmallest(15, "r")[["symbol", "date", "side", "r1", "r2", "kind", "xt", "r", "risk", "stop_atr"]])
# what would the losers have done without the stop (hold 15:30 open -> 15:55 open), and in ATR units
rows = []
for t in raw.itertuples():
    o, h, l, c, v, hh, pc, atr = S[(t.symbol, t.date)]
    j = np.flatnonzero(hh >= t.tod)[0]
    xs = np.flatnonzero(hh >= 1555)
    x = xs[0] if len(xs) else len(o) - 1
    nostop = t.side * (o[x] - o[j])
    mae = (t.side * ((l[j:x] if t.side == 1 else h[j:x]) - o[j])).min()
    rows.append((t.symbol, t.date, t.side, nostop / t.risk, nostop / atr, mae / atr, t.r1, t.r2,
                 t.side * (o[j] - c[np.flatnonzero(hh == 959)[0]]) / atr))
D = pd.DataFrame(rows, columns=["symbol", "date", "side", "nostop_r_gross", "nostop_atr", "mae_atr", "r1", "r2", "mid_atr"])
D = D.merge(raw[["symbol", "date", "r", "r_gross", "kind", "stop_cost_r"]], on=["symbol", "date"])
print("\nall raw signals (no cost filter): with stop gross", D.r_gross.mean().round(3), " no-stop gross",
      D.nostop_r_gross.mean().round(3), " no-stop in ATR", D.nostop_atr.mean().round(4))
st = D[D.kind == 1]
print("stopped trades:", len(st), "their no-stop gross R", st.nostop_r_gross.mean().round(3),
      "share that finished on the right side w/o stop", (st.nostop_r_gross > 0).mean().round(3))
print("MAE (ATR) quantiles of all signals:", D.mae_atr.quantile([.1, .25, .5]).round(3).to_dict())
D["r1b"] = pd.cut(D.r1.abs(), [0.25, 0.5, 0.75, 1.0, 9])
print("\nby |r1| bucket:\n", D.groupby("r1b", observed=True)[["r_gross", "nostop_r_gross", "nostop_atr"]].agg(["count", "mean"]).round(3))
D["agree"] = np.sign(D.r2) == D.side
print("\nmid-day move agrees with side:\n", D.groupby("agree")[["r_gross", "nostop_atr"]].agg(["count", "mean"]).round(3))
D["filt"] = D.stop_cost_r <= 0.15
print("\npassed cost filter:\n", D.groupby("filt")[["r", "r_gross"]].agg(["count", "mean"]).round(3))
D["month"] = D.date.str[:7]
print("\nby month:\n", D.groupby("month")[["r_gross", "nostop_atr"]].agg(["count", "mean"]).round(3))
