"""U9 prep: build the what-if signal sets from the live journals (signals table, live run as journaled)."""
import sqlite3, glob, json, sys
import pandas as pd
S = sys.argv[1]
fr = []
for f in sorted(glob.glob(f"{S}/j/*.db")):
    c = sqlite3.connect(f)
    d = pd.read_sql("select day,ts,symbol,strategy,side,status,reason,ref_price,stop,target,entry_type,broker_order_id from signals "
                    "where status in ('submitted','skipped','rejected')", c)
    d["acct"] = f.split("/")[-1][:-3]
    fr.append(d)
A = pd.concat(fr, ignore_index=True)
A = A[(A.day >= "2026-10-06") & (A.day <= "2026-11-17")]
k = ["acct", "day", "strategy", "symbol"]
etb = A[A.reason == "not shortable/ETB"].sort_values("ts").drop_duplicates(k)
sub = A[(A.status == "submitted") & (A.side == -1) & A.strategy.isin(set(etb.strategy))].sort_values("ts").drop_duplicates(k)
tgt = A[(A.status == "rejected") & A.reason.str.contains("take_profit", na=False)].copy()
tgt["base"] = tgt.reason.map(lambda r: float(json.loads(r)["base_price"]))
etb.assign(set="etb").to_csv(f"{S}/w_etb.csv", index=False)
sub.assign(set="sub").to_csv(f"{S}/w_sub.csv", index=False)
tgt.assign(set="tgt").to_csv(f"{S}/w_tgt.csv", index=False)
sd = pd.concat([etb, sub, tgt])[["day", "symbol"]].drop_duplicates()
sd.to_csv(f"{S}/symdays.csv", index=False)
print(len(etb), len(sub), len(tgt), "symdays", len(sd), "days", sd.day.nunique())
