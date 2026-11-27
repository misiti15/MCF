"""GET-only Alpaca market-data fetch of 15-min SIP bars (raw) 2016-2022 for an EARLY breadth sample. Keys never printed."""
import os, sys, time, random, requests, pandas as pd
from pathlib import Path
URL="https://data.alpaca.markets/v2/stocks/bars"
OUT=Path(sys.argv[1])
syms=sorted(p.stem for p in Path('/home/user/MCF/data/cache_fresh/1Min').glob('*.parquet'))
syms=[x for x in syms if x not in ('SPY','QQQ','TQQQ','SPXL','SQQQ','SPXS','UPRO','SH','PSQ')]
random.Random(1127).shuffle(syms); syms=sorted(syms[:130])
s=requests.Session(); s.headers.update({"APCA-API-KEY-ID":os.environ["ALPACA_API_KEY"],"APCA-API-SECRET-KEY":os.environ["ALPACA_SECRET_KEY"]})
for i in range(0,len(syms),10):
    b=[x for x in syms[i:i+10] if not (OUT/f"{x}.parquet").exists()]
    if not b: continue
    params={"symbols":",".join(b),"timeframe":"15Min","start":"2016-01-01","end":"2022-12-31","feed":"sip","adjustment":"raw","limit":10000}
    rows={x:[] for x in b}
    while True:
        for a in range(8):
            r=s.get(URL,params=params,timeout=60)
            if r.status_code==429 or r.status_code>=500: time.sleep(2**a); continue
            r.raise_for_status(); break
        j=r.json()
        for k,v in (j.get("bars") or {}).items(): rows[k]+=v
        tok=j.get("next_page_token")
        if not tok: break
        params["page_token"]=tok
    for k,v in rows.items():
        if not v: pd.DataFrame().to_parquet(OUT/f"{k}.parquet"); continue
        df=pd.DataFrame(v); df.index=pd.DatetimeIndex(pd.to_datetime(df.t,utc=True)).tz_convert("America/New_York")
        df=df.rename(columns=dict(o="open",h="high",l="low",c="close",v="volume"))[["open","high","low","close","volume"]]
        df=df.between_time("09:30","15:59"); df.to_parquet(OUT/f"{k}.parquet")
    print(i,b[0],len(rows[b[0]]),flush=True)
print("done")
