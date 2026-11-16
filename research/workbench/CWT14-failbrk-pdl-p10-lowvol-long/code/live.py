"""Pull every live trade of the parent from the account journals (read-only). Educational only - not financial advice."""
import sys, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-cwt14pdl")
from mcf.report.blueprint import data_branches, _journal
SID = "CWT14-failbrk-pdl-p10-lowvol-long"
out = []
for acct, br in data_branches().items():
    db = _journal(br)
    if db is None: continue
    try:
        df = pd.read_sql_query("SELECT * FROM trades WHERE run_id = 1 AND strategy = ? AND exit_time IS NOT NULL", db, params=(SID,))
    except Exception as e:
        continue
    df["acct"] = acct; out.append(df)
L = pd.concat(out, ignore_index=True)
L["pnl_adj"] = L.pnl_adj.fillna(L.pnl)
L["R"] = L.pnl_adj / ((L.entry - L.stop).abs() * L.shares)
L.to_parquet(sys.argv[1]); print(len(L), L.date.nunique(), L.R.mean(), L.groupby("acct").R.agg(["count","mean"]))
