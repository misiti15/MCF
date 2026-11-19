import sys; sys.path.insert(0,'fr')
from score import *
exec(open('fr/lag2.py').read().split("t,F=flags(d,0)")[0].split("from score import *")[1])
s=pd.read_parquet('fr/sig.parquet'); A=['testing2','explore1','livelab','testingd','testinge','testingf','gen']
res=['max positions for this setup','max concurrent positions','halted']
sess=sorted(d.date.unique())
def leaders(dd):
    t=table(dd,setups).sort_values('score'); return set(t[t.n>=10].index[:35]),t
# Review Fri 11-13 after close: data <= 11-13; forward 11-16..11-18
for cut,fwd0 in [('2026-11-13','2026-11-16'),('2026-11-18','2026-11-19')]:
    pre=d[d.date<=cut]; after=sum(1 for x in sess if x>cut)
    L,t=leaders(pre); tt,FF=flags(pre,after)
    B=set(tt[FF['B avg<=0 & t<=-1.5']].index); A0=set(tt[FF['A avg<=0']].index); E=set(tt[FF['EXIT100']].index)
    post=d[(d.date>=fwd0)&(d.account.isin(A))]
    print(f'REVIEW {cut}: leaders {len(L)} | B-moves {len(B)} | A-moves {len(A0)} | EXIT100 {len(E)}')
    if len(post):
        for nm,S in [('leaders',L),('B',B),('A',A0),('EXIT100',E)]:
            g=post[post.strategy.isin(S)]; print(f'   fwd {nm}: {len(g)} tr, {g.r_multiple.sum():+.1f}R, avg {g.r_multiple.mean() if len(g) else 0:+.3f}; share of arena trades {len(g)/len(post):.1%}')
        print(f'   arena all fwd: {len(post)} tr {post.r_multiple.sum():+.1f}R')
    sk=s[(s.account.isin(A))&(s.day>cut if cut<'2026-11-18' else s.day>='2026-11-12')&(s.reason.isin(res))]
    sk2=s[(s.account.isin(A))&(s.day>=('2026-11-17'))&(s.reason.isin(res))]
    print('   arena resource skips (window):',len(sk),'of which leaders',int(sk.strategy.isin(L).sum()),'| since TSZ1 11-17:',len(sk2),'leaders',int(sk2.strategy.isin(L).sum()))
    if cut=='2026-11-18':
        json.dump(dict(leaders=sorted(L),B=sorted(B)),open('fr/now_sets.json','w'))
        lt=t.loc[sorted(L,key=lambda x:t.score[x])]
        print(lt[['n','days','tot','avg','wo_avg','best_share','score']].round(3).to_string())
        # leader stats
        print('leaders total R',round(lt.tot.sum(),1),'n',lt.n.sum(),'wo_tot>0:',int((lt.wo_tot>0).sum()), ' one-day tag (share>=.5):', int((lt.best_share>=0.5).sum()))
