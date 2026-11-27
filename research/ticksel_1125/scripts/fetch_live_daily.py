"""Daily SIP bars (Alpaca GET only) for live-trade symbols of the TICKSEL setups + SPY, 2026-06-01..11-24. Educational only."""
import sys
from datetime import datetime
import pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox")
from mcf.data.priors import _bars, _client
T = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel/"
d = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/live_dedup.parquet")
syms = sorted(set(d.symbol.dropna().astype(str)) | {"SPY"})
raw = _bars(_client(), syms, datetime(2026, 6, 1), datetime(2026, 11, 25), None, "sip")
raw = raw.reset_index()
raw["date"] = pd.to_datetime(raw["timestamp"]).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
raw = raw[["symbol", "date", "open", "high", "low", "close", "volume"]]
raw.to_parquet(T + "live_daily.parquet")
print(raw.shape, raw.symbol.nunique(), raw.date.min(), raw.date.max())
