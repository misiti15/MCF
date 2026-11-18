"""SPY 1-min bars 10-06..11-17 via Alpaca market-data GET (read-only). Educational only - not financial advice."""
import os, sys, json, urllib.request, urllib.parse, pandas as pd
H={'APCA-API-KEY-ID':os.environ['ALPACA_API_KEY'],'APCA-API-SECRET-KEY':os.environ['ALPACA_SECRET_KEY']}
rows=[];tok=None
while True:
    q={'timeframe':'1Min','start':'2026-10-06T13:30:00Z','end':'2026-11-17T21:00:00Z','limit':10000,'feed':'sip','adjustment':'split'}
    if tok:q['page_token']=tok
    r=urllib.request.Request('https://data.alpaca.markets/v2/stocks/SPY/bars?'+urllib.parse.urlencode(q),headers=H)
    j=json.load(urllib.request.urlopen(r));rows+=j.get('bars') or [];tok=j.get('next_page_token')
    if not tok:break
d=pd.DataFrame(rows);d['ts']=pd.to_datetime(d.t).dt.tz_convert('America/New_York');d[['ts','o','h','l','c','v']].to_pickle(sys.argv[1]);print(len(d))
