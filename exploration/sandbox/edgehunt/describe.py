"""EDGEHUNT descriptive follow-ups (not scored, no configs counted): walker sanity, gross vs cost by stop width.
Usage: python describe.py HOLD_PARQUET. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.argv = [sys.argv[0], sys.argv[1]]
exec(open(__file__.replace("describe.py", "score.py")).read().split("def ct(")[0])
c["xh"] = (c.hxt // 100) * 60 + c.hxt % 100
print("walker sanity: share of lots whose hold exit is before the stored exit minute:", round(float((c.xh < c.xm).mean()), 4))
print("share hold exit == stored exit minute:", round(float((c.xh == c.xm).mean()), 3))
c["wb"] = pd.cut(c.rp, [0, 0.5, 1, 1.5, 2, 3, 100], labels=["<0.5", "0.5-1", "1-1.5", "1.5-2", "2-3", ">=3"])
c["hcost"] = c.hgross - c.hr
for side, nm in ((-1, "shorts"), (1, "longs")):
    g = c[(c.side == side) & c.per.isin(["CHECK", "T2"])]
    t = g.groupby(["per", "wb"], observed=True).agg(n=("hr", "size"), base_net=("r", "mean"), hold_gross=("hgross", "mean"),
                                                    hold_cost=("hcost", "mean"), hold_net=("hr", "mean"))
    print("\n", nm); print(t.round(3).to_string())
print("\nFIT (descriptive), shorts by width: hold net / base net")
g = c[(c.side == -1) & (c.per == "FIT")]
print(g.groupby("wb", observed=True).agg(n=("hr", "size"), base_net=("r", "mean"), hold_net=("hr", "mean")).round(3).to_string())
g = c[(c.side == -1) & (c.rp >= 2)]
print("\nshorts stop>=2% hold, by setup x split (n, net):")
print(g.groupby(["s", "per"]).hr.agg(["size", "mean"]).round(3).to_string())
