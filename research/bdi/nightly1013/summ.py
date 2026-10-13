"""Descriptive splits of 2026-10-13 trades (trades.csv). Educational only."""
import pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
T = pd.read_csv("trades.csv")
def agg(d):
    return pd.Series(dict(n=len(d), win=round(100 * (d.pnl > 0).mean()), avgR=round(d.r_multiple.mean(), 3), pnl=round(d.pnl.sum(), 2),
                          adj=round(d.pnl_adj.sum(), 2), stops=int((d.exit_reason == 'stop').sum()), tgt=int((d.exit_reason == 'target').sum()),
                          flat=int((d.exit_reason == 'flatten').sum()), mfe=round(d.mfe.mean(), 2), mae=round(d.mae.mean(), 2)))
def grp(d, by):
    return pd.DataFrame({k: agg(g) for k, g in d.groupby(by)}).T
for a in ["p", "t1", "t2"]:
    d = T[T.acct == a]
    print("=====", a); print(agg(d).to_dict())
    print(grp(d, "strategy").sort_values("pnl").to_string())
    print("side"); print(grp(d, "side").to_string())
    print("hour"); print(grp(d, "hour").to_string())
    print("lot_no"); print(grp(d, "lot_no").to_string())
    print("sym_stacked x lot"); print(grp(d, ["sym_stacked", "lot_no"]).to_string())
    print("after_restart"); print(grp(d, "after_restart").to_string())
    print("ex_primary"); print(grp(d, "ex_primary").to_string())
    print("exit"); print(grp(d, "exit_reason").to_string())
