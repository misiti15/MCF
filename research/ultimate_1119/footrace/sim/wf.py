import sys; sys.path.insert(0,'fr')
from score import *
sess=sorted(d.date.unique())
setups=list(arena); act_now={s:reps.get(s,{}).get('active_days',0) for s in arena}
spd={s:(reps.get(s,{}).get('signals',0)/max(1,act_now[s])) for s in arena}
for c in ['2026-11-04','2026-11-09','2026-11-11','2026-11-13']:
    after=sum(1 for x in sess if x>=c)
    pre=d[d.date<c]; post=d[(d.date>=c)&(d.strategy.isin(setups))]
    t=table(pre,setups); t['active']=pd.Series({s:max(0,act_now[s]-after) for s in setups})
    t=t.sort_values('score'); elig=t.n>=10
    lead=set(t[elig].index[:35])
    for thr,name in [(0,'avg<=0'),(-0.05,'avg<=-0.05')]:
        lag=set(t[(t.active>=15)&(t.n>=30)&(t.avg<=thr)&(t.wo_avg<=0)&(pd.Series(spd)[t.index]>=0.5)].index)
        rest=set(setups)-lag-lead
        def f(S):
            g=post[post.strategy.isin(S)]; per=g.groupby('strategy').r_multiple.mean()
            return f"{len(S)} setups {len(g)} tr avgR {g.r_multiple.mean():+.3f} totR {g.r_multiple.sum():+.1f} pos {int((per>0).sum())}/{len(per)}"
        print(c,f'fwd {after} sess |',name,'LAG:',f(lag),'| LEAD:',f(lead),'| REST:',f(rest))
