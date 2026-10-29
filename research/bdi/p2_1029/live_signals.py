"""Live (paper) signal funnel for the dormant / low Testing 1 / Testing 2 setups (tiers.csv): per setup, signals,
unique symbol-day signals, submitted, and skip reasons since the setup entered the account (through 2026-10-28).
Usage: python live_signals.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3, re
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "tiers.csv"); R = R[R.tier.isin(["dormant", "low"])]
rows = []
for acct, j in (("testing", "t1"), ("testing2", "t2")):
    G = pd.read_sql("select day, symbol, strategy, status, reason from signals where run_id=1", sqlite3.connect(S / j / "journal.db"))
    for _, r in R[R.acct == acct].iterrows():
        g = G[(G.strategy == r.setup) & (G.day >= r.start) & (G.day <= "2026-10-28")]
        rs = g[g.status != "submitted"].reason.fillna("").map(lambda s: re.sub(r"[\d.$]+", "#", s)[:40]).value_counts()
        rows.append(dict(acct=acct, setup=r.setup, tier=r.tier, sessions=r.sessions, trades=r.trades, per_sess=r.per_sess,
                         signals=len(g), symdays=g.groupby(["day", "symbol"]).ngroups,
                         symdays_per_sess=round(g.groupby(["day", "symbol"]).ngroups / r.sessions, 2),
                         skip_reasons="; ".join(f"{k}:{v}" for k, v in rs.items())))
X = pd.DataFrame(rows); X.to_csv(OUT / "live_signals.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
print(X.to_string(index=False))
