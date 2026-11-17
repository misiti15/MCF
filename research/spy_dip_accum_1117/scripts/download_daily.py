"""SPY dip accumulation (2026-11-17): daily bars for SPY / SPXL / UPRO / SSO / BIL.

Alpaca SIP 1Day, adjustment=all (split + dividend adjusted = total-return proxy), read-only market-data endpoint,
keys from the environment and never printed (same pattern as research/longhold/download_extra.py).
Rows inside the locked block 2024-11-01..2025-02-28 are dropped before anything is kept.
Usage: python download_daily.py OUT.parquet   Educational only - not financial advice.
"""
from __future__ import annotations

import os
import sys
import time

import pandas as pd
import requests

URL = "https://data.alpaca.markets/v2/stocks/bars"
SYMS = ["SPY", "SPXL", "UPRO", "SSO", "BIL"]
LOCK = ("2024-11-01", "2025-02-28")


def main(out, start="2008-01-01"):
    s = requests.Session()
    s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    params = {"symbols": ",".join(SYMS), "timeframe": "1Day", "start": start, "end": pd.Timestamp.now("UTC").strftime("%Y-%m-%d"),
              "feed": "sip", "adjustment": "all", "limit": 10000}
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
    df = df.drop(columns="t")
    df = df[~df.date.between(pd.Timestamp(LOCK[0]), pd.Timestamp(LOCK[1]))]
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    df.to_parquet(out, index=False)
    print(df.groupby("symbol").date.agg(["min", "max", "size"]))


if __name__ == "__main__":
    main(sys.argv[1])
