"""FIT-only diagnosis of BEG-06 base losers (entry timing, stop, trailing exit, window, filter). Educational only."""
import numpy as np
import pandas as pd
import run as R

S = R.sessions("t1")
bk = pd.read_parquet(R.WORK / "bk_base_fit.parquet")
assert set(R.B.half(bk.date.unique())) == {"fit"}
print("booked", len(bk), "avgR", round(bk.r.mean(), 3), "gross", round(bk.r_gross.mean(), 3),
      "cost R/trade", round((bk.r_gross - bk.r).mean(), 3), "risk/entry bp", round((bk.risk / bk.entry).median() * 1e4, 1))
for col in ("kind", "side", "check", "symbol"):
    print(bk.groupby(col).r.agg(["count", "mean", "sum"]).round(3).T.to_string(), "\n")
bk["nth"] = bk.groupby(["symbol", "date"]).cumcount() + 1
print("nth entry of the day:\n", bk.groupby("nth").r.agg(["count", "mean", "sum"]).round(3).T.to_string())
bk["band_vs_atr"] = bk.band_w_pct / 100 * bk.entry / bk.atr
bk["vwq"] = pd.qcut(bk.side * bk.vw_dist_pct, 4)
print("side-signed distance from VWAP at entry:\n", bk.groupby("vwq", observed=True).r.agg(["count", "mean"]).round(3).T.to_string())
bk["mq"] = pd.qcut(bk.m_pct, 4)
print("m_t quartile:\n", bk.groupby("mq", observed=True).r.agg(["count", "mean"]).round(3).T.to_string())
rows = []
for t in bk.itertuples():
    o, h, l, c, v, hh, pc, atr, mv = S[(t.symbol, t.date)]
    j = int(np.flatnonzero(hh >= t.tod)[0])
    x5 = np.flatnonzero(hh >= 1555)
    x5 = int(x5[0]) if len(x5) else len(o) - 1
    hold = t.side * (o[x5] - o[j]) / t.risk                      # no stops at all, to 15:55
    seg_l, seg_h = l[j:x5], h[j:x5]
    mae = float((t.side * ((seg_l if t.side == 1 else seg_h) - o[j])).min()) / atr
    # hard stop only (no trailing), stop 0.25 and 0.3125 ATR
    def stop_only(mult):
        st = o[j] - t.side * mult * atr
        for k in range(j, x5):
            if (t.side == 1 and l[k] <= st) or (t.side == -1 and h[k] >= st):
                return t.side * ((min(o[k], st) if t.side == 1 else max(o[k], st)) - o[j]) / t.risk
        return hold
    rows.append((hold, mae, stop_only(0.25), stop_only(0.3125)))
D = pd.DataFrame(rows, columns=["hold_r", "mae_atr", "hardonly_r", "hard125_r"], index=bk.index)
bk = bk.join(D)
print("\ngross R: setup", round(bk.r_gross.mean(), 3), "| no stops, hold to 15:55", round(bk.hold_r.mean(), 3),
      "| hard stop only (no trail)", round(bk.hardonly_r.mean(), 3), "| hard stop x1.25 only", round(bk.hard125_r.mean(), 3))
print("MAE (ATR) quantiles:", bk.mae_atr.quantile([.25, .5, .75]).round(3).to_dict())
for k, g in bk.groupby("kind"):
    print(f"kind {k}: n {len(g)} setup R {g.r_gross.mean():.3f}  held-to-15:55 R {g.hold_r.mean():.3f}  "
          f"share ending right side if held {(g.hold_r > 0).mean():.2f}")
print("\nworst 15:\n", bk.nsmallest(15, "r")[["symbol", "date", "check", "side", "kind", "xt", "r", "hold_r", "m_pct",
                                               "vw_dist_pct"]].to_string())
spy = R.B.spy_t1()
bk["spy"] = bk.date.map(spy)
print("\nSPY day type x side:\n", bk.pivot_table(index="spy", columns="side", values="r", aggfunc=["count", "mean"]).round(3))
bk["month"] = bk.date.str[:7]
print(bk.groupby("month").r.agg(["count", "mean", "sum"]).round(2).T.to_string())
