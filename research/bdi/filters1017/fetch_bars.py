"""Read-only Alpaca 1-min SIP bars for journal symbol-days. Educational only."""
import sys, sqlite3, pandas as pd
from datetime import datetime, timezone, timedelta
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = sys.argv[1]
sd = set()
for f in ["p.db", "t1.db", "t2.db"]:
    t = pd.read_sql("select symbol,date from trades where run_id=1", sqlite3.connect(f"{S}/{f}"))
    sd |= set(map(tuple, t.values))
by = {}
for s, d in sd: by.setdefault(d, set()).add(s)
cl = _client()
for d, syms in sorted(by.items()):
    syms = sorted(syms)
    y, m, dd = map(int, d.split("-"))
    a = datetime(y, m, dd, 13, 0, tzinfo=timezone.utc); b = datetime(y, m, dd, 20, 30, tzinfo=timezone.utc)
    out = []
    for i in range(0, len(syms), 100):
        for s, g in fetch_bars(syms[i:i+100], a, b, feed="sip", client=cl).items():
            g = g.copy(); g["symbol"] = s; out.append(g)
    df = pd.concat(out); df.to_parquet(f"{S}/bars/{d}.parquet"); print(d, len(syms), len(df), flush=True)
