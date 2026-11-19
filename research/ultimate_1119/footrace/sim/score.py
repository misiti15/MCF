"""FOOTRACE1 scoring sim. Educational only - not financial advice."""
import json, pandas as pd, numpy as np
d=pd.read_parquet('ev1119/w/trades.parquet')
R=json.load(open('fr/roster.json')); reps=json.load(open('ult/docs/live/arena_reps.json'))['setups']
ARENA=['testing2','explore1','livelab','testingd','testinge','testingf','gen']
arena={x['setup']:a for a in ARENA for x in R[a] if x['enabled']}
K=30  # shrink: pseudo-trades at 0R
def stats(g):
    day=g.groupby('date').r_multiple.sum(); n=len(g); tot=g.r_multiple.sum()
    best=day.idxmax() if len(day) else None
    wo=g[g.date!=best].r_multiple
    return dict(n=n,days=int(day.size),tot=tot,avg=tot/n if n else np.nan,wo_avg=wo.mean() if len(wo) else np.nan,
                wo_tot=wo.sum(),best_share=(day.max()/tot if tot>0 else np.nan),shr=tot/(n+K),shr_wo=wo.sum()/(len(wo)+K))
def table(dd, setups):
    rows=[]
    for s in setups:
        g=dd[dd.strategy==s]; st=stats(g) if len(g) else dict(n=0,days=0,tot=0,avg=np.nan,wo_avg=np.nan,wo_tot=0,best_share=np.nan,shr=0,shr_wo=0)
        st['setup']=s; rows.append(st)
    t=pd.DataFrame(rows).set_index('setup')
    # leader score: mean of rank(total R w/o best day) and rank(shrunk avg R w/o best day); ties fine
    t['score']=(t.wo_tot.rank(ascending=False)+t.shr_wo.rank(ascending=False))/2
    return t
if __name__=='__main__':
    t=table(d,list(arena))
    t['acct']=pd.Series(arena); t['active']=pd.Series({s:reps.get(s,{}).get('active_days',0) for s in arena})
    t['sig_per_day']=pd.Series({s:(reps.get(s,{}).get('signals',0)/max(1,reps.get(s,{}).get('active_days',0))) for s in arena})
    t=t.sort_values('score')
    elig=(t.wo_tot>0)&(t.n>=10)
    t['leader']=False; t.loc[t[elig].index[:35],'leader']=True
    t['lag']=(t.active>=15)&(t.n>=30)&(t.avg<=0)&(t.wo_avg<=0)&(t.sig_per_day>=0.5)
    t['exit100']=(t.active>=15)&(t.n>=100)&(t.avg<=-0.05)&(t.wo_avg<=0)
    t.round(3).to_csv('fr/arena_table.csv')
    print(len(t),'arena setups; eligible for leader',int(elig.sum()),'leaders',int(t.leader.sum()))
    print('verdict-ready (>=15 active & >=30 tr):',int(((t.active>=15)&(t.n>=30)).sum()))
    print('FOOTRACE laggards',int(t.lag.sum()),' EXIT100',int(t.exit100.sum()))
    pd.set_option('display.width',250)
    c=['acct','n','days','active','tot','avg','wo_avg','best_share','score']
    print(t[t.leader][c].round(3).to_string())
    print(t[t.lag][c+['exit100']].round(3).to_string())
    print('below-min reps:',int(((t.active<15)|(t.n<30)).sum()))
    print(t.groupby('leader')[['n','tot']].sum())
    print(t.groupby('lag')[['n','tot']].sum())
