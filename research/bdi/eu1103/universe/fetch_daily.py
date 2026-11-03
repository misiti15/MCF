"""Read-only Alpaca market-data GET: SIP daily bars 2025-03-03..2026-11-02 for every name in the 11-02 live universe
(+ the 11 sector SPDRs). Locked block (2024-11..2025-02) not requested. Usage: python fetch_daily.py <scratch>
-> <scratch>/daily.parquet. Educational only - not financial advice."""
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.priors import _bars, _client

S = Path(sys.argv[1])
u = pd.read_csv(S / "universe_live.csv")
syms = sorted(set(u.symbol.astype(str)) | set("XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SPY".split()))
raw = _bars(_client(), syms, datetime(2025, 3, 3), datetime(2026, 11, 3), None, "sip", batch=200, workers=4)
raw = raw.reset_index()
raw["date"] = pd.to_datetime(raw["timestamp"]).dt.tz_convert("America/New_York").dt.date.astype(str)
raw = raw[["symbol", "date", "open", "high", "low", "close", "volume", "vwap"]]
for c in ("open", "high", "low", "close", "vwap"):
    raw[c] = raw[c].astype("float32")
raw.to_parquet(S / "daily.parquet", index=False, compression="zstd")
print(len(syms), raw.symbol.nunique(), len(raw), raw.date.min(), raw.date.max())
