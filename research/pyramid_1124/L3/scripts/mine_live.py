"""Part A: live losers' pattern for the top-3 live longs. Educational only - not financial advice."""
import json, numpy as np, pandas as pd
t = pd.read_pickle("live_ext.pkl")
def idx(s):
    b = pd.read_parquet(f"live_{s}.parquet"); b.index = b.index.tz_convert("America/New_York")
    b["d"] = b.index.date.astype(str); b["pv"] = b.close*b.volume
    b["vwap"] = b.groupby("d").pv.cumsum()/b.groupby("d").volume.cumsum()
    b["o"] = b.groupby("d").open.transform("first"); return b
S, Q = idx("SPY"), idx("QQQ")
def state(b, ts):
    i = b.index.searchsorted(ts) - 1
    r = b.iloc[i]; r30 = b.iloc[max(i-30, 0)]
    return (r.close/r.o-1)*100, (r.close/r.vwap-1)*100, (r.close/r30.close-1)*100
rows = []
L = t[(t.side == 1)]
for s in ["GEN-261027-01", "GEN-261020-09", "GEN-261019-02", "CWT14-failbrk-orl-p10-long-WB5"]:
    g = L[L.strategy.str.startswith(s)].copy()
    et = pd.to_datetime(g.entry_time, utc=True).dt.tz_convert("America/New_York")
    xt = pd.to_datetime(g.exit_time, utc=True).dt.tz_convert("America/New_York")
    g["em"] = et.dt.hour*100 + et.dt.minute; g["hold"] = (xt-et).dt.total_seconds()/60
    st = [state(S, x) for x in et]; q = [state(Q, x) for x in et]
    g["spy_fo"], g["spy_vw"], g["spy30"] = zip(*st); g["qqq_fo"], g["qqq_vw"], g["qqq30"] = zip(*q)
    g["spread"] = g.meta.map(lambda m: json.loads(m.split(";")[0]).get("spread_bps") if m else np.nan)
    g["dow"] = pd.to_datetime(g.date).dt.dayofweek
    g["key"] = s; rows.append(g)
x = pd.concat(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
cols = ["date", "symbol", "account", "em", "entry", "r", "exit_reason", "hold", "spy_fo", "spy_vw", "spy30", "qqq_fo", "qqq30", "spread"]
for k, g in x.groupby("key"):
    print("=====", k, len(g), "avg", round(g.r.mean(), 3))
    g = g.assign(win=g.r > 0)
    print(g.groupby("win")[["em", "hold", "spy_fo", "spy_vw", "spy30", "qqq_fo", "qqq30", "spread", "entry"]].median().round(3))
    print(g.groupby("date").r.agg(["size", "sum", "mean"]).round(2).T.to_string())
    for c, bins in [("em", [0, 1130, 1200, 1230, 1330, 1400, 1430, 1500, 1600]), ("spy_vw", [-9, -0.3, 0, 0.3, 9]),
                    ("spy30", [-9, -0.15, 0, 0.15, 9]), ("qqq_fo", [-9, -1, -0.5, -0.3, 0, 9]), ("spread", [0, 5, 10, 20, 999]), ("entry", [0, 10, 20, 50, 1e5])]:
        print(c, g.groupby(pd.cut(g[c], bins), observed=True).r.agg(["size", "mean"]).round(3).T.to_string())
x.drop(columns=["meta"]).to_csv("live_top3_trades.csv", index=False)
