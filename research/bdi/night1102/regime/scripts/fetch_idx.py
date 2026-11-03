"""night1102/regime: read-only SIP 1-minute bars of SPY/QQQ/IWM/RSP for 2026-09-01..2026-11-02 (to tag the live
sessions 10-06..11-02). Market-data GET only; keys come from the environment and are never written.
Educational only - not financial advice."""
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from mcf.data.alpaca_data import _client, fetch_bars  # noqa: E402

SCR = Path(sys.argv[1])
tz = ZoneInfo("America/New_York")
got = fetch_bars(["SPY", "QQQ", "IWM", "RSP"], datetime(2026, 9, 1, 9, 30, tzinfo=tz),
                 datetime(2026, 11, 2, 16, 0, tzinfo=tz), feed="sip", client=_client())
parts = []
for s, df in got.items():
    d = df.copy(); d["symbol"] = s; parts.append(d)
b = pd.concat(parts)
b.index = pd.to_datetime(b.index, utc=True).tz_convert(tz)
b = b[(b.index.time >= pd.Timestamp("09:30").time()) & (b.index.time < pd.Timestamp("16:00").time())]
b["date"] = b.index.date
b.to_parquet(SCR / "idx_1min.parquet")
print(b.groupby("symbol").size(), b["date"].max())
