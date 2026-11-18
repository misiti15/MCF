import pandas as pd,numpy as np,json,subprocess,math,sys
t=pd.read_pickle('t.pkl')
CUR5=['L3-gap-slope-fromopen-FD','NM-ETF-late-dip-di-long','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','ST7-rsi50dn-long-pm-t1s1-FD']
sm=json.loads(subprocess.check_output(['git','-C','/home/user/MCF','show','origin/claude/charming-mccarthy-i3rhhr:research/rework/web_families/sector_map.json']))
dl=pd.read_parquet('mkt/daily.parquet'); dl['d']=pd.to_datetime(dl.t).dt.strftime('%Y-%m-%d')
px=dl.pivot(index='d',columns='S',values='c').sort_index(); ret=px.pct_change()
days=list(ret.index)
corr_cache={}
def cmat(d):
    if d not in corr_cache:
        i=days.index(d); w=ret.iloc[max(0,i-40):i]   # prior 40 sessions, excludes d
        corr_cache[d]=w.corr(min_periods=30)
    return corr_cache[d]
LATCH_FROM='2026-10-29'
def ab(s): return {'L3-gap-slope-fromopen-FD':'L3-fromopen','L3-gap-slope-rsi5hi-FD':'L3-rsi5hi'}.get(s,s.split('-')[0])
def run(df,rule,exempt=False):
    keep=[]
    for d,g in df.groupby('date',sort=True):
        g=g.sort_values(['entry_time','id'])
        taken=[]  # rows
        clu={}; fh=0; C=cmat(d) if rule=='CORR2' else None
        for _,r in g.iterrows():
            et=r.entry_time
            closed=[x for x in taken if x.exit_time<=et]; opn=[x for x in taken if x.exit_time>et]
            ok=True
            if d>=LATCH_FROM:
                simR=sum(x.R for x in closed if x.strategy==r.strategy)
                baseR=g[(g.strategy==r.strategy)&(g.exit_time<=et)].R.sum()
                if simR<=-2 and baseR>-2: ok=False
            if rule=='SYM1' and any(x.symbol==r.symbol and x.R<0 for x in closed): ok=False
            if rule=='STACK1' and any(x.symbol==r.symbol for x in opn): ok=False
            if rule in('CLU3','CLU5') and clu.get(r.bar,0)>=(3 if rule=='CLU3' else 5): ok=False
            if rule=='CORR2':
                n=0
                for x in opn:
                    if x.side==r.side and x.symbol!=r.symbol and r.symbol in C.index and x.symbol in C.index:
                        v=C.at[r.symbol,x.symbol]
                        if v==v and v>=0.6: n+=1
                if n>=2: ok=False
            if rule=='SECT3':
                s=sm.get(r.symbol)
                if s and sum(1 for x in opn if x.side==r.side and sm.get(x.symbol)==s)>=3: ok=False
            if rule=='TOD-FH' and r.hm<630 and fh>=6: ok=False
            if rule=='FLAT25' and abs(r.spy_e_fo)<0.25: ok=False
            if exempt and r.strategy=='L3-gap-slope-fromopen-FD' and not (d>=LATCH_FROM and sum(x.R for x in closed if x.strategy==r.strategy)<=-2 and g[(g.strategy==r.strategy)&(g.exit_time<=et)].R.sum()>-2): ok=True
            if ok:
                taken.append(r); clu[r.bar]=clu.get(r.bar,0)+1
                if r.hm<630: fh+=1
        keep+= [x.id for x in taken]
    return set(keep)
def per(Rs):  # per-day stats
    return dict(total=Rs.sum(),green=(Rs>0).mean()*100,median=Rs.median(),worst=Rs.min(),le10=(Rs<=-10).sum())
def win(d): return 'EARLY' if d<'2026-10-23' else ('FIT' if d<='2026-11-05' else 'CHECK')
out=[];pers=[]
for book in ['asis','cur5']:
    df=t if book=='asis' else t[t.strategy.isin(CUR5)]
    alld=sorted(t.date.unique())
    base_ids=run(df,'BASE'); 
    print(book,'baseline sim drops',len(df)-len(base_ids),'actual trades')
    B=df.groupby('date').R.sum().reindex(alld,fill_value=0)
    for rr in ['SYM1','STACK1','CLU3','CLU5','CORR2','SECT3','TOD-FH','FLAT25','STACK1+L3x','CLU5+L3x','CORR2+L3x','SECT3+L3x']:
        rule=rr.replace('+L3x',''); ids=run(df,rule,exempt=rr.endswith('L3x')); rule=rr; k=df[df.id.isin(ids)]
        A=k.groupby('date').R.sum().reindex(alld,fill_value=0)
        dd=A-B; w=pd.Series([win(x) for x in alld],index=alld)
        main=dd[w!='EARLY']; n=len(main); tt=main.mean()/main.std(ddof=1)*math.sqrt(n) if main.std()>0 else 0
        pos=main[main>0]; best_share=(main.max()/pos.sum()*100) if pos.sum()>0 else float('nan')
        b2=per(B[w!='EARLY']); a2=per(A[w!='EARLY'])
        ps=(k.groupby('strategy').R.sum().reindex(df.strategy.unique(),fill_value=0)-df[df.date>='2026-10-23'].groupby('strategy').R.sum()*0) # placeholder
        # per setup effect in main window
        dm=df[df.date>='2026-10-23']; km=k[k.date>='2026-10-23']
        eff=(km.groupby('strategy').R.sum().reindex(dm.strategy.unique(),fill_value=0)-dm.groupby('strategy').R.sum())
        rem=dm[~dm.id.isin(ids)]
        out.append(dict(book=book,rule=rule,removed=len(rem),removed_R=rem.R.sum(),dR=main.sum(),fit=dd[w=='FIT'].sum(),check=dd[w=='CHECK'].sum(),early=dd[w=='EARLY'].sum(),
            t=tt,dR_wo_best=main.sum()-main.max(),best_share=best_share,
            green_b=b2['green'],green_a=a2['green'],med_b=b2['median'],med_a=a2['median'],worst_b=b2['worst'],worst_a=a2['worst'],le10_b=b2['le10'],le10_a=a2['le10'],
            improve=int((eff>0.05).sum()),worsen=int((eff<-0.05).sum()),
            eff='; '.join(f'{ab(s)} {v:+.1f}' for s,v in eff[eff.abs()>0.05].sort_values().items())))
        pers.append(dd.rename(f'{book}:{rule}'))
R=pd.DataFrame(out); R.to_csv('results.csv',index=False); pd.concat(pers,axis=1).to_csv('perday_delta.csv')
pd.set_option('display.width',300); pd.set_option('display.max_colwidth',200)
print(R.drop(columns=['eff']).round(2).to_string()); print(R[['book','rule','eff']].to_string())
