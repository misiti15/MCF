"""Fetch Alpaca SIP daily opens (GET only) for every symbol traded live; keys from env, never printed."""
import os, sys, json, glob, sqlite3, urllib.request, urllib.parse
import pandas as pd
jdir, out = sys.argv[1], sys.argv[2]
syms = set()
for f in glob.glob(os.path.join(jdir, '*.db')):
    c = sqlite3.connect(f)
    syms |= {r[0] for r in c.execute("select distinct symbol from trades where run_id in (1,2)")}
syms = sorted(s for s in syms if s)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
rows = []
for i in range(0, len(syms), 100):
    tok = None
    while True:
        q = {"symbols": ",".join(syms[i:i+100]), "timeframe": "1Day", "start": "2026-10-06", "end": "2026-11-17",
             "feed": "sip", "adjustment": "raw", "limit": 10000}
        if tok: q["page_token"] = tok
        req = urllib.request.Request("https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q), headers=H)
        d = json.load(urllib.request.urlopen(req, timeout=60))
        for s, bs in (d.get("bars") or {}).items():
            for b in bs:
                rows.append((s, b["t"][:10], b["o"], b["h"], b["l"], b["c"]))
        tok = d.get("next_page_token")
        if not tok: break
pd.DataFrame(rows, columns=["symbol", "date", "open", "high", "low", "close"]).to_csv(out, index=False)
print(len(syms), "symbols", len(rows), "daily bars")
