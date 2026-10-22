"""regime1022: read-only SIP 1-minute bars of SPY / QQQ / IWM for 2026-09-01..2026-10-21, to label the live paper
sessions (10-06..10-21) with the same regime rules as the history (needs 20 prior sessions for the range median).
Market-data GET only; keys come from the environment and are never written. Educational only - not financial advice."""
from __future__ import annotations

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from rc import ROOT, SCR

sys.path.insert(0, str(ROOT))
from mcf.data.alpaca_data import _client, fetch_bars  # noqa: E402


def main():
    tz = ZoneInfo("America/New_York")
    got = fetch_bars(["SPY", "QQQ", "IWM"], datetime(2026, 9, 1, 9, 30, tzinfo=tz), datetime(2026, 10, 21, 16, 0, tzinfo=tz),
                     feed="sip", client=_client())
    parts = []
    for s, df in got.items():
        d = df.copy()
        d["symbol"] = s
        parts.append(d)
    b = pd.concat(parts)
    b.index = pd.to_datetime(b.index, utc=True).tz_convert(tz)
    b = b[(b.index.time >= pd.Timestamp("09:30").time()) & (b.index.time < pd.Timestamp("16:00").time())]
    b["date"] = b.index.date
    b.to_parquet(SCR / "idx_live_1min.parquet")
    d = b.groupby(["symbol", "date"]).agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                         close=("close", "last")).reset_index()
    d.to_parquet(SCR / "idx_live_daily.parquet")
    print(d[d.symbol == "SPY"].tail(12).to_string())


if __name__ == "__main__":
    main()
