import os,sys,sqlite3,requests,pandas as pd,time
H={'APCA-API-KEY-ID':os.environ['ALPACA_API_KEY'],'APCA-API-SECRET-KEY':os.environ['ALPACA_SECRET_KEY']}
U='https://data.alpaca.markets/v2/stocks/bars'
def get(syms,tf,start,end):
    out=[];tok=None
    while True:
        p={'symbols':','.join(syms),'timeframe':tf,'start':start,'end':end,'limit':10000,'adjustment':'split','feed':'sip'}
        if tok:p['page_token']=tok
        r=requests.get(U,headers=H,params=p,timeout=60);r.raise_for_status();j=r.json()
        for s,b in (j.get('bars') or {}).items():
            for x in b: x['S']=s;out.append(x)
        tok=j.get('next_page_token')
        if not tok:break
    return pd.DataFrame(out)
c=sqlite3.connect('p.db')
syms=sorted(set(r[0] for r in c.execute("select distinct symbol from trades where run_id=1 and date>='2026-10-06'")))
m=get(['SPY','QQQ','IWM'],'5Min','2026-10-06T13:30:00Z','2026-11-18T21:00:00Z'); m.to_parquet('mkt/idx5.parquet'); print('idx',len(m))
ds=[]
for i in range(0,len(syms),100):
    ds.append(get(syms[i:i+100]+['SPY'],'1Day','2026-06-20','2026-11-18'))
d=pd.concat(ds).drop_duplicates(['S','t']); d.to_parquet('mkt/daily.parquet'); print('daily',len(d),d.S.nunique())
