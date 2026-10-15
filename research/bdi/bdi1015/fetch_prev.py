"""Read-only SIP 1-minute bars (Alpaca market data only) for SPY, QQQ, SPXL, UPRO, TQQQ on 2026-10-14 (prior closes for
the 2026-10-15 descriptive check). Usage: python fetch_prev.py <out_dir>. Educational only - not financial advice."""
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); S.mkdir(parents=True, exist_ok=True)
a, b = datetime(2026, 10, 14, 13, tzinfo=timezone.utc), datetime(2026, 10, 14, 21, tzinfo=timezone.utc)
for s, g in fetch_bars(["SPY", "QQQ", "SPXL", "UPRO", "TQQQ"], a, b, feed="sip", client=_client()).items():
    g.to_parquet(S / f"{s}.parquet"); print(s, len(g))
