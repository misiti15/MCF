import pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from caplib import *
M=pd.read_parquet('lab_mat.parquet').sort_values(['strategy','date']).reset_index(drop=True)
M['wk']=pd.to_datetime(M.date).dt.strftime('%G-%V')
mu=(M.Rnone.groupby(M.strategy).sum()/M.nnone.groupby(M.strategy).sum())
print('lab avg R/lot (book, no latch):',mu.round(3).to_dict())
short=lambda s:s[:30]
def R(r,L,neu=False):
    v= r['Rnone'] if L is None else r[f'R{L}']; n= r['nnone'] if L is None else r[f'n{L}']
    return v-n*mu[r['strategy']] if neu else v
pd.set_option('display.width',250)
print('=== descriptive by period: P(final>L | touch L) and gain (raw / neutral) ===')
for per in ['FIT','CHECK','T2']:
    X=M[M.per==per]
    for s,g in X.groupby('strategy'):
        d=[]
        for L in [-1.0,-1.5,-2.0,-2.5,-3.0,-4.0]:
            tc=g.pmin<=L; gr=(g[f'R{L}']-g.Rnone).sum(); dn=(g[f'n{L}']-g.nnone).sum(); gn=gr-dn*mu[s]
            d.append(f'{L}:T{int(tc.sum())} P{(g.final[tc]>L).mean():.2f} g{gr:+.0f}/n{gn:+.0f}')
        print(per,short(s),len(g),' | '.join(d))
def run(cal_sel, test_sel, label):
    rows=[];lv=[]
    for s,g in M.groupby('strategy'):
        for key,(C,Tst) in cal_sel(g):
            if len(C)<1 or len(Tst)<1: continue
            G={L:(C[f'R{L}']-C.Rnone).sum() for L in GRID}; T={L:int((C.pmin<=L).sum()) for L in GRID}
            p1,p3=calib(G,T); p2=clamp(p1); lv.append(dict(setup=short(s),key=key,P1=p1,P3=p3))
            for _,r in Tst.iterrows():
                d=dict(strategy=s,date=r.date,per=r.per)
                for nm,L in [('none',None),('u2',-2.0),('P1',p1),('P2',p2),('P3',p3)]:
                    d[nm]=R(r,L); d[nm+'_n']=R(r,L,True)
                rows.append(d)
    W=pd.DataFrame(rows); out=[]
    for per in sorted(W.per.unique())+['ALL']:
        X=W if per=='ALL' else W[W.per==per]
        for p in ['none','u2','P1','P2','P3']:
            dd=X.groupby('date')[p].sum(); dn=X.groupby('date')[p+'_n'].sum()
            out.append(dict(test=per,pol=p,R=round(dd.sum(),1),R_neutral=round(dn.sum(),1),worst=round(dd.min(),1),
              t_vs_none=round(clustered_t(dd-X.groupby('date')['none'].sum()),2),t_vs_u2=round(clustered_t(dd-X.groupby('date')['u2'].sum()),2),
              tN_vs_u2=round(clustered_t(dn-X.groupby('date')['u2_n'].sum()),2)))
    print(f'\n=== {label} ==='); print(pd.DataFrame(out).to_string(index=False))
    P=W.groupby('strategy')[['none','u2','P1','P2','P3','none_n','u2_n','P1_n','P2_n']].sum(); P.index=[short(s) for s in P.index]
    for p in ['P1','P2','P3']:
        for b in ['none','u2']:
            dl=P[p]-P[b]; print(f'{p} vs {b}: improve {int((dl>0.05).sum())} (+{dl[dl>0.05].sum():.1f}) worse {int((dl<-0.05).sum())} ({dl[dl<-0.05].sum():.1f})')
    print(P.round(1).to_string())
    return pd.DataFrame(lv)
# A: static FIT -> CHECK, T2
def stat(g):
    C=g[g.per=='FIT']; yield 'FIT',(C,g[g.per!='FIT'])
lvA=run(stat,None,'Lab A static: calibrate FIT, test CHECK and T2')
print('FIT levels:',lvA[['setup','P1','P3']].to_string(index=False))
# B: rolling weekly trailing 60 active days, min 20, chronological
def roll(g):
    for w in sorted(g.wk.unique()):
        C=g[g.wk<w].tail(60); Tst=g[g.wk==w]
        if len(C)>=20: yield w,(C,Tst)
lvB=run(roll,None,'Lab B rolling weekly (trailing 60 active days, min 20)')
lvB['q']=lvB.key.str[:4]
print('\nP1 level by setup per year (share of weeks at each level):')
for s,g in lvB.groupby('setup'):
    print(s, {y:gg.P1.fillna(0).value_counts(normalize=True).round(2).to_dict() for y,gg in g.groupby('q')})
print('weeks where P1 changed vs previous week, share:',round(lvB.groupby('setup').P1.apply(lambda v:(v.fillna(0).diff()!=0).iloc[1:].mean()).mean(),2))
