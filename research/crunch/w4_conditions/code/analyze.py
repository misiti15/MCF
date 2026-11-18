"""W4 conditions map + one bespoke rule per setup (fit earlier half / check later half). Educational only - not financial advice."""
import pandas as pd, numpy as np, json, math
t=pd.read_pickle('trades.pkl'); t=t[t.date<='2026-11-17']
F=pd.read_pickle('feat.pkl')
COND=['tod','gap','spy10','atr_pct','price','adv','withday','vwap','open','pday','or30']
PRIMARY=['L3-gap-slope-fromopen-FD','NM-ETF-late-dip-di-long','NS5-sma50-flush-oversold-long','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','ST7-rsi50dn-long-pm-t1s1-FD']
rawn=t.groupby('strategy').size().sort_values(ascending=False)
top30=list(rawn.index[:30]); setups=top30+[s for s in PRIMARY if s not in top30]
x=t[t.strategy.isin(setups)].merge(F,on=['id','acct'],how='left')
# de-dup twin copies: same setup/symbol/day, signals within 5 min -> keep earliest
x=x.sort_values(['strategy','symbol','date','sig'])
gap_prev=x.groupby(['strategy','symbol','date']).sig.diff()
# chain: drop a trade if it is within 5 min of the previous one AND from a different account
prev_acct=x.groupby(['strategy','symbol','date']).acct.shift()
x['dup']=(gap_prev<=pd.Timedelta(minutes=5))&(prev_acct!=x.acct)
NSET=len(setups); NC=68; N=NC*NSET
BAR=max(1.5,math.sqrt(2*math.log(N))); BARS=max(1.5,math.sqrt(2*math.log(NC)))
QS=[0.1,0.2,0.3]
def daysum(d): return d.groupby('date').R.sum()
def wobd(d):
    s=daysum(d)
    if len(s)==0: return np.nan,np.nan
    b=s.idxmax(); tot=s.sum()
    return s.drop(b).sum()/max(len(d[d.date!=b]),1), (s.max()/tot if tot>0 else np.nan)
def tstat(v):
    v=np.asarray(v,float)
    if len(v)<3 or v.std(ddof=1)==0: return np.nan
    return v.mean()/(v.std(ddof=1)/math.sqrt(len(v)))
mapping=[]; res=[]; cand_all=[]
TODB=[(0,30,'09:30-10:00'),(30,60,'10:00-10:30'),(60,120,'10:30-11:30'),(120,240,'11:30-13:30'),(240,330,'13:30-15:00'),(330,999,'15:00+')]
for s in setups:
    d=x[(x.strategy==s)&(~x.dup)].copy()
    nraw=int(rawn[s]); nd=len(d)
    dfeat=d.dropna(subset=['tod'])
    # map
    for c in COND:
        v=dfeat.dropna(subset=[c])
        if len(v)<9: continue
        try: b=pd.qcut(v[c].rank(method='first'),3,labels=['T1 low','T2 mid','T3 high'])
        except Exception: continue
        for lab,g in v.groupby(b,observed=True):
            mapping.append(dict(setup=s,cond=c,bucket=str(lab),lo=round(g[c].min(),3),hi=round(g[c].max(),3),n=len(g),avgR=g.R.mean(),totR=g.R.sum(),days=g.date.nunique()))
    for lo,hi,lab in TODB:
        g=dfeat[(dfeat.tod>=lo)&(dfeat.tod<hi)]
        if len(g): mapping.append(dict(setup=s,cond='tod_fixed',bucket=lab,lo=lo,hi=hi,n=len(g),avgR=g.R.mean(),totR=g.R.sum(),days=g.date.nunique()))
    for e,g in dfeat.groupby('etf'):
        mapping.append(dict(setup=s,cond='etf',bucket='ETF' if e else 'stock',lo=e,hi=e,n=len(g),avgR=g.R.mean(),totR=g.R.sum(),days=g.date.nunique()))
    # split
    days=sorted(d.date.unique()); half=days[:len(days)//2]; 
    fit=dfeat[dfeat.date.isin(half)]; chk=dfeat[~dfeat.date.isin(half)]
    row=dict(setup=s,primary=s in PRIMARY,in_top30=s in top30,raw_trades=nraw,dedup_trades=nd,feat_trades=len(dfeat),
             sessions=len(days),fit_days=f'{half[0]}..{half[-1]}' if half else '',check_days=f'{days[len(half)]}..{days[-1]}' if len(days)>len(half) else '',
             totR=d.R.sum(),avgR=d.R.mean(),fit_n=len(fit),fit_avg=fit.R.mean(),chk_n=len(chk),chk_avg=chk.R.mean())
    w,sh=wobd(d); row.update(avg_wo_best=w,best_share=sh)
    if len(fit)<20 or len(chk)<10:
        row.update(rule='no rule (too few trades)'); res.append(row); continue
    topcut=fit.R.quantile(0.9); topfit=fit.R>=topcut
    cands=[]
    for c in COND:
        v=fit[c]
        for q in QS:
            for tail in ('low','high'):
                thr=v.quantile(q if tail=='low' else 1-q)
                rm=(fit[c]<thr) if tail=='low' else (fit[c]>thr)
                cands.append((c,tail,q,thr,rm))
    for e in (0,1):
        cands.append(('etf','skip_'+('ETF' if e else 'stock'),None,e,fit.etf==e))
    best=None
    for c,tail,q,thr,rm in cands:
        rm=rm.fillna(False)
        keep=1-rm.mean(); topkeep=1-(rm&topfit).sum()/max(topfit.sum(),1)
        gain=-fit.R[rm].sum()
        elig=keep>=0.7 and topkeep>=0.9 and rm.sum()>0 and fit.R[rm].mean()<0
        cand_all.append(dict(setup=s,cond=c,tail=tail,q=q,thr=thr,fit_keep=keep,fit_topkeep=topkeep,fit_gain=gain,eligible=elig))
        if elig and (best is None or gain>best[5]): best=(c,tail,q,thr,keep,gain,topkeep)
    if best is None:
        row.update(rule='no rule (no eligible tail on fit)'); res.append(row); continue
    c,tail,q,thr,keep,gain,topkeep=best
    def apply(df,c=c,tail=tail,thr=thr):
        if c=='etf': return (df.etf==thr)
        return ((df[c]<thr) if tail=='low' else (df[c]>thr)).fillna(False)
    rmc=apply(chk); kc=chk[~rmc]
    tc=chk.R.quantile(0.9); topc=chk.R>=tc
    dd=(-chk.R.where(rmc,0)).groupby(chk.date).sum()
    tt=tstat(dd.values)
    # plateau: same cond/tail at the other q (thresholds from fit)
    plat=[]
    if c!='etf':
        for q2 in QS:
            if q2==q: continue
            th2=fit[c].quantile(q2 if tail=='low' else 1-q2)
            r2=apply(chk,thr=th2); plat.append(-chk.R[r2].sum())
    w2,sh2=wobd(kc)
    rule=f"skip if {c} {'<' if tail=='low' else '>'} {thr:.3g}" if c!='etf' else f"{tail}"
    row.update(rule=rule,cond=c,tail=tail,q=q,thr=thr,fit_keep=keep,fit_topkeep=topkeep,fit_gain=gain,
        chk_keep=1-rmc.mean(),chk_topkeep=1-(rmc&topc).sum()/max(topc.sum(),1),chk_gain=-chk.R[rmc].sum(),
        chk_removed=int(rmc.sum()),chk_removed_avg=chk.R[rmc].mean() if rmc.sum() else np.nan,
        chk_avg_after=kc.R.mean(),chk_t=tt,plateau=(all(p>0 for p in plat) if plat else None),plateau_gains=';'.join(f'{p:.1f}' for p in plat),
        chk_wo_best_after=w2,chk_best_share_after=sh2,
        chk_days_better=int((dd>0).sum()),chk_days_worse=int((dd<0).sum()))
    ok=row['chk_gain']>0 and row['chk_keep']>=0.7 and row['chk_topkeep']>=0.9 and bool(row['plateau'] if row['plateau'] is not None else True)
    row['verdict']=('PASS' if ok and tt>=BAR else 'LEAD' if ok and tt>=BARS else 'direction holds, below bar' if row['chk_gain']>0 else 'FAIL (worse on check)')
    res.append(row)
R=pd.DataFrame(res); M=pd.DataFrame(mapping); C=pd.DataFrame(cand_all)
R.to_csv('results.csv',index=False); M.to_csv('map.csv',index=False); C.to_csv('cands.csv',index=False)
print('N',N,'bar',round(BAR,2),'per-setup bar',round(BARS,2),'cands',len(C))
pd.set_option('display.width',300); pd.set_option('display.max_columns',40); pd.set_option('display.max_colwidth',40)
print(R[['setup','raw_trades','dedup_trades','sessions','totR','avgR','rule','fit_gain','chk_gain','chk_keep','chk_topkeep','chk_t','plateau','verdict']].round(2).to_string())
