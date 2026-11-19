import os, sys, requests, pandas as pd
W = sys.argv[1]
syms='SPXS SQQQ VSXY NBIZ MSTZ SMST SPCQ DAMD UVIX UVXY VXX TSDD TSLQ TSLZ IREZ SPXU AAOZ BMNZ CORD RGTZ SOXS SSG AXTQ LITZ TECS IONZ ETHD SKDD HIBS MUZ RAMZ BEZ SMCZ BTCZ FNGD MUD QID SBIT SKHZ SNDQ NVDQ PLTZ PLTD TRI SPY QQQ'.split()
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
feed = os.environ.get("ALPACA_DATA_FEED", "sip")
rows=[];tok=None;n=0
while True:
    p = {"symbols": ",".join(syms), "timeframe": "1Min", "start": "2026-11-19T14:30:00Z", "end": "2026-11-19T21:00:00Z",
         "limit": 10000, "feed": feed, "adjustment": "raw"}
    if tok: p["page_token"] = tok
    r = requests.get("https://data.alpaca.markets/v2/stocks/bars", params=p, headers=H, timeout=60); n+=1
    r.raise_for_status(); j=r.json()
    for s,bars in (j.get("bars") or {}).items():
        for b in bars: rows.append((s,b["t"],b["o"],b["h"],b["l"],b["c"],b["v"]))
    tok=j.get("next_page_token")
    if not tok or n>=6: break
d=pd.DataFrame(rows,columns=["symbol","t","o","h","l","c","v"]);d.to_parquet(f"{W}/bars_today.parquet")
print("requests",n,"rows",len(d),d.t.max(),d.symbol.nunique())
