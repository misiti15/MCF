"""Owner's PENG/BKV read as a FILTER on orb20_a: skip an ORB trade in the direction of an already-extended
opening swing (run from the open to the 09:50 high/low >= k x daily ATR). 8 configurations, pre-declared:
k in {0.5, 0.75, 1.0, 1.5} x {longs only, both sides}. Uses the engine trades collected by the autopsy
(research/oct7/autopsy/base_with_features.parquet, train/valid only, costs in). Educational only."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "research/oct7/innovation")
import bdlib as B

d = pd.read_parquet("research/oct7/autopsy/base_with_features.parquet")
o = d[d.setup == "orb20_a"].copy()
o["side"] = np.sign((o.exit - o.entry) * o.pnl)
o["date"] = pd.to_datetime(o["date"]).dt.date
feat = []
for sp in ("train", "valid"):
    f = B.load(sp)
    f = f[f.tod == 950][["symbol", "date", "up_run_950", "dn_run_950"]].copy()
    f["symbol"] = f["symbol"].astype(str)
    feat.append(f)
feat = pd.concat(feat)
o = o.merge(feat, on=["symbol", "date"], how="left")
o["run_with"] = np.where(o.side > 0, o.up_run_950, o.dn_run_950)
print("missing features:", int(o.run_with.isna().sum()), "of", len(o))
rows = []
for k in (0.5, 0.75, 1.0, 1.5):
    for scope in ("long", "both"):
        drop = (o.run_with >= k) & ((o.side > 0) if scope == "long" else True)
        for sp in ("train", "valid"):
            x = o[o.split == sp]
            dx = drop[o.split == sp]
            diff = -x.pnl.where(dx, 0.0)            # P/L change from skipping
            daily = diff.groupby(x.date).sum()
            t = daily.mean() / (daily.std(ddof=1) / np.sqrt(len(daily))) if daily.std(ddof=1) > 0 else np.nan
            rows.append({"k": k, "scope": scope, "split": sp, "n": len(x), "dropped": int(dx.sum()),
                         "dropped_pnl": round(float(x.pnl[dx].sum()), 1), "dropped_r": round(float(x.r_live[dx].mean()), 3) if dx.any() else np.nan,
                         "kept_pnl": round(float(x.pnl[~dx].sum()), 1), "base_pnl": round(float(x.pnl.sum()), 1),
                         "delta": round(float(diff.sum()), 1), "t_delta": round(float(t), 2)})
r = pd.DataFrame(rows)
r.to_csv("research/oct7/innovation/orb_swing_filter.csv", index=False)
print(r.to_string())
