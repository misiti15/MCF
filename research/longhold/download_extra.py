"""Longhold (2026-10-10): extra ETF daily bars not in research/swarm1010/w3_daily/data/daily_2016.parquet.

Benchmarks and cash/bond legs only: RSP (equal-weight S&P 500, point-in-time membership -> survivorship yardstick),
MTUM / USMV / SPLV / QUAL (factor ETFs, reference only), BIL (T-bills = cash), SHY / IEF / AGG (bonds), VTI.
Alpaca SIP 1Day, adjustment=all, 2016-01-01..today, read-only market-data endpoint, keys never printed.
Output: research/longhold/data/etf_extra.parquet (git-ignored). Educational only - not financial advice.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
URL = "https://data.alpaca.markets/v2/stocks/bars"
SYMS = ["RSP", "MTUM", "USMV", "SPLV", "QUAL", "BIL", "SHY", "IEF", "AGG", "VTI"]


def main(start="2016-01-01"):
    end = pd.Timestamp.now("UTC").strftime("%Y-%m-%d")
    s = requests.Session()
    s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    params = {"symbols": ",".join(SYMS), "timeframe": "1Day", "start": start, "end": end, "feed": "sip",
              "adjustment": "all", "limit": 10000}
    rows = []
    while True:
        r = s.get(URL, params=params, timeout=90)
        r.raise_for_status()
        j = r.json()
        for sym, bars in (j.get("bars") or {}).items():
            rows += [(sym, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bars]
        tok = j.get("next_page_token")
        if not tok:
            break
        params["page_token"] = tok
        time.sleep(0.35)
    df = pd.DataFrame(rows, columns=["symbol", "t", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    df = df.drop(columns="t").sort_values(["symbol", "date"]).reset_index(drop=True)
    (HERE / "data").mkdir(exist_ok=True)
    df.to_parquet(HERE / "data" / "etf_extra.parquet", compression="zstd", index=False)
    print(df.groupby("symbol").date.agg(["min", "max", "size"]))


if __name__ == "__main__":
    main()
