# LIVE-READY 2026-11-11 (research only). Reads journal.db copies of every data branch from a scratch folder (S).
import sqlite3, json, subprocess, io
import pandas as pd, numpy as np
S='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad'
ACC={'mcf-data':'primary','mcf-data-testing':'testing','mcf-data-testing2':'testing2','mcf-data-gen':'gen',
     'mcf-data-graveyard':'graveyard','mcf-data-livelab':'livelab','mcf-data-explore1':'explore1'}
def load():
    out=[]
    for b,a in ACC.items():
        db=sqlite3.connect(f'{S}/j/{b}.db')
        t=pd.read_sql("select t.*, r.kind from trades t join runs r on r.id=t.run_id where r.kind='paper' and t.exit_time is not null and t.exit_time!='None'",db)
        o=pd.read_sql("select broker_order_id, qty as order_qty, entry_ref, stop as order_stop from orders",db)
        t=t.merge(o,on='broker_order_id',how='left')
        t['acct']=a; out.append(t)
    t=pd.concat(out,ignore_index=True)
    u=pd.read_csv(io.StringIO(subprocess.run(['git','-C','/home/user/MCF','show','origin/mcf-data:universe.csv'],capture_output=True,text=True).stdout))
    t=t.merge(u[['symbol','adv','atr','atr_pct','tier']],on='symbol',how='left')
    m=t.meta.fillna('').str.split(';').str[0]
    def js(x):
        try: return json.loads(x)
        except Exception: return {}
    mm=m.map(js)
    t['spread_bps']=mm.map(lambda d:d.get('spread_bps'))
    t['bid']=mm.map(lambda d:d.get('bid')); t['ask']=mm.map(lambda d:d.get('ask'))
    t['risk_ps']=(t.entry-t.stop).abs()
    t['R_raw']=t.r_multiple
    t['R_cur']=np.where(t.risk_ps*t.shares>0, t.pnl_adj.fillna(t.pnl)/(t.risk_ps*t.shares), t.r_multiple)
    t['touch']=t.meta.fillna('').str.contains('touch_fill')
    return t
