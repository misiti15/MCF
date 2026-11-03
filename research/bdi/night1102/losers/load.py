"""Live trades (run_id 1, all 5 intraday journals) 2026-10-20..11-02 + read-only Alpaca 1-minute SIP bars for every
traded symbol-day (plus SPY/QQQ) into scratch. Usage: python load.py <scratch>. Educational only - not financial advice."""
import sqlite3, subprocess, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.replay import store
S = Path(sys.argv[1]); (S / "j").mkdir(parents=True, exist_ok=True); (S / "bars").mkdir(exist_ok=True)
A = {"primary": "mcf-data", "testing1": "mcf-data-testing", "testing2": "mcf-data-testing2",
     "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}
out = []
for a, b in A.items():
    p = S / "j" / f"{b}.db"
    if not p.exists():
        p.write_bytes(subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{b}:journal.db"], capture_output=True, check=True).stdout)
    c = sqlite3.connect(p)
    t = pd.read_sql("select * from trades where run_id=1 and date>='2026-10-20' and date<='2026-11-02'", c)
    t["account"] = a; out.append(t)
t = pd.concat(out, ignore_index=True)
t["risk"] = (t.entry - t.stop).abs() * t.shares
t = t[(t.risk > 0) & t.pnl_adj.notna()].copy()
t["R"] = t.pnl_adj / t.risk
t.to_parquet(S / "trades.parquet", index=False)
for d, g in t.groupby("date"):
    p = S / "bars" / f"{d}.parquet"
    if p.exists():
        continue
    syms = sorted(set(g.symbol) | {"SPY", "QQQ"})
    df = store._fetch_bars(syms, f"{d}T13:00:00Z", f"{d}T21:00:00Z", "1Min").set_index("ts")
    df.index = df.index.tz_convert("America/New_York")
    df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
    df.reset_index().to_parquet(p, compression="zstd", index=False)
    print(d, df.symbol.nunique(), "of", len(syms), len(df), flush=True)
