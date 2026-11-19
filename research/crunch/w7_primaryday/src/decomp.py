import pandas as pd,numpy as np
t=pd.read_pickle('t.pkl'); day=pd.read_pickle('day.pkl')
g=t.groupby('date')
D=pd.DataFrame({'n':g.size(),'R':g.R.sum(),'Rlong':t[t.side==1].groupby('date').R.sum(),'Rshort':t[t.side==-1].groupby('date').R.sum(),
 'nshort':t[t.side==-1].groupby('date').size()}).fillna(0)
D=D.join(day)
# time buckets
b=pd.cut(t.hm,[0,600,660,720,840,960],labels=['0930-1000','1000-1100','1100-1200','1200-1400','1400-1600'])
D=D.join(t.groupby(['date',b],observed=False).R.sum().unstack().add_prefix('t'))
# clusters: entries per 5-min bar across setups
cs=t.groupby(['date','bar']).size().rename('cs'); t=t.join(cs,on=['date','bar'])
t['clu']=np.where(t.cs>=5,'c5+',np.where(t.cs>=3,'c3-4','c1-2'))
D=D.join(t.groupby(['date','clu']).R.sum().unstack().fillna(0))
# stacking: other open lots same symbol at entry
def openlots(r,df):
    o=df[(df.entry_time<r.entry_time)&(df.exit_time>r.entry_time)]
    return pd.Series({'stack':(o.symbol==r.symbol).sum(),'stack_same_setup':((o.symbol==r.symbol)&(o.strategy==r.strategy)).sum(),'open_same_side':(o.side==r.side).sum(),'open_all':len(o)})
parts=[]
for d,df in t.groupby('date'):
    parts.append(df.apply(lambda r:openlots(r,df),axis=1))
t=t.join(pd.concat(parts))
# prior realized loss on symbol same day (closed before entry)
def prior_loss(r,df):
    p=df[(df.symbol==r.symbol)&(df.exit_time<=r.entry_time)]
    return pd.Series({'sym_prior_loss':(p.R<0).sum(),'sym_prior_n':len(p),'sym_prior_stop':(p.exit_reason=='stop').sum()})
parts=[]
for d,df in t.groupby('date'): parts.append(df.apply(lambda r:prior_loss(r,df),axis=1))
t=t.join(pd.concat(parts))
# peak realized and giveback
pk=[]
for d,df in t.groupby('date'):
    cum=df.sort_values('exit_time').R.cumsum(); pk.append((d,cum.max(),cum.min(),cum.iloc[-1]))
D=D.join(pd.DataFrame(pk,columns=['date','peak','trough','end']).set_index('date'))
D['green']=D.R>0
t.to_pickle('t2.pkl')
pd.set_option('display.width',250)
print(D.round(1).drop(columns=['end']).to_string())
print('\n=== green vs red day means')
print(D.groupby('green').mean(numeric_only=True).round(2).T.to_string())
print('\n=== trade-level splits (avg R, n, sum) by category; red days vs green days')
t['gd']=t.date.map(D.green)
for col in ['clu','side','stack','sym_prior_loss','exit_reason']:
    x=t.assign(k=t[col].clip(upper=3) if t[col].dtype!=object else t[col]).groupby(['k','gd']).R.agg(['size','mean','sum']).round(3)
    print(col); print(x.unstack().to_string())
t['ob']=pd.cut(t.open_same_side,[-1,2,5,10,20,100])
print(t.groupby('ob',observed=True).R.agg(['size','mean','sum']).round(3))
t['sq']=pd.cut(t.spy_move,[-9,-0.3,-0.1,0.1,0.3,9])
print('spy move with trade (entry->exit)');print(t.groupby(['side','sq'],observed=True).R.agg(['size','mean','sum']).round(3).to_string())
