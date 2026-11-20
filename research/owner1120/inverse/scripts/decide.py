"""Per-setup handling by the pre-registered choice rule (PLAN.md 'Choice per setup'); afford-to-drop; L3 detail."""
import sys, pandas as pd, numpy as np
WT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inv1120_tmp'
OUT=WT+'/research/owner1120/inverse'
sys.path.insert(0,OUT); import shadow as S
def prep(T):
    T=T.reset_index(drop=True).copy(); T['pc']=T.symbol.map(S.pclass); T['bs']=T.symbol.map(S.beta_sign); T['fam']=T.strategy.map(S.family_of); return T
live=prep(pd.read_pickle(f'{W}/live.pkl')); lab=prep(pd.read_pickle(f'{W}/lab.pkl'))
def st(d): return pd.Series(dict(n=len(d),R=d.R.sum(),avg=d.R.mean() if len(d) else np.nan))
rows=[]
LI=live[live.bs==-1]; LB=lab[lab.bs==-1]
for (s,side),_ in pd.concat([LI,LB]).groupby(['strategy','side']):
    a=LI[(LI.strategy==s)&(LI.side==side)]; b=LB[(LB.strategy==s)&(LB.side==side)]
    lf,lc=a[a.date<='2026-11-05'],a[a.date>'2026-11-05']; bf,bc=b[b.date<'2025-11-01'],b[b.date>='2025-11-01']
    allS=live[(live.strategy==s)]
    r=dict(setup=s,side='short' if side<0 else 'long',live_n=len(a),live_R=a.R.sum(),live_fit_n=len(lf),live_fit_avg=lf.R.mean(),live_chk_R=lc.R.sum(),
           lab_n=len(b),lab_R=b.R.sum(),lab_fit_n=len(bf),lab_fit_avg=bf.R.mean(),lab_chk_n=len(bc),lab_chk_R=bc.R.sum(),lab_chk_avg=bc.R.mean(),
           live_setup_trades=len(allS),share_of_reps=len(a)/len(allS) if len(allS) else np.nan)
    if side<0:
        fitok=(len(lf)>=5 and lf.R.mean()>0) or (len(bf)>=5 and bf.R.mean()>0)
        chkok=(lc.R.sum()>=0 if len(lc) else True) and (bc.R.sum()>=0 if len(bc) else True) and (len(lc)+len(bc)>0)
        r['handling']='KEEP shorts (H2S)' if fitok and chkok else 'block shorts (H1)'
    else:
        neg=(len(a)>=5 and a.R.mean()<0) and (len(bc)>=5 and bc.R.mean()<0)
        r['handling']='BLOCK longs' if neg else 'keep longs (H2)'
    rows.append(r)
D=pd.DataFrame(rows).sort_values(['side','live_R']); D.round(3).to_csv(OUT+'/tables/per_setup_handling.csv',index=False)
print(D.handling.value_counts().to_string())
print('SHORT_KEEP:',sorted(D[D.handling.str.startswith('KEEP')].setup)); print('LONG_BLOCK:',sorted(D[D.handling=='BLOCK longs'].setup))
for h in D.handling.unique():
    x=D[D.handling==h]; print(f'{h}: setups {len(x)}, live {int(x.live_n.sum())} trades {x.live_R.sum():+.1f}R (check {x.live_chk_R.sum():+.1f}R), lab {int(x.lab_n.sum())} {x.lab_R.sum():+.1f}R (check {x.lab_chk_R.sum():+.1f}R)')
print(D[D.handling.isin(['KEEP shorts (H2S)','BLOCK longs'])][['setup','side','live_n','live_R','live_chk_R','lab_fit_n','lab_fit_avg','lab_chk_n','lab_chk_R','handling']].round(2).to_string())
# chosen handling scored live per setup x account (and by family), all + check window
sk=set(D[D.handling.str.startswith('KEEP')].setup); lb=set(D[D.handling=='BLOCK longs'].setup)
def rm_of(T): return (T.bs==-1)&(((T.side<0)&~T.strategy.isin(sk))|((T.side>0)&T.strategy.isin(lb)))
_src=open(OUT+'/scripts/score.py').read(); exec('def awob'+_src.split('def awob',1)[1].split('INVV=lambda')[0])
for src,T in [('live',live),('lab',lab)]:
    rm=rm_of(T); key=['acct','strategy'] if src=='live' else ['strategy']
    for wl,m in ([('all',T.date>=''),('ex 11-19',T.date!='2026-11-19'),('check 11-06..',T.date>'2026-11-05')] if src=='live' else [('all',T.date>=''),('fit',T.date<'2025-11-01'),('check',T.date>='2025-11-01')]):
        Y=T[m]; g=score(Y,rm.loc[Y.index],None,key); print(summ(g,f'CHOSEN {src} {wl}'))
        if wl=='all':
            g.round(3).to_csv(f'{OUT}/tables/{src}_CHOSEN.csv',index=False); gf=score(Y,rm.loc[Y.index],None,['fam']); print(summ(gf,f'CHOSEN {src} all by family'))
            gf.round(3).to_csv(f'{OUT}/tables/{src}_CHOSEN_fam.csv',index=False)
            if src=='live': print(gf.sort_values('d')[['fam','n','cut','cutR','d','wob0','wob1','share0','share1']].round(2).to_string())
# afford to drop: H1M per setup (live), the setups that LOSE if everything inverse is blocked
g=pd.read_csv(OUT+'/tables/live_H1M.csv'); w=g[g.d<-0.005].sort_values('d')
print('afford-to-drop (block all inverse/vol, both sides): setups hurt',len(w),f'{w.d.sum():.1f}R, reps lost {int(w.cut.sum())}; top:'); print(w.head(10)[['acct','strategy','n','cut','base','new','d']].round(2).to_string())
lr=live[(live.bs==-1)]; print('reps share of all live trades: inverse/vol',len(lr),f'{len(lr)/len(live):.1%}', ' longs',int((lr.side>0).sum()),' shorts',int((lr.side<0).sum()))
# L3 detail
L3=live[live.fam=='L3']; x=L3[L3.bs==-1]
print('L3 live inverse trades by copy:'); print(x.groupby(['acct','strategy','symbol']).R.agg(['count','sum']).round(2).to_string())
print('L3 live: underlying (index ETF) shorts:', L3[L3.symbol.isin(S.INVERSE_OF)&L3.symbol.isin(['SPY','QQQ','IWM','DIA','SOXX','XLK','XLF','SMH'])].shape[0])
lb3=lab[lab.fam=='L3']; print('L3 lab: inverse shorts',(lb3.bs==-1).sum(), f'{lb3[lb3.bs==-1].R.sum():+.1f}R', ' index-underlying shorts', lb3.symbol.isin(['SPY','QQQ','IWM','DIA','SOXX','XLK','XLF']).sum())
# playing time in low-rep homes under CHOSEN
c=pd.read_csv(f'{OUT}/tables/live_CHOSEN.csv'); c['frac']=c.cut/c.n
print('playing time: setup x accounts losing >25% of reps:'); print(c[c.frac>0.25][['acct','strategy','n','cut','base','new']].round(2).to_string())
