"""REPS1 step 1: every live paper signal since 10-20 from the 7 account journals (signals + trades). Educational only.
    python -I load.py <journal dir> <out dir>"""
import sys, os, glob, sqlite3, pandas as pd
J, O = sys.argv[1], sys.argv[2]; S, T = [], []
for p in sorted(glob.glob(f"{J}/mcf-data*.db")):
    if os.path.getsize(p) == 0: continue
    a = os.path.basename(p)[:-3]; c = sqlite3.connect(p)
    pid = ",".join(str(r[0]) for r in c.execute("select id from runs where kind='paper'"))
    s = pd.read_sql(f"select day,ts,symbol,strategy,side,status,reason,ref_price,stop,target,entry_type,entry_price from signals "
                    f"where run_id in ({pid}) and day>='2026-10-20' and day<='2026-11-10'", c); s["acct"] = a; S.append(s)
    t = pd.read_sql(f"select date,symbol,strategy,side,signal_time,entry_time,entry,stop,target,exit_time,exit,exit_reason,shares,pnl,pnl_adj "
                    f"from trades where run_id in ({pid}) and date>='2026-10-20' and date<='2026-11-10'", c); t["acct"] = a; T.append(t)
S, T = pd.concat(S, ignore_index=True), pd.concat(T, ignore_index=True)
S.to_csv(f"{O}/signals.csv.gz", index=False); T.to_csv(f"{O}/trades.csv.gz", index=False)
print("signals", len(S), "trades", len(T), "symbols", S.symbol.nunique(), "symbol-days", S.groupby(["symbol", "day"]).ngroups, "sessions", S.day.nunique())
