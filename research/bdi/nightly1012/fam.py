import sys, re, pandas as pd, numpy as np
pd.set_option("display.width", 250)
S = sys.argv[1]
T = pd.read_csv(f"{S}/trades_all.csv")
for c in ("entry_time", "exit_time"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
d = T[T.acct == "t2"].copy()
d["fam"] = d.strategy.str.extract(r"^(CWT\d+-[a-z]+)")[0]
d["lev"] = d.strategy.str.extract(r"-(orl|pdl|pdh)-")[0]
d["lowvol"] = d.strategy.str.contains("lowvol")
f = lambda g: pd.Series({"n": len(g), "win%": round(100 * (g.pnl > 0).mean()), "avgR": round(g.r_multiple.mean(), 3), "pnl": round(g.pnl.sum(), 1), "stop%": round(100 * (g.exit_reason == "stop").mean()), "mfe": round(g.mfe.mean(), 2)})
print(d.groupby(["fam", "side"]).apply(f).to_string())
c14 = d[d.fam == "CWT14-failbrk"]
print(c14.groupby(["lev", "lowvol"]).apply(f).to_string())
print(c14.groupby(c14.strategy.str.contains("p05").rename("p05")).apply(f).to_string())
# concurrency of same-side
d = d.sort_values("entry_time")
d["same_side_open"] = [((d.entry_time < r.entry_time) & (d.exit_time > r.entry_time) & (d.side == r.side)).sum() for r in d.itertuples()]
d["crowd"] = pd.cut(d.same_side_open, [-1, 20, 40, 60, 200])
print(d[d.side == 1].groupby("crowd").apply(f).to_string())
# open-history expectations from config comments
txt = open("/home/user/MCF/config/account_testing2.yaml").read()
exp = {}
for m in re.finditer(r"open history n (\d+), exp ([+-][0-9.]+)R, t ([+-]?[0-9.]+), ([0-9.]+)/day; verdict (\w+)\n\s+(\S+):", txt):
    exp[m.group(6)] = (int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5))
X = T[T.acct == "t2"].groupby("strategy").agg(n=("pnl", "size"), avgR=("r_multiple", "mean"), pnl=("pnl", "sum"))
X["hist_exp"] = [exp.get(s, (None,)*5)[1] for s in X.index]; X["hist_t"] = [exp.get(s, (None,)*5)[2] for s in X.index]; X["hist_per_day"] = [exp.get(s, (None,)*5)[3] for s in X.index]; X["verdict"] = [exp.get(s, (None,)*5)[4] for s in X.index]
print(X.round(3).sort_values("pnl").to_string())
print("setups with no trades:", sorted(set(exp) - set(X.index)))
print("n hist neg:", sum(1 for v in exp.values() if v[1] < 0), "of", len(exp))
X.to_csv(f"{S}/t2_vs_hist.csv")
