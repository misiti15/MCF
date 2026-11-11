"""REPS1 step 2: Alpaca 5-min SIP bars (split-adjusted) for every signal symbol, sessions 10-20..11-10. GET only; keys from env.
    python -I fetch.py <signals.csv.gz> <out m5.csv.gz> [start index]     Educational only - not financial advice."""
import os, sys, time, json, gzip, urllib.request, urllib.parse, pandas as pd
syms = sorted(pd.read_csv(sys.argv[1], usecols=["symbol"]).symbol.dropna().unique())
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def get(q):
    req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
    for a in range(6):
        try: return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception: time.sleep(2 ** (a + 1))
    raise RuntimeError("fetch failed")
with gzip.open(sys.argv[2], "wt") as f:
    f.write("symbol,t,o,h,l,c,v\n"); n = 0
    for i in range(int(sys.argv[3]) if len(sys.argv) > 3 else 0, len(syms), 100):
        tok = None
        while True:
            q = {"symbols": ",".join(syms[i:i + 100]), "timeframe": "5Min", "start": "2026-10-20T13:30:00Z", "end": "2026-11-10T21:00:00Z",
                 "limit": 10000, "feed": "sip", "adjustment": "split"}
            if tok: q["page_token"] = tok
            j = get(q)
            for s, bs in (j.get("bars") or {}).items():
                for b in bs:
                    f.write(f"{s},{b['t']},{b['o']},{b['h']},{b['l']},{b['c']},{b['v']}\n"); n += 1
            tok = j.get("next_page_token")
            if not tok: break
        print(i, n, flush=True)
print("done", n)
