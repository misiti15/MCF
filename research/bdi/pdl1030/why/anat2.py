"""pdl1030/why extra descriptive slices (not scored configs). Educational only - not financial advice."""
import glob, numpy as np, pandas as pd
W = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030/why"
T = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(W + "/tr_*.parquet"))], ignore_index=True)
NS = T.date.nunique(); o = []
for S in ("p05", "p10"):
    g = T[T.setup == S].copy(); g["dspy"] = g.spy_x - g.spy_fo
    b = np.polyfit(g.dspy.fillna(0), g.r, 1)
    o.append(f"{S}: r = {b[1]:+.4f} + {b[0]:+.3f} * SPY%move-during-trade (intercept = market-neutral net R); gross intercept {b[1] + g.cost_rt_R.mean():+.4f}")
    g["cb"] = np.where(g.cost_rt_R <= 0.05, "cost<=5%R", "cost>5%R"); g["sv"] = np.where(g.spy_vd > 0, "SPYabvVWAP", "SPYblwVWAP")
    x = g.groupby(["cb", "sv"]).r.agg(["size", "mean"]); x["per_sess"] = x["size"] / NS
    o.append(x.round(3).to_string())
    g["gross"] = g.r + g.cost_rt_R
    o.append("gross R by cost bucket: " + g.groupby(pd.cut(g.cost_rt_R, [0, .03, .05, .08, .12, 9]), observed=True).gross.mean().round(3).to_dict().__repr__())
    o.append("price / atr% medians by cost bucket: " + g.groupby(pd.cut(g.cost_rt_R, [0, .05, .12, 9]), observed=True)[["price", "atrpct"]].median().round(2).to_dict().__repr__())
    d = g.groupby("date").agg(R=("r", "sum"), up=("spy_day", lambda v: v.iloc[0] > 0))
    o.append(f"share of total loss from SPY-down sessions: {d[~d.up].R.sum():+.0f}R of {d.R.sum():+.0f}R; up sessions {d[d.up].R.sum():+.0f}R")
    o.append(f"SPY gap<=-0.5 & cost<=5%R: n {((g.spy_gap<=-0.5)&(g.cost_rt_R<=.05)).sum()}, avgR {g[(g.spy_gap<=-0.5)&(g.cost_rt_R<=.05)].r.mean():+.3f}")
print("\n".join(o)); open(W + "/anat2_out.txt", "w").write("\n".join(o) + "\n\nEducational only - not financial advice.\n")
