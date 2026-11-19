import pandas as pd, numpy as np, re, sys
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ev1119/w'
TZ='America/New_York'
t=pd.read_parquet(W+'/trades.parquet'); f=pd.read_parquet(W+'/feat.parquet')
t=t.merge(f,on=['id','account'],how='left'); t['R']=t.r_multiple
t['sig']=pd.to_datetime(t.signal_time.astype(str).str.replace('T',' '),utc=True,format='mixed').dt.tz_convert(TZ)
t['ent']=pd.to_datetime(t.entry_time.astype(str).str.replace('T',' '),utc=True,format='mixed').dt.tz_convert(TZ)
t['ext']=pd.to_datetime(t.exit_time.astype(str).str.replace('T',' '),utc=True,format='mixed').dt.tz_convert(TZ)
t['base']=t.strategy.str.replace(r'-WB\d+$','',regex=True)
t['fam']=t.strategy.str.split('-').str[0]
t['mkey']=t.sig.dt.floor('min').astype(str)
n0=len(t); t=t.sort_values('id').drop_duplicates(['base','symbol','date','side','mkey'])
print(f'dedupe: {n0} -> {len(t)} (WB copies / same setup in 2 accounts)')
days=sorted(t.date.unique()); mid=days[len(days)//2]; t['half']=np.where(t.date<mid,'H1','H2')
t['tod']=t.ent.dt.hour*60+t.ent.dt.minute
t['hold']=(t.ext-t.ent).dt.total_seconds()/60
t['sidec']=np.where(t.side>0,'long','short')
# side-relative features: positive = move in trade direction already happened
for c in ['fo_atr','vw_atr','m30_atr','m15_atr','gap_atr','dpc_atr']:
    t['s_'+c]=t[c]*t.side
t['s_rsi5']=np.where(t.side>0,100-t.rsi5,t.rsi5)   # high = stretched AGAINST the trade? no: for long, low RSI -> high value = oversold buy
t['s_spyfo']=t.spy_fo*t.side; t['s_spym30']=t.spy_m30*t.side; t['s_spygap']=t.spy_gap*t.side
t['s_pos']=np.where(t.side>0,t.pos_rng,1-t.pos_rng)
t['ladv']=np.log10(t.adv)
uni=pd.read_csv('/home/user/MCF/data/universe.csv',usecols=['symbol','name'])
etfpat=re.compile(r'ETF|Trust|Fund|ProShares|Direxion|iShares|SPDR|Invesco|Leverage|Daily|2X|3X|Ultra|Bull|Bear|Index|Shares',re.I)
nm=dict(zip(uni.symbol,uni.name))
t['etf']=t.symbol.map(lambda s: bool(etfpat.search(str(nm.get(s,'')))) if s in nm else np.nan)
t.to_parquet(W+'/merged.parquet')
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
def summ(g):
    dr=g.groupby('date').R.sum(); tot=g.R.sum(); b=dr.max()
    return pd.Series(dict(n=len(g),avg=g.R.mean(),avg_wo=(tot-b)/max((g.date!=dr.idxmax()).sum(),1) if len(dr) else np.nan,
        bshare=b/tot if tot>0 else np.nan,h1=g[g.half=='H1'].R.mean(),h2=g[g.half=='H2'].R.mean(),n1=(g.half=='H1').sum(),n2=(g.half=='H2').sum(),win=(g.R>0).mean()))
out=[]
def tab(col,bins=None,labels=None,by=None,q=None):
    x=t.copy()
    if q: x['b']=pd.qcut(x[col],q,duplicates='drop')
    elif bins is not None: x['b']=pd.cut(x[col],bins)
    else: x['b']=x[col]
    keys=['b'] if by is None else [by,'b']
    r=x.dropna(subset=['b']).groupby(keys,observed=True).apply(summ)
    s=f'\n### {col}' + (f' by {by}' if by else '') + '\n' + r.round(3).to_string()
    print(s); out.append(s); return r
print('total',summ(t).round(3).to_dict())
tab('tod',bins=[570,590,600,615,630,660,690,720,780,840,870,900,930,960])
tab('tod',bins=[570,600,630,690,780,870,960],by='sidec')
tab('hold',bins=[0,2,5,10,20,30,45,60,120,400])
tab('sidec')
tab('exit_reason')
tab('gap_pct',bins=[-50,-6,-3,-1.5,-0.5,0.5,1.5,3,6,50],by='sidec')
tab('s_fo_atr',q=8)
tab('s_fo_atr',q=6,by='sidec')
tab('s_vw_atr',q=8)
tab('rsi5',bins=[0,15,25,35,50,65,75,85,100],by='sidec')
tab('rvol',q=6)
tab('rvol15',q=6)
tab('atr_pct',q=6)
tab('px',bins=[0,5,10,20,50,100,250,5000])
tab('ladv',q=6)
tab('etf',by='sidec')
tab('s_spyfo',bins=[-5,-0.75,-0.3,-0.1,0.1,0.3,0.75,5])
tab('spy_fo',bins=[-5,-0.75,-0.3,0,0.3,0.75,5],by='sidec')
tab('s_spym30',q=6)
tab('s_m30_atr',q=8)
tab('s_m15_atr',q=6)
tab('rng_atr',q=6)
tab('s_pos',q=5)
tab('dsma20',q=6,by='sidec')
tab('ret5d',q=6,by='sidec')
tab('s_dpc_atr',q=8)
open(W+'/tables.txt','w').write('\n'.join(out))
