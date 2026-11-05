"""REGX: SIP 1-minute RTH bars for 2026-11-05 (the 2-year cache ends 11-04) for the lab universe + index / sector ETFs.
Alpaca market-data GET only; keys from the environment, never printed. Writes <scratch>/bars1105.parquet (not the cache).
Usage: python fetch1105.py <scratch>. Educational only - not financial advice."""
import os, sys, time
from pathlib import Path
import pandas as pd, requests

M = Path("/home/user/MCF")
URL = "https://data.alpaca.markets/v2/stocks/bars"
S = Path(sys.argv[1])
syms = sorted(set(M.joinpath("research/lab_symbols.txt").read_text().split()) |
              {"SPY", "QQQ", "IWM", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"})
sess = requests.Session()
sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
rows = []
for k in range(0, len(syms), 100):
    p = {"symbols": ",".join(syms[k:k + 100]), "timeframe": "1Min", "start": "2026-11-05T14:30:00Z",
         "end": "2026-11-05T21:00:00Z", "feed": "sip", "adjustment": "split", "limit": 10000}
    while True:
        for a in range(8):
            r = sess.get(URL, params=p, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 ** a); continue
            r.raise_for_status(); break
        j = r.json()
        for s, bs in (j.get("bars") or {}).items():
            rows += [(s, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bs]
        if not j.get("next_page_token"):
            break
        p["page_token"] = j["next_page_token"]
    print(k, len(rows), flush=True)
d = pd.DataFrame(rows, columns=["symbol", "t", "open", "high", "low", "close", "volume"])
d["t"] = pd.to_datetime(d.t, utc=True).dt.tz_convert("America/New_York")
d = d[(d.t.dt.hour * 60 + d.t.dt.minute >= 570) & (d.t.dt.hour * 60 + d.t.dt.minute < 960)]
d.to_parquet(S / "bars1105.parquet")
print(d.symbol.nunique(), "symbols", len(d), "bars")
