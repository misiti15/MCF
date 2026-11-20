import sys,pandas as pd,numpy as np
sys.argv=['x','lab']; exec(open('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ig_scripts/score.py').read().split("mode=sys.argv[1]")[0])
L=pd.read_parquet(WT+'/research/rootcause_1119/sl_work/family_trades.parquet'); L['date']=L.date.astype(str)
assert not L.date.between('2024-11-01','2025-02-28').any()
L=L.rename(columns={'r':'R'}).reset_index(drop=True); L['sd']=np.where(L.side=='short',-1,1); L['fam']=L.setup.map(S.family_of)
htb=set(pd.read_csv(f'{W}/htb.csv').iloc[:,0])
print('lab rows',len(L),'setups',L.setup.nunique(),'G1 symbols present',L.symbol.isin(SETS['G1']).sum(), sorted(set(L.symbol)&SETS['G1']))
lines=[]
for cfg in ['G1','G2','G3','M1','G1+M1','G1-ETBp','G2-ETBp']:
    X=L
    if cfg.endswith('ETBp'): X=L[~((L.sd==-1)&L.symbol.isin(htb))]
    base=cfg.split('-')[0]; st=SETS['G1']
    if base=='M1': fl=(X.sd==1)&X.symbol.isin(st)
    elif cfg=='G1+M1': fl=X.symbol.isin(st)
    else: fl=(X.sd==-1)&X.symbol.isin(SETS[base])
    for lab,msk in [('all',slice(None)),('early <2025-11',X.date<'2025-11-01'),('late >=2025-11',X.date>='2025-11-01')]:
        Y=X[msk]; g=score(Y,fl.loc[Y.index],'setup'); lines.append(summ(g,f'{cfg} {lab}'))
        if lab=='all':
            if len(g): g.round(3).to_csv(f'{OUT}/lab_{cfg.replace("+","_")}.csv',index=False)
            gf=score(Y,fl.loc[Y.index],'fam'); lines.append(summ(gf,f'{cfg} {lab} by family'))
            x=Y[fl.loc[Y.index]]; lines.append(f'|   removed {len(x)} fires, {x.R.sum():+.1f}R, avg {x.R.mean():+.3f}, w/o best day {awob(x)[0]:+.3f} | | | | | |')
            if cfg in('G1','G1-ETBp','M1'): print(cfg,'worst 6:\n',g.sort_values('d').head(6)[['setup','n','cut','cutR','avg0','avg1','wob0','wob1','d']].round(3).to_string()); print('best 6:\n',g.sort_values('d').tail(6)[['setup','n','cut','cutR','d']].round(1).to_string()); print(gf.sort_values('d')[['fam','cut','d']].round(1).to_string())
print('\n'.join(lines))
