"""Family scan: base vs A-SR vs A-GA for RSI-candidate lab setups; plus ST7-FD B-WIN / C-SKIP. Open months only."""
import sys, glob, yaml, importlib.util, numpy as np, pandas as pd, time, re, os, warnings
warnings.filterwarnings('ignore')
REPO='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/st7w'
sys.path.insert(0,REPO); sys.path.insert(0,'/home/user/MCF/research/history2y')
from lib import load_month, months
from mcf.research import gates as G
from mcf.research.heat import COMPONENTS
ALL=os.environ.get('ALLSETUPS')=='1'
mods={}
for p in sorted(glob.glob(REPO+'/config/*.yaml')):
    y=yaml.safe_load(open(p))
    for n,s in ((y or {}).get('strategies') or {}).items():
        if isinstance(s,dict) and s.get('type')=='lab' and s.get('enabled') and n not in mods:
            mods[n]=dict(module=s['module'],min_adv=float(s.get('min_adv') or 0),window=tuple(s.get('window') or (950,1500)),geom=s.get('geom'))
tok=re.compile(r"""['"](rsi|rsi5|rsiSlope|rsiHeat|heat|bear_div|bull_div)['"]|col\(\s*['"]rsi|\.rsi\b|\.heat\b""")
L={}
for n,s in mods.items():
    path=REPO+'/'+s['module']; t=open(path).read()
    for lib in re.findall(r'import (\w+_lib) as',t):
        lp=os.path.join(os.path.dirname(path),lib+'.py')
        if os.path.exists(lp): t+=open(lp).read()
    s['cand']=bool(tok.search(t))
    if not (s['cand'] or ALL): continue
    try:
        sp=importlib.util.spec_from_file_location('m_'+re.sub(r'\W','_',n),path); m=importlib.util.module_from_spec(sp)
        sys.path.insert(0,os.path.dirname(path)); sp.loader.exec_module(m)
        g=s['geom'] or getattr(m,'GEOM','t1s1')
        if g not in ('t1s1','t05s1','t1s05') or getattr(m,'SIDE',None) not in ('long','short'): continue
        L[n]=(m,g,m.SIDE)
    except Exception as e: print('skip',n,type(e).__name__,flush=True)
ST7='ST7-rsi50dn-long-pm-t1s1-FD'
COLS=['rsi','rsi5','rsiSlope','bear_div','bull_div','rsiHeat']
def variant_cols(df,V,mo):
    parts=[]
    for f in glob.glob(f'{W}/rsi/{V}_*.parquet'):
        x=pd.read_parquet(f); x=x[x.date.str.startswith(mo)]; parts.append(x)
    x=pd.concat(parts); x['date']=pd.to_datetime(x.date).dt.date
    d=df.copy()
    k=d[['symbol','date','tod']].astype({'symbol':str}).merge(x.astype({'symbol':str}),on=['symbol','date','tod'],how='left')
    has=k['rsi'].notna().to_numpy()|k['rsiSlope'].notna().to_numpy()|k['bear_div'].notna().to_numpy()
    for c in COLS:
        v=k[c].to_numpy(); d.loc[has,c]=v[has].astype(d[c].dtype if c in d else 'float32')
    vh,mh,rh,ph,th=[d[c].to_numpy(float) for c in ['volumeHeat','momentumHeat','rsiHeat','priceActionHeat','trendHeat']]
    bonus=(np.where((vh>5)&(mh>5),5,0)+np.where((rh>10)&(ph>5),5,0)+np.where((vh<-5)&(mh<-5),-5,0)+np.where((rh<-10)&(ph<-5),-5,0))
    d['heat']=np.clip(d[COMPONENTS].to_numpy(float).sum(1)+bonus,-100,100).astype('float32')
    return d, has
def run(mo):
    t0=time.time(); out=[]; fires=[]
    df=load_month(mo,context=True)
    tod=df.tod.to_numpy(); adv=df.adv20.fillna(0).to_numpy()
    for V in ('base','SR','GA'):
        d=df if V=='base' else variant_cols(df,V,mo)[0]
        for n,(m,g,side) in L.items():
            s=mods[n]; lo,hi=s['window']
            try:
                with np.errstate(all='ignore'): mk=np.asarray(m.mask(d),bool)
            except Exception as e:
                print('err',n,V,type(e).__name__,flush=True); continue
            mk=mk&(tod>=max(950,lo))&(tod<=min(1500,hi))&(adv>=s['min_adv'])
            tr=G.lab_trades(d,mk,side,g); tr['setup']=n; tr['side']=side; tr['var']=V; out.append(tr)
            if mo>='2026-10':
                live=mk&(df.date.astype(str).to_numpy()>='2026-10-06')
                ii=np.flatnonzero(live); fires.append(pd.DataFrame({'setup':n,'var':V,'symbol':df.symbol.astype(str).to_numpy()[ii],'date':df.date.astype(str).to_numpy()[ii],'tod':tod[ii]}))
            if n==ST7 and V=='base':
                for nm,extra in (('BWIN',(tod>=1335)&(tod<=1500)),('CSKIP',tod!=1045)):
                    tr=G.lab_trades(d,mk&extra,side,g); tr['setup']=n; tr['side']=side; tr['var']=nm; out.append(tr)
    x=pd.concat(out,ignore_index=True); x['symbol']=x.symbol.astype(str)
    if fires: pd.concat(fires,ignore_index=True).to_parquet(f'{W}/scan/fires_{mo}{"_all" if ALL else ""}.parquet')
    x.to_parquet(f'{W}/scan/{mo}{"_all" if ALL else ""}.parquet'); print(mo,len(L),f'{time.time()-t0:.0f}s',flush=True)
if __name__=='__main__':
    import multiprocessing as mp
    os.makedirs(W+'/scan',exist_ok=True)
    ms=sys.argv[1:] or months()
    todo=[m for m in ms if not os.path.exists(f'{W}/scan/{m}{"_all" if ALL else ""}.parquet')]
    print('setups',len(L),'months',todo,flush=True)
    with mp.Pool(int(os.environ.get('NW','3'))) as p: p.map(run,todo,chunksize=1)
