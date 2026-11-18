"""W6 pre-registered tests X1-X7. Educational only - not financial advice. usage: tests.py trades.pkl spy1m.pkl"""
import sys, itertools, numpy as np, pandas as pd
t=pd.read_pickle(sys.argv[1]); spy=pd.read_pickle(sys.argv[2])
S=sorted(t.date.unique()); NS=len(S)
def tday(s):  # day-clustered t over all sessions (zeros on inactive days)
    s=s.reindex(S,fill_value=0.0); return s.mean()/s.std(ddof=1)*np.sqrt(len(s)) if s.std()>0 else 0
def wobd(r,dates):
    dd=r.groupby(dates).sum(); b=dd.idxmax() if len(dd) else None
    tot=dd.sum(); n=len(r); nb=n-(dates==b).sum()
    return (tot-dd.max())/nb if nb else np.nan, dd.max()/tot if tot>0 else np.nan
P=lambda *a:print(*a)
# ---------------- X1 PBO / CSCV
P('== X1 PBO (CSCV, S=8)')
cnt=t.groupby('strategy').size(); keep=cnt[cnt>=20].index
M=t[t.strategy.isin(keep)].pivot_table(index='date',columns='strategy',values='R',aggfunc='sum').reindex(S).fillna(0)
N=t[t.strategy.isin(keep)].pivot_table(index='date',columns='strategy',values='R',aggfunc='count').reindex(S).fillna(0)
blocks=np.array_split(np.arange(NS),8)
for metric in ('total','avg'):
    lam=[];oos_best=[];oos_med=[]
    for comb in itertools.combinations(range(8),4):
        ii=np.concatenate([blocks[k] for k in comb]); oo=np.setdiff1d(np.arange(NS),ii)
        if metric=='total': isv=M.iloc[ii].sum(); oov=M.iloc[oo].sum()
        else:
            ni=N.iloc[ii].sum(); no=N.iloc[oo].sum()
            isv=(M.iloc[ii].sum()/ni).where(ni>=10); oov=(M.iloc[oo].sum()/no).where(no>=10)
            ok=isv.notna()&oov.notna(); isv=isv[ok]; oov=oov[ok]
        b=isv.idxmax(); w=oov.rank(pct=True)[b]; w=min(max(w,1e-3),1-1e-3)
        lam.append(np.log(w/(1-w))); oos_best.append(oov[b]); oos_med.append(oov.median())
    lam=np.array(lam)
    P(f'{metric}: setups={M.shape[1]} PBO={np.mean(lam<=0):.2f} median OOS pct-rank of IS-best={np.median(1/(1+np.exp(-lam))):.2f} mean OOS value IS-best={np.mean(oos_best):.3f} vs OOS median setup {np.mean(oos_med):.3f}')
    # top-10 basket instead of top-1
# also: IS top decile basket vs rest
lam=[]
for comb in itertools.combinations(range(8),4):
    ii=np.concatenate([blocks[k] for k in comb]); oo=np.setdiff1d(np.arange(NS),ii)
    isv=M.iloc[ii].sum(); oov=M.iloc[oo].sum(); top=isv.nlargest(max(1,len(isv)//10)).index
    lam.append(oov[top].mean()-oov.mean())
P(f'  (descriptive) IS top-decile basket OOS total R minus all-setup mean: mean {np.mean(lam):.2f}R, share>0 {np.mean(np.array(lam)>0):.2f}')
# ---------------- X2 try-count bar
P('== X2 try-count-scaled bar')
Nset=t.strategy.nunique(); bar=max(1.5,np.sqrt(2*np.log(Nset)))
rows=[]
for s,g in t.groupby('strategy'):
    if len(g)<30: continue
    dd=g.groupby('date').R.sum(); tt=tday(dd)
    a,sh=wobd(g.R,g.date)
    rows.append((s,len(g),g.date.nunique(),g.R.sum(),g.R.mean(),tt,a,sh,
                 g[g.half=='fit'].R.mean(),g[g.half=='check'].R.mean()))
X2=pd.DataFrame(rows,columns=['setup','n','days','totR','avgR','t_day','avg_wobd','bestshare','fit_avg','check_avg']).sort_values('t_day',ascending=False)
P(f'distinct setups={Nset} bar={bar:.2f}; setups>=30 trades={len(X2)}; t>=bar: {(X2.t_day>=bar).sum()}; t>=2: {(X2.t_day>=2).sum()}; t>=1.5: {(X2.t_day>=1.5).sum()}')
P(f'  null expectation: of {len(X2)} null setups ~{len(X2)*0.067:.1f} would show t>=1.5 by chance (one-sided)')
P(X2.head(12).round(3).to_string(index=False))
X2.round(4).to_csv('X2.csv',index=False)
# ---------------- X3 gap fade by liquidity / uncertainty
P('== X3 gap-fade cells')
f=t[t.gap.abs()>=0.02].copy(); f=f[np.sign(f.gap)==-f.side]
q=t.drop_duplicates(['symbol','date']).adv20.quantile([1/3,2/3]).values
f['liq']=pd.cut(f.adv20,[-1,q[0],q[1],1e18],labels=['low','mid','top'])
med=t[t.half=='fit'].drop_duplicates('date').rv10.median()
f['unc']=np.where(f.rv10>med,'highVol','lowVol')
P(f'gap-fade trades n={len(f)} ({len(f)/len(t):.1%} of all), avgR {f.R.mean():.3f}; ADV tercile cuts ${q[0]/1e6:.1f}M/${q[1]/1e6:.1f}M; rv10 median {med:.2e}')
P(f.pivot_table(index='liq',columns=['unc'],values='R',aggfunc=['mean','count'],observed=False).round(3).to_string())
P(f.pivot_table(index='liq',columns='half',values='R',aggfunc=['mean','count'],observed=False).round(3).to_string())
P(f.pivot_table(index='unc',columns='half',values='R',aggfunc=['mean','count'],observed=False).round(3).to_string())
def filt(name,mask):
    sk=t[mask]; d=-sk.groupby('date').R.sum()
    per=sk.groupby('strategy').R.agg(['sum','count'])
    imp=(per['sum']<0).sum(); wor=(per['sum']>0).sum()
    P(f'{name}: skipped {len(sk)} trades in {sk.strategy.nunique()} setups; R change {-sk.R.sum():+.1f} (fit {-sk[sk.half=="fit"].R.sum():+.1f}, check {-sk[sk.half=="check"].R.sum():+.1f}); day-t {tday(d):.2f}; setups improve {imp} / worsen {wor}; worst-hit setups: '+
      ', '.join(f'{i} {-v:+.1f}' for i,v in per['sum'].sort_values(ascending=False).head(4).items()))
    if len(sk): 
        a,sh=wobd(-sk.R,sk.date); P(f'   avg R change per skipped trade w/o best day {a:+.3f}, best-day share {sh if sh==sh else float("nan"):.2f}')
    return sk
filt('F3 skip gap-fade in top ADV tercile', t.index.isin(f[f.liq=='top'].index))
# ---------------- X4 short squeeze / tail
P('== X4 shorts')
s=t[t.side==-1].copy(); s['tl']=s.R<=-1.5
s['px']=pd.cut(s.pc,[0,5,10,20,1e9],labels=['<5','5-10','10-20','>20'])
s['run']=pd.cut(s.ret5,[-9,0.10,0.25,99],labels=['<10%','10-25%','>=25%'])
s['gup']=pd.cut(s.gap,[-9,0.03,0.10,99],labels=['<3%','3-10%','>=10%'])
P(f'shorts n={len(s)} avgR {s.R.mean():.3f}, tail rate {s.tl.mean():.3f}, tail R share {s[s.tl].R.sum()/s[s.R<0].R.sum():.2f} of short losses')
for col in ('px','run','gup'):
    P(s.groupby(col,observed=False).agg(n=('R','size'),avgR=('R','mean'),tail=('tl','mean'),fitR=('R',lambda x:x[s.loc[x.index,'half']=='fit'].mean()),chkR=('R',lambda x:x[s.loc[x.index,'half']=='check'].mean())).round(3).to_string())
filt('F4 skip shorts with prior-5-session return >= +25%', (t.side==-1)&(t.ret5>=0.25))
L3=t[(t.strategy=='L3-gap-slope-fromopen-FD')&(t.side==-1)&(t.ret5>=0.25)]
P(f'   protected L3-gap-slope-fromopen-FD trades hit by F4: {len(L3)}, R {L3.R.sum():+.1f}')
# ---------------- X5 market intraday momentum
P('== X5 SPY first-half-hour sign vs late trades')
spy['date']=spy.ts.dt.strftime('%Y-%m-%d'); spy['hm']=spy.ts.dt.hour*100+spy.ts.dt.minute
p10=spy[spy.hm<=959].groupby('date').c.last()

import pandas as _p
pcs=t[t.symbol=='SPY'].groupby('date').pc.first() if (t.symbol=='SPY').any() else None
daily=_p.read_parquet(sys.argv[3]) if len(sys.argv)>3 else None
spyd=daily[daily.symbol=='SPY'].copy(); spyd['date']=spyd.ts.dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d'); spyd['pc']=spyd.close.shift(1)
r30=(p10/spyd.set_index('date').pc.reindex(p10.index)-1)
late=t[t.hhmm>=1500].copy(); late['r30']=late.date.map(r30); late['al']=np.sign(late.r30)==late.side
P(f'late trades n={len(late)}, aligned {late.al.sum()} avgR {late[late.al].R.mean():.3f}, against {(~late.al).sum()} avgR {late[~late.al].R.mean():.3f}')
P(late.pivot_table(index='al',columns='half',values='R',aggfunc=['mean','count']).round(3).to_string())
allt=t.copy(); allt['r30']=allt.date.map(r30); allt['al']=np.sign(allt.r30)==allt.side; allt['win']=pd.cut(allt.hhmm,[0,1000,1130,1400,1500,1600],labels=['<10','10-11:30','11:30-14','14-15','>=15'])
P('  (descriptive, all entry windows) aligned-minus-against avgR:'); P(allt.pivot_table(index='win',columns='al',values='R',aggfunc='mean',observed=False).round(3).to_string())
filt('F5 after 15:00 take only SPY-aligned trades', t.index.isin(late[~late.al].index))
# ---------------- X6 vol-managed weights
P('== X6 vol-managed daily weights')
def vm(series_by_date, L):
    rv=t.drop_duplicates('date').set_index('date')[f'rv{L}'].reindex(S)
    w=1/rv; w=w/w[[d<='2026-10-27' for d in S]].mean(); w=w.clip(upper=2)
    x=series_by_date.reindex(S,fill_value=0); y=x*w
    out={}
    for h,m in (('fit',[d<='2026-10-27' for d in S]),('check',[d>'2026-10-27' for d in S])):
        out[h]=(x[m].sum(),x[m].mean()/x[m].std(),y[m].sum(),y[m].mean()/y[m].std(),x[m].min(),y[m].min(),w[m].mean())
    return out
books={'Primary journal':t[t.acct=='primary'].groupby('date').R.sum(),'All accounts pooled (per-trade R)':t.groupby('date').R.sum()}
cur=t[(t.acct=='primary')&(t.date>='2026-11-04')].strategy.value_counts(); six=cur[cur>=3].index.tolist()
books['Current Primary setups pooled across accounts']=t[t.strategy.isin(six)].groupby('date').R.sum()
P('current Primary setups (>=3 Primary trades since 11-04):',six)
for nm,b in books.items():
    for L in (10,5,20):
        o=vm(b,L); P(f'{nm} L={L}: '+'; '.join(f'{h}: R {v[0]:+.1f}->{v[2]:+.1f}, daySharpe {v[1]:.3f}->{v[3]:.3f}, worst {v[4]:+.1f}->{v[5]:+.1f}, mean w {v[6]:.2f}' for h,v in o.items()))
# per setup improve/worsen of daily Sharpe (L=10) for setups with >=30 trades
rv=t.drop_duplicates('date').set_index('date')['rv10'].reindex(S); w=1/rv; w=(w/w[[d<='2026-10-27' for d in S]].mean()).clip(upper=2)
imp=wor=0; dl=[]
for st,g in t.groupby('strategy'):
    if len(g)<30: continue
    x=g.groupby('date').R.sum().reindex(S,fill_value=0); y=x*w; d=y.sum()-x.sum(); dl.append(d); imp+=d>0; wor+=d<0
P(f'  per setup (>=30 trades) total R change under L=10 weights: improve {imp}, worsen {wor}, median {np.median(dl):+.2f}R, sum {np.sum(dl):+.1f}R')
P('  weights by date:', ' '.join(f'{d[5:]}:{w[d]:.2f}' for d in S))
# ---------------- X7 breadth
P('== X7 implied breadth')
B=t[t.strategy.isin(six)].pivot_table(index='date',columns='strategy',values='R',aggfunc='sum').reindex(S).fillna(0)
C=B.corr().values; n=len(six); rho=(C.sum()-n)/(n*(n-1))
P(f'current Primary setups n={n}, avg pairwise corr of daily R {rho:.3f}, implied breadth {n/(1+(n-1)*rho):.2f}')
P(pd.DataFrame(C,index=six,columns=six).round(2).to_string())
