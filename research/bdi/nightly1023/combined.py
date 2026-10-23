"""Promotion / demotion suggestion table, 2026-10-23: one row per setup with its combined live (paper) record across
Primary, Testing 1, Testing 2 and the Setup Generator account, merged by setup name as the dashboard does
(mcf/report/scorecard.leaderboard fields: trades, sessions, win rate, break-even win rate, avg R, t).
Costs are in: avgR_c = pnl_adj / $ risk per trade; the journal r_multiple (what the dashboard shows) is avgR_j.
t_j is the dashboard's per-trade t on r_multiple; t_day is the day-clustered t on avgR_c (sum of R per session,
rule 4). last4 = avg R after costs over the last 4 sessions in the journals (10-20..10-23). bt = backtest expectancy
(scorecard._expected: Apr-Jun 2026 exp R / CWT scored exp / scorecard_expectations), '(base)' = the non-FD version's.
Known gap: Testing 1's journal misses 132 of 457 trades on 2026-10-19 (final push failed; nightly1019).
Writes combined.csv and combined_out.txt.  Usage: python combined.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3, json
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.report.scorecard import _expected
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
A = json.load(open("/home/user/MCF/docs/live/assignments.json"))["setups"]
rows = []
for a, lab in (("p", "primary"), ("t1", "testing"), ("t2", "testing2"), ("gy", "graveyard"), ("gen", "gen")):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, entry, stop, shares, pnl, pnl_adj, r_multiple from trades where run_id=1 and exit is not null", c)
    t["acct"] = lab; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T["rc"] = np.where(T.risk > 0, T.pnl_adj / T.risk, T.r_multiple)
dates = sorted(T.date.unique()); last4 = dates[-4:]
exp = _expected()
out = []
for s, g in T.groupby("strategy"):
    r, rc = g.r_multiple.astype(float), g.rc.astype(float)
    n = len(g); aw = r[r > 0].mean() if (r > 0).any() else np.nan; al = -r[r <= 0].mean() if (r <= 0).any() else np.nan
    day = g.groupby("date").rc.sum(); k = len(day)
    bt = exp.get(s); btsrc = ""
    if bt is None and s.endswith("-FD") and exp.get(s[:-3]) is not None:
        bt, btsrc = exp[s[:-3]], "(base)"
    rec = g[g.date.isin(last4)]
    out.append(dict(setup=s, now=",".join(A.get(s, {}).get("accounts", ["(not assigned)"])), accts=",".join(sorted(g.acct.unique())),
                    trades=n, sessions=k, first=g.date.min(), win=round((g.pnl > 0).mean(), 3),
                    be_win=round(al / (aw + al), 3) if aw == aw and al == al else np.nan,
                    avgR_j=round(r.mean(), 3), avgR_c=round(rc.mean(), 3),
                    t_j=round(r.mean() / (r.std(ddof=1) / n ** .5), 2) if n > 1 and r.std(ddof=1) > 0 else np.nan,
                    t_day=round(day.mean() / (day.std(ddof=1) / k ** .5), 2) if k > 1 and day.std(ddof=1) > 0 else np.nan,
                    last4_n=len(rec), last4_R=round(rec.rc.mean(), 3) if len(rec) else np.nan,
                    pnl_adj=round(g.pnl_adj.sum(), 2), bt=None if bt is None else round(bt, 3), bt_src=btsrc,
                    today_n=int((g.date == dates[-1]).sum()), today_R=round(g[g.date == dates[-1]].rc.sum(), 2)))
C = pd.DataFrame(out).sort_values(["now", "avgR_c"])
C.to_csv(OUT / "combined.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 300); pd.set_option("display.max_colwidth", 48)
txt = f"sessions in journals: {dates[0]}..{dates[-1]} ({len(dates)}); last4 = {last4}\n" + C.drop(columns=["first"]).to_string(index=False)
open(OUT / "combined_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
