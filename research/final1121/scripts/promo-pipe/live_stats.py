import json, math, numpy as np, pandas as pd
P='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/promo-pipe'; I='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox'
t=pd.read_pickle(P+'/live.pkl')
asg=json.load(open(I+'/docs/live/assignments.json'))['accounts']
home={}
for a,ss in asg.items():
    for s in ss: home.setdefault(s,[]).append(a)
reps=json.load(open(I+'/docs/live/arena_reps.json'))['setups']
prim=t[t.account=='primary']
pday=prim.groupby('date').r.sum()
alld=sorted(t.date.unique())
pday=pday.reindex(alld,fill_value=0.0)
psd=set(zip(prim.symbol,prim.date))
def ct(x):
    if len(x)<3: return np.nan
    m=x.r.mean(); e=(x.r-m).groupby(x.date).sum(); se=math.sqrt((e**2).sum())/len(x)
    return m/se if se>0 else np.nan
def rec(x):
    d=x.groupby('date').r.sum(); n=len(x); tot=x.r.sum()
    o=dict(n=n,sess=d.size,tot=tot,avg=x.r.mean())
    srt=d.sort_values(ascending=False)
    b1=srt.index[:1]; b2=srt.index[:2]
    o['wo1']=x[~x.date.isin(b1)].r.mean() if d.size>1 else np.nan
    o['wo2']=x[~x.date.isin(b2)].r.mean() if d.size>2 else np.nan
    o['bshare']=srt.iloc[0]/tot if tot>0 else np.nan
    o['dayt']=ct(x)
    o['green']=(d>0).mean()
    o['shrunk']=n/(n+150)*o['avg']+150/(n+150)*(-0.10)
    return o
rows=[]
for s,x in t.groupby('strategy'):
    o=dict(setup=s,home='/'.join(home.get(s,['-'])),accts='/'.join(sorted(x.account.unique())))
    o.update(rec(x))
    no=x[[ (a,b) not in psd for a,b in zip(x.symbol,x.date)]] if 'primary' not in home.get(s,[]) else x[x.account!='primary']
    r2=rec(no) if len(no) else {}
    for k in ('n','avg','wo1','bshare','shrunk','sess'): o['no_'+k]=r2.get(k,np.nan)
    d=x.groupby('date').r.sum().reindex(alld,fill_value=0.0)
    first=x.date.min(); m=np.array(alld)>=first
    o['corrP']=np.corrcoef(d[m],pday[m])[0,1] if m.sum()>5 else np.nan
    red=(pday<0)&m
    o['R_on_Pred']=d[red].sum(); o['Pred_n']=int(red.sum()); o['green_on_Pred']=int((d[red]>0).sum())
    o['traded_on_Pred']=int((d[red]!=0).sum())
    o['active']=reps.get(s,{}).get('active_days',np.nan)
    o['last10']=x[x.date.isin(sorted(x.date.unique())[-10:])].r.sum()
    o['first']=first
    rows.append(o)
R=pd.DataFrame(rows)
R.to_pickle(P+'/live_stats.pkl')
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',200)
f=R[(R.sess>=15)&(R.avg>0)&(R.wo1>0)].sort_values('shrunk',ascending=False)
cols=['setup','home','n','sess','active','tot','avg','wo1','wo2','bshare','dayt','green','shrunk','no_n','no_avg','no_wo1','no_bshare','no_shrunk','corrP','R_on_Pred','Pred_n','green_on_Pred','last10']
print(f[cols].round(3).to_string(index=False))
names=['RW7-gapdn-bounce-early-short-FD','RW1-gapdn-bounce-flowsell-short-FD','BEG-ORB-orb15-inplay-stopOR','RW7-gapdn-bounce-early-short-FD-WB3','RW1-gapdn-bounce-flowsell-short-FD-WB3']
print(R[R.setup.isin(names)][cols].round(3).to_string(index=False))
print('primary days',len(alld), 'red',int((pday<0).sum()), 'Primary tot',pday.sum())
