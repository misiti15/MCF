"""eu1103/preopen: raw (unadjusted) SIP daily bars for the lab universe, so pre-market gaps (raw 30-minute bars) are
measured against a raw prior close. Two ranges that skip the rule-19 locked block 2024-11-01..2025-02-28 (asserted).
    python fetch_daily_hist.py <scratch>  -> <scratch>/hist_daily_raw.parquet
Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.longhold.data import SipDaily

S = Path(sys.argv[1])
syms = sorted(pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet", columns=["symbol"]).symbol.astype(str).unique())
c = SipDaily()
d = pd.concat([c.bars(syms, "2024-08-15", "2024-10-31", adjustment="raw"), c.bars(syms, "2025-03-01", "2026-09-16", adjustment="raw")])
d["date"] = pd.to_datetime(d.date).dt.strftime("%Y-%m-%d")
assert not ((d.date >= "2024-11-01") & (d.date <= "2025-02-28")).any()
d.to_parquet(S / "hist_daily_raw.parquet", index=False)
print(len(d))
