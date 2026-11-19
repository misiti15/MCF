import sqlite3,glob,os,collections,pandas as pd,numpy as np
R='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/rootcause_1119'
beta=pd.read_csv(f'{R}/cond_work/beta.csv',index_col=0).iloc[:,0]
import sys; TH=float(sys.argv[1]); NEG=set(beta[beta<=TH].index)
LOCK=('2024-11-01','2025-02-28')
rows=[]
for f in sorted(glob.glob(f'{R}/stk/*.db')):
    a=os.path.basename(f)[:-3]; c=sqlite3.connect(f)
    t=pd.read_sql("select strategy,symbol,side,date,entry,stop,shares,pnl_adj from trades where run_id=1 and pnl_adj is not null and shares>0 and entry!=stop",c)
    t=t[~t.date.between(*LOCK)]; t['acct']=a; rows.append(t)
T=pd.concat(rows); T['R']=T.pnl_adj/((T.entry-T.stop).abs()*T.shares)
T['flag']=(T.side==-1)&T.symbol.isin(NEG)
print('neg-beta symbols',len(NEG)); print('trades',len(T),'flagged',T.flag.sum(),'R',round(T[T.flag].R.sum(),1),'avg',round(T[T.flag].R.mean(),3),'WR',round((T[T.flag].R>0).mean(),2))
for lab,X in [('all',T),('excl 11-19',T[T.date!='2026-11-19'])]:
    g=X.groupby(['acct','strategy']).apply(lambda d: pd.Series(dict(n=d.flag.sum(),base=d.R.sum(),new=d.R[~d.flag].sum())))
    g=g[g.n>0]; g['d']=g.new-g.base
    imp=g[g.d>0.005]; wor=g[g.d<-0.005]
    print(f'== {lab}: setup-accounts affected {len(g)} | improve {len(imp)} ({imp.d.sum():+.1f}R) | worse {len(wor)} ({wor.d.sum():+.1f}R) | net {g.d.sum():+.1f}R | trades {int(g.n.sum())}')
    if lab=='all': print(g.sort_values('d').round(2).to_string())
f=T[T.flag]; print('by date', f.groupby('date').R.agg(['count','sum']).round(1).T.to_string())
print('by symbol', f.groupby('symbol').R.agg(['count','sum']).round(1).sort_values('sum').T.to_string())
# Primary only
p=T[T.acct=='primary']; print('Primary flagged:',p.flag.sum(),round(p[p.flag].R.sum(),2))
# mirror check: long setups buying neg-beta
m=T[(T.side==1)&T.symbol.isin(NEG)]; print('longs on neg-beta (info):',len(m),round(m.R.sum(),1),round(m.R.mean(),3))
# 2y lab, L3 fires
L=pd.read_parquet(f'{R}/sl_work/lab_fires.parquet'); L=L[~L.date.astype(str).between(*LOCK)]
for s,g in L.groupby('setup'):
    k=g.symbol.isin(NEG)
    print(f'lab {s}: n={len(g)} avg={g.r.mean():+.3f} | neg-beta n={k.sum()} avg={g.r[k].mean():+.3f} sum={g.r[k].sum():+.1f} | rest avg={g.r[~k].mean():+.3f}  first-only neg avg={g.r[k&g['first']].mean():+.3f} n={(k&g["first"]).sum()}')
    dd=g[k].groupby('date').r.sum().sort_values()
    if len(dd): print('   neg-beta lab days',len(dd),'w/o best day avg', round((g.r[k].sum()-dd.iloc[-1])/max(1,k.sum()-g[k][g[k].date==dd.index[-1]].shape[0]),3),'best day share',round(dd.iloc[-1]/g.r[k].sum(),2) if g.r[k].sum()>0 else 'n/a(neg total)')
