import sqlite3,pandas as pd,re
cat=lambda r: ('setupcap' if 'max positions for this setup' in r else 'maxpos' if 'max concurrent' in r else 'bp' if 'buying power' in r.lower() else 'lotcap' if r.startswith('lot cap') or 'setup lot cap' in r else 'size0' if 'size <' in r or 'size 0' in r else 'trades/day' if 'max trades' in r else None)
for a in ['testing2','explore1','livelab','testingd','testinge','testingf']:
    c=sqlite3.connect(f'{a}.db')
    s=pd.read_sql("select day,ts,status,reason,strategy,ref_price,stop,qty from signals where run_id=1 and day>='2026-11-09'",c)
    days=s.day.nunique(); sk=s[s.status=='skipped'].copy(); sk['c']=sk.reason.fillna('').map(cat)
    g=sk.dropna(subset=['c']).groupby('c').size()/days
    sc=sk[sk.c=='setupcap'].groupby('strategy').size().sort_values(ascending=False)/days
    t=pd.read_sql("select date,entry_time,exit_time,entry,shares,stop,strategy from trades where run_id=1 and date>='2026-11-09'",c)
    t['n']=t.entry*t.shares; t['risk']=(t.entry-t.stop).abs()*t.shares
    ev=[]
    for _,r in t.iterrows():
        ev+= [(r.date,r.entry_time,1,r.n),(r.date,r.exit_time or '99',-1,-r.n)]
    e=pd.DataFrame(ev,columns=['d','t','k','n']).sort_values(['d','t','k'])
    e['lots']=e.groupby('d').k.cumsum(); e['not']=e.groupby('d').n.cumsum()
    pk=e.groupby('d')[['lots','not']].max()
    # per-setup peak concurrent
    print(f"== {a} days={days} cat/day={g.round(1).to_dict()} median notional/lot={t.n.median():.0f} median $risk={t.risk.median():.1f} shares med={t.shares.median():.0f} | peak lots max={pk.lots.max()} mean={pk.lots.mean():.0f} peak notional max={pk['not'].max():.0f}")
    print('   setupcap by setup/day:', sc.head(5).round(1).to_dict())
