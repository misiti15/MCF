import sys; sys.path.insert(0,'fr')
from score import *
def tclu(g):
    dm=g.groupby('date').r_multiple.mean()
    return dm.mean()/(dm.std(ddof=1)/np.sqrt(len(dm))) if len(dm)>2 and dm.std()>0 else 0.0
setups=list(arena); act_now={s:reps.get(s,{}).get('active_days',0) for s in arena}
spd=pd.Series({s:(reps.get(s,{}).get('signals',0)/max(1,act_now[s])) for s in arena})
sess=sorted(d.date.unique())
def flags(dd,after):
    t=table(dd,setups); t['active']=pd.Series({s:max(0,act_now[s]-after) for s in setups})
    t['t']=pd.Series({s:tclu(dd[dd.strategy==s]) for s in setups})
    base=(t.active>=15)&(t.n>=30)&(t.wo_avg<=0)&(spd[t.index]>=0.5)
    return t,{'A avg<=0':base&(t.avg<=0),'B avg<=0 & t<=-1.5':base&(t.avg<=0)&(t.t<=-1.5),'C avg<=-0.05 & t<=-2':base&(t.avg<=-0.05)&(t.t<=-2),
              'EXIT100':(t.active>=15)&(t.n>=100)&(t.avg<=-0.05)&(t.wo_avg<=0)}
t,F=flags(d,0)
t['spd']=spd; t['acct']=pd.Series(arena)
for k,m in F.items(): print('NOW',k,int(m.sum()))
t['flagB']=F['B avg<=0 & t<=-1.5']; t['flagC']=F['C avg<=-0.05 & t<=-2']
t.round(3).to_csv('fr/arena_table2.csv')
print(t[t.flagB][['acct','n','active','tot','avg','wo_avg','t','flagC']].round(3).to_string())
# rare exclusions
print('rare/day-gated excluded with avg<=0:', list(t[(spd[t.index]<0.5)&(t.active>=15)&(t.n>=30)&(t.avg<=0)].index))
for c in ['2026-11-04','2026-11-09','2026-11-11','2026-11-13']:
    after=sum(1 for x in sess if x>=c); pre=d[d.date<c]; post=d[(d.date>=c)&(d.strategy.isin(setups))]
    tt,FF=flags(pre,after)
    out=[]
    for k,m in FF.items():
        S=set(tt[m].index); g=post[post.strategy.isin(S)]; o=post[~post.strategy.isin(S)]
        per=g.groupby('strategy').r_multiple.mean()
        out.append(f"{k}: {len(S)} set, fwd {len(g)} tr {g.r_multiple.mean() if len(g) else float('nan'):+.3f} (others {o.r_multiple.mean():+.3f}) pos {int((per>0).sum())}/{len(per)}")
    print(c,f'fwd{after}',' | '.join(out))
