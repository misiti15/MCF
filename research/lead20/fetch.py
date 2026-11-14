"""LEAD20 data: Alpaca 5-min SIP bars (split-adjusted), two ranges around the locked block. GET only; keys from env.
    python -I fetch.py <out.csv.gz>        Educational only - not financial advice."""
import os, sys, time, json, gzip, urllib.request, urllib.parse
SY = "SPY QQQ SPXL TQQQ AAPL MSFT NVDA AMZN META GOOGL GOOG BRK.B AVGO LLY TSLA JPM UNH XOM V MA PG JNJ COST HD".split()
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
    for a in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception: time.sleep(2 ** (a + 1))
    raise RuntimeError("fetch failed")
with gzip.open(sys.argv[1], "wt") as f:
    f.write("symbol,t,o,h,l,c,v\n"); n = 0
    for a, b in (("2024-10-01T13:00:00Z", "2024-10-31T21:00:00Z"), ("2025-03-03T13:00:00Z", "2026-11-13T21:00:00Z")):
        for i in range(0, len(SY), 6):
            tok = None
            while True:
                q = {"symbols": ",".join(SY[i:i + 6]), "timeframe": "5Min", "start": a, "end": b, "limit": 10000, "feed": "sip", "adjustment": "split"}
                if tok: q["page_token"] = tok
                j = get(q)
                for s, bs in (j.get("bars") or {}).items():
                    for x in bs: f.write(f"{s},{x['t']},{x['o']},{x['h']},{x['l']},{x['c']},{x['v']}\n"); n += 1
                tok = j.get("next_page_token")
                if not tok: break
            print(a[:10], i, n, flush=True)
print("done", n)
