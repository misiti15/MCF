import pandas as pd, numpy as np, sys, json
sys.path.insert(0,'.')
from score import B, ETB, extra
fin=['S6-pdlrej-b0.3','R2a-midrec-f2','R2b-smallgap-f2.5','R2c-atrrec-k0.9','REF-L3']
F=pd.concat([pd.read_parquet('trades_fit.parquet'),pd.read_parquet('r2_trades_fit.parquet')]); F=F[F.cfg.isin(fin)&(F.grp=='real')]
C=pd.read_parquet('trades_check.parquet'); C=C[C.cfg.isin(fin)&(C.grp=='real')]
A=B.add_r(pd.concat([F,C])); A['h']=B.half(A.date); A=A[A.h!='none']
spy=B.spy_t1(); days=pd.Series(spy.index); days=days[days<='2026-11-04']; n=int((B.half(days)!='none').sum())
live=pd.read_pickle('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/live_trades.pkl')
pr=live[live.account=='primary'].groupby('date').r.sum(); pr.index=pr.index.astype(str)
out={}
for c,g in A.groupby('cfg'):
    b=B.book(g.drop(columns=['cfg']),B.TESTING_RULES,ETB)
    s=B.stats(b,n,spy); s.update(extra(b))
    d=b.groupby('date').r.sum()
    lv=pd.concat([d.rename('s'),pr.rename('p')],axis=1).loc[lambda x:x.p.notna()&(x.index<='2026-11-04')].fillna(0)
    s['live_window_days']=len(lv); s['live_corr_primary']=round(float(lv.s.corr(lv.p)),3)
    s['bt_sum_on_primary_red']=round(float(lv[lv.p<0].s.sum()),2); s['bt_sum_on_primary_green']=round(float(lv[lv.p>0].s.sum()),2)
    s['primary_red_days_helped']=int(((lv.p<0)&(lv.s>0)).sum()); s['primary_red_days']=int((lv.p<0).sum())
    out[c]={k:s.get(k) for k in ['trades','avg_r','avg_r_wo_best_day','avg_r_wo_top2','best_day','best_day_share','total_r_per_session','t_day_clustered','pct_days_green','worst_day','symbols','live_window_days','live_corr_primary','bt_sum_on_primary_red','bt_sum_on_primary_green','primary_red_days_helped','primary_red_days']}
json.dump(out,open('combined.json','w'),indent=1,default=float)
pd.set_option('display.width',250); print(n); print(pd.DataFrame(out).T.to_string())
