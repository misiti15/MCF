"""Fetch UUP (dollar proxy, not in the lab universe) read-only from Alpaca market data: 1-minute bars on the open
history (feed sip, split-adjusted) and daily bars 2016..2026. Locked-block rows (2024-11-01..2025-02-28) are dropped
before saving. Keys from ALPACA_API_KEY / ALPACA_SECRET_KEY (never logged). Market-data GET only, no trading endpoint.
Educational only - not financial advice."""
import os
import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
URL = "https://data.alpaca.markets/v2/stocks/bars"
LOCK = ("2024-11-01", "2025-02-28")


def pull(tf, start, end, adj):
    s = requests.Session()
    s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    p = {"symbols": "UUP", "timeframe": tf, "start": start, "end": end, "feed": "sip", "adjustment": adj, "limit": 10000}
    rows = []
    while True:
        r = s.get(URL, params=p, timeout=60)
        if r.status_code == 429:
            time.sleep(3)
            continue
        r.raise_for_status()
        j = r.json()
        rows += (j.get("bars") or {}).get("UUP", [])
        if not j.get("next_page_token"):
            break
        p["page_token"] = j["next_page_token"]
        time.sleep(0.3)
    df = pd.DataFrame(rows).rename(columns={"t": "ts", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("America/New_York")
    d = df["ts"].dt.strftime("%Y-%m-%d")
    return df[(d < LOCK[0]) | (d > LOCK[1])][["ts", "open", "high", "low", "close", "volume"]]


m = pull("1Min", "2024-09-16", "2026-10-08", "split")
m = m[(m["ts"].dt.hour * 60 + m["ts"].dt.minute >= 570) & (m["ts"].dt.hour * 60 + m["ts"].dt.minute <= 959)]
m.to_parquet(HERE / "data" / "uup_1min.parquet")
d = pull("1Day", "2016-01-01", "2026-10-10", "all")
d.to_parquet(HERE / "data" / "uup_daily.parquet")
print("UUP", len(m), "1-min rows;", len(d), "daily rows")
