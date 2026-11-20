import sys, glob, numpy as np, pandas as pd
REPO='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/st7w'
sys.path.insert(0,REPO)
from mcf.research import gates as G
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
x=pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(W+'/scan/20*.parquet')) if '_all' not in f],ignore_index=True)
x['date']=x.date.astype(str); x['half']=np.where(x.date<'2026-03-10','early','late')
ST7='ST7-rsi50dn-long-pm-t1s1-FD'
def st(d):
    if not len(d): return dict(n=0)
    s=G.summary(d.assign(date=d.date)); g=d.groupby('date').r.sum()
    return dict(n=s['n'],days=s['days'],win=s['win_rate'],avgR=s['exp_r'],t=s['t'],totR=round(d.r.sum(),1),
        woBest=s['ex_best_day'],bestShare=round(g.max()/d.r.sum(),2) if d.r.sum()>0 else None,worstDay=round(g.min(),1),
        early=round(d[d.half=='early'].r.mean(),3),late=round(d[d.half=='late'].r.mean(),3),n1045=int((d.tod==1045).sum()))
print('== ST7-FD configs (2-year lab, first fire per symbol-day, prod costs)')
print(pd.DataFrame({v:st(x[(x.setup==ST7)&(x['var']==v)]) for v in ['base','SR','GA','BWIN','CSKIP']}).T.to_string())
# family
rows=[]
for n,d in x[x['var'].isin(['base','SR','GA'])].groupby('setup'):
    b=d[d['var']=='base']; kb=set(zip(b.date,b.symbol,b.tod))
    for v in ('SR','GA'):
        e=d[d['var']==v]; ke=set(zip(e.date,e.symbol,e.tod))
        if kb==ke: continue
        r=dict(setup=n,var=v,side=b.side.iloc[0] if len(b) else e.side.iloc[0],n_b=len(b),n_v=len(e),R_b=b.r.sum(),R_v=e.r.sum(),
               avg_b=b.r.mean(),avg_v=e.r.mean(),changed=len(kb^ke))
        for h in ('early','late'): r['d_'+h]=e[e.half==h].r.sum()-b[b.half==h].r.sum()
        rows.append(r)
F=pd.DataFrame(rows); F['delta']=F.R_v-F.R_b
F.to_csv(W+'/family_delta.csv',index=False)
print('candidate setups scanned',x.setup.nunique())
for v in ('SR','GA'):
    f=F[F['var']==v]
    print(f'\n== A-{v}: affected {len(f)}; better {(f.delta>0).sum()} (+{f.delta[f.delta>0].sum():.1f}R), worse {(f.delta<0).sum()} ({f.delta[f.delta<0].sum():.1f}R), net {f.delta.sum():.1f}R; not worse share {(f.delta>=0).mean():.2f}')
    for h in ('early','late'): print(f'   {h}: better {(f["d_"+h]>0).sum()} worse {(f["d_"+h]<0).sum()} net {f["d_"+h].sum():.1f}')
    print('   by side:',f.groupby('side').delta.agg(['size',lambda s:(s>0).sum(),lambda s:(s<0).sum(),'sum']).round(1).to_dict('index'))
    print(f.sort_values('delta')[['setup','side','n_b','n_v','avg_b','avg_v','delta','d_early','d_late']].round(3).to_string(index=False))
