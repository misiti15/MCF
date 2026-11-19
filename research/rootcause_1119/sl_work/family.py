"""All enabled lab setups (any account YAML): first-per-symbol-day trades on the 2-year open history (locked block never read),
production costs, tagged with symbol class and tod. For remedy family tests. Research only."""
import sys, glob, yaml, importlib.util, numpy as np, pandas as pd, time, re, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/user/MCF'); sys.path.insert(0,'/home/user/MCF/research/history2y')
from lib import load_month, months
from mcf.research import gates as G
mods={}
for p in sorted(glob.glob('/home/user/MCF/config/*.yaml')):
    try: y=yaml.safe_load(open(p))
    except Exception: continue
    for n,s in ((y or {}).get('strategies') or {}).items():
        if isinstance(s,dict) and s.get('type')=='lab' and s.get('enabled') and n not in mods:
            mods[n]=dict(module=s['module'],min_adv=float(s.get('min_adv') or 0),window=tuple(s.get('window') or (950,1500)),geom=s.get('geom'),acct=p.split('/')[-1])
L={}
for n,s in mods.items():
    try:
        sp=importlib.util.spec_from_file_location('m_'+re.sub(r'\W','_',n),'/home/user/MCF/'+s['module']); m=importlib.util.module_from_spec(sp)
        sys.path.insert(0,str(__import__('pathlib').Path('/home/user/MCF/'+s['module']).parent)); sp.loader.exec_module(m)
        g=s['geom'] or getattr(m,'GEOM','t1s1')
        if g not in ('t1s1','t05s1','t1s05') or getattr(m,'SIDE',None) not in ('long','short'): continue
        L[n]=(m,g,m.SIDE)
    except Exception as e: print('skip',n,type(e).__name__)
print('setups',len(L),flush=True)
def run(mo):
  out=[];bad=set();t0=time.time()
  if True:
    df=load_month(mo,context=True)
    tod=df.tod.to_numpy(); adv=df.adv20.fillna(0).to_numpy()
    for n,(m,g,side) in L.items():
        s=mods[n]; lo,hi=s['window']
        try:
            with np.errstate(all='ignore'): mk=np.asarray(m.mask(df),bool)
        except Exception as e:
            bad.add(n); continue
        mk=mk&(tod>=max(950,lo))&(tod<=min(1500,hi))&(adv>=s['min_adv'])
        tr=G.lab_trades(df,mk,side,g); tr['setup']=n; tr['side']=side
        out.append(tr)
    print(mo,f'{time.time()-t0:.0f}s',flush=True)
    x=pd.concat(out,ignore_index=True); x['symbol']=x.symbol.astype(str)
    x.to_parquet(f'fam/{mo}.parquet'); return sorted(bad)
if __name__=='__main__':
    import os, multiprocessing as mp
    os.makedirs('fam',exist_ok=True)
    todo=[m for m in months() if not os.path.exists(f'fam/{m}.parquet')]
    with mp.Pool(3) as p:
        bads=p.map(run,todo,chunksize=1)
    print('bad',sorted(set(sum(bads,[]))))
    x=pd.concat([pd.read_parquet(f) for f in sorted(glob.glob('fam/*.parquet'))]); x.to_parquet('family_trades.parquet'); print('done',x.setup.nunique())
