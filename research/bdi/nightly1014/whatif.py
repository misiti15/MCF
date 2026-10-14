"""What-if (run 2: simulated signals not taken) per skip reason / setup / side. Educational only."""
import sys, sqlite3, pandas as pd
S, acct = sys.argv[1], sys.argv[2]
w = pd.read_sql("select * from trades where date='2026-10-14' and run_id=2", sqlite3.connect(f"{S}/{acct}/journal.db"))
w["why"] = w.meta.str.extract(r"why=([^;]*)")[0].str.replace(r"\d+", "#", regex=True)
pd.set_option("display.width", 200)
print(w.groupby("why").agg(n=("id", "size"), R=("r_multiple", "sum"), avgR=("r_multiple", "mean"), pnl=("pnl", "sum")).round(2).to_string())
for k in sys.argv[3:]:
    h = w[w.why == k]
    print("==", k); print(h.groupby(["strategy"]).agg(n=("id", "size"), R=("r_multiple", "sum"), avgR=("r_multiple", "mean")).round(2).sort_values("R").to_string())
    print(h.groupby("side").r_multiple.agg(["size", "sum", "mean"]).round(3).to_string())
