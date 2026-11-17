"""Live trades + live signals of the parent from every account journal (read-only). Educational only."""
import pandas as pd
from mcf.report import blueprint as B, engine as E
S = "RW6G1-ns2-up3-vwap2sd-short-FD"
tr, _ = E.live_trades(S)
pd.DataFrame(tr).to_parquet("live_trades.parquet")
rows = []
for acct, br in B.data_branches().items():
    db = B._journal(br)
    if db is None: continue
    cols = [r[1] for r in db.execute("PRAGMA table_info(signals)")]
    cur = db.execute("SELECT * FROM signals WHERE run_id = 1 AND strategy = ?", (S,))
    for r in cur.fetchall():
        d = dict(zip(cols, r)); d["acct"] = acct; rows.append(d)
s = pd.DataFrame(rows); print(s.columns.tolist()); print(s.head())
s.to_parquet("signals.parquet")
t = pd.DataFrame(tr); print(len(t), t.r.mean(), t.groupby("acct").r.agg(["size","mean"]))
