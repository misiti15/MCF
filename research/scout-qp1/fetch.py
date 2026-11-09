"""Fetch 5-min SIP RTH bars for QP1 (Alpaca market-data GET only; keys from env, never printed)."""
import os, sys, time, json, urllib.request, urllib.parse
import pandas as pd
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
SYMS = "SPY VXX XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
for s in SYMS:
    rows, tok = [], None
    while True:
        q = {"symbols": s, "timeframe": "5Min", "start": "2024-10-01T00:00:00Z", "end": "2026-11-07T00:00:00Z",
             "limit": 10000, "feed": "sip", "adjustment": "split"}
        if tok: q["page_token"] = tok
        req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
        for a in range(4):
            try:
                j = json.load(urllib.request.urlopen(req, timeout=60)); break
            except Exception as e:
                time.sleep(2 ** (a + 1))
        rows += j.get("bars", {}).get(s, []); tok = j.get("next_page_token")
        if not tok: break
    df = pd.DataFrame(rows); df["t"] = pd.to_datetime(df.t, utc=True).dt.tz_convert("America/New_York")
    m = df.t.dt.hour * 60 + df.t.dt.minute; df = df[(m >= 570) & (m < 960)]
    df.to_csv(f"{OUT}/{s}.csv", index=False); print(s, len(df), flush=True)
