"""eu1103/edge: SIP 1-minute RTH bars for every symbol-day traded live (run_id 1, 5 accounts, 10-06..11-02) plus
SPY/QQQ (Alpaca market-data GET only). Usage: python fetch_live_bars.py <scratch>. Educational only - not financial advice."""
import sqlite3, sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client

S = Path(sys.argv[1])
B = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen"]
T = pd.concat([pd.read_sql("select symbol,date from trades where run_id=1", sqlite3.connect(S / f"{b}.db")) for b in B])
dc = _client(); fr = []
for d, g in T.groupby("date"):
    syms = sorted(set(g.symbol) | {"SPY", "QQQ"})
    a = datetime.combine(pd.Timestamp(d).date(), datetime.min.time()) + timedelta(hours=13)
    raw = _bars(dc, syms, a, a + timedelta(hours=8), 1, "sip")
    for s, x in raw.groupby(level=0):
        x = rth(normalize(x.droplevel(0)))
        if len(x):
            fr.append(x.assign(symbol=s).reset_index().rename(columns={"index": "ts", "timestamp": "ts"}))
    print(d, len(syms), flush=True)
X = pd.concat(fr, ignore_index=True)
X[["symbol", "ts", "open", "high", "low", "close", "volume"]].to_parquet(S / "live_bars.parquet")
print(len(X), X.symbol.nunique())
