"""SIP daily bars for the long-hold runner (read-only market-data endpoint, same request as
research/swarm1010/w3_daily/download_daily.py). Keys from ALPACA_API_KEY / ALPACA_SECRET_KEY (the SIP data plan),
never printed. Educational only - not financial advice."""
from __future__ import annotations

import os
import time

import pandas as pd

URL = "https://data.alpaca.markets/v2/stocks/bars"
COLS = ["symbol", "date", "open", "high", "low", "close", "volume"]


class SipDaily:
    def __init__(self, key: str | None = None, secret: str | None = None, feed: str = "sip"):
        import requests

        self.sess = requests.Session()
        self.sess.headers.update({"APCA-API-KEY-ID": key or os.environ["ALPACA_API_KEY"],
                                  "APCA-API-SECRET-KEY": secret or os.environ["ALPACA_SECRET_KEY"]})
        self.feed = feed

    def _get(self, params):
        import requests

        wait = 1.0
        for _ in range(10):
            try:
                r = self.sess.get(URL, params=params, timeout=90)
            except requests.RequestException:
                time.sleep(wait); wait = min(wait * 2, 60); continue
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(wait); wait = min(wait * 2, 60); continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError("market data: gave up after retries")

    def bars(self, symbols: list[str], start, end, adjustment: str = "all") -> pd.DataFrame:
        """Long frame symbol, date (ET session date, naive), open, high, low, close, volume."""
        rows = []
        syms = list(dict.fromkeys(symbols))
        for i in range(0, len(syms), 100):
            params = {"symbols": ",".join(syms[i:i + 100]), "timeframe": "1Day", "start": str(start),
                      "end": str(end), "feed": self.feed, "adjustment": adjustment, "limit": 10000}
            while True:
                j = self._get(params)
                for s, bs in (j.get("bars") or {}).items():
                    rows += [(s, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bs]
                tok = j.get("next_page_token")
                if not tok:
                    break
                params["page_token"] = tok
                time.sleep(0.35)
        df = pd.DataFrame(rows, columns=["symbol", "t", "open", "high", "low", "close", "volume"])
        if df.empty:
            return pd.DataFrame(columns=COLS)
        df["date"] = (pd.to_datetime(df["t"], utc=True).dt.tz_convert("America/New_York")
                      .dt.tz_localize(None).dt.normalize())
        for c in ("open", "high", "low", "close", "volume"):
            df[c] = df[c].astype("float64")
        return df[COLS].sort_values(["symbol", "date"]).reset_index(drop=True)
