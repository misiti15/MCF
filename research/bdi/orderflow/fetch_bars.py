"""1-minute and daily SIP bars (read-only Alpaca market data) for the 40 OF-A symbols, 2026-07-15..10-09, regular
session, for daily ATR and the bar-level signatures (C3b, C6). -> data/bars1m.parquet, data/daily.parquet.
Educational only - not financial advice."""
from __future__ import annotations

import os

import pandas as pd
import requests

from fetch_agg import DATA, SYMBOLS

H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}


def bars(tf: str, start: str, end: str) -> pd.DataFrame:
    rows, tok = [], None
    while True:
        p = {"symbols": ",".join(SYMBOLS), "timeframe": tf, "start": start, "end": end, "feed": "sip", "limit": 10000,
             "adjustment": "raw"}
        if tok:
            p["page_token"] = tok
        j = requests.get("https://data.alpaca.markets/v2/stocks/bars", headers=H, params=p, timeout=60).json()
        for s, L in (j.get("bars") or {}).items():
            for b in L:
                rows.append((s, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]))
        tok = j.get("next_page_token")
        if not tok:
            break
    df = pd.DataFrame(rows, columns=["symbol", "t", "open", "high", "low", "close", "volume"])
    df["t"] = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
    return df


def main():
    d = bars("1Day", "2026-06-01", "2026-10-10")
    d["date"] = d.t.dt.date
    d.drop(columns="t").to_parquet(DATA / "daily.parquet", index=False)
    m = bars("1Min", "2026-07-15T13:30:00Z", "2026-10-09T20:00:00Z")
    hm = m.t.dt.hour * 100 + m.t.dt.minute
    m = m[(hm >= 930) & (hm < 1600)]
    m.to_parquet(DATA / "bars1m.parquet", index=False)
    print(d.shape, m.shape)


if __name__ == "__main__":
    main()
