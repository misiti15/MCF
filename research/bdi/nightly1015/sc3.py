"""3-account scorecard summary (reports/scorecard.json as of 2026-10-15 EOD) plus journal totals by day. Educational only."""
import sys, json, sqlite3, pandas as pd
S = sys.argv[1]
pd.set_option("display.width", 250)
for a in ("p", "t1", "t2"):
    d = json.load(open(f"{S}/{a}/scorecard.json"))
    s = pd.DataFrame(d["setups"])
    t = pd.read_sql("select date, pnl, r_multiple from trades where run_id=1", sqlite3.connect(f"{S}/{a}/journal.db"))
    byday = t.groupby("date").agg(n=("pnl", "size"), pnl=("pnl", "sum"), avgR=("r_multiple", "mean")).round(3).tail(6)
    print(f"===== {a}: scorecard {d['sessions']} sessions, {d['window']}; trades {s.trades.sum()}, P/L {s.pnl.sum():.2f}")
    print(byday.to_string())
    print(s.verdict.value_counts().to_dict())
    flag = s[s.verdict.isin(["below backtest - review", "negative so far"])].sort_values("pnl")
    print(flag[["setup", "trades", "win_rate", "avg_r", "pnl", "expected_r", "verdict"]].head(12).to_string())
    print(s[s.verdict == "positive so far"].sort_values("pnl", ascending=False)[["setup", "trades", "win_rate", "avg_r", "pnl", "expected_r"]].head(8).to_string())
