import sqlite3,pandas as pd,numpy as np,math
rows=[]
for a in ['testing2','explore1','livelab','testingd','testinge','testingf']:
    c=sqlite3.connect(f'{a}.db')
    t=pd.read_sql("select date,side,entry,stop,shares,pnl,pnl_adj from trades where run_id=1 and date>='2026-11-02' and exit is not null and shares>0",c)
    t['acct']=a; rows.append(t)
t=pd.concat(rows); t['ps']=(t.entry-t.stop).abs(); t=t[t.ps>0]
t['cost']=(t.pnl-t.pnl_adj).fillna(0)
for f,lab in [(1,'now'),(0.5,'half')]:
    q=np.floor(t.shares*f)
    ok=q>=1
    risk=q*t.ps
    # model costs scale with qty (per-share/per-notional) + fee cent rounding: SEC+TAF each min $0.01 per sell order, CAT negligible
    cpr=(t.cost/t.shares*q)/risk
    cent=0.02/risk
    dist=1-(q*t.ps)/(t.shares*f*t.ps)
    print(lab, f"lots kept {ok.mean():.3%}  med shares {q[ok].median():.0f}  cost/R mean {cpr[ok].mean():.4f} median {cpr[ok].median():.4f}  +cent-rounding fees {cent[ok].mean():.4f}R  $risk med {risk[ok].median():.1f}  rounding $-shortfall>5%: {(dist[ok]>0.05).mean():.1%}  q<5: {(q[ok]<5).mean():.1%}")
print(len(t))
for M in (3,5,8):
    q=np.maximum(np.floor(t.shares*0.5), np.minimum(M, t.shares))
    risk=q*t.ps; cpr=(t.cost/t.shares*q)/risk; cent=0.02/risk
    dol=q*t.entry
    print(M, f"kept 100%  avg $/lot now {(t.shares*t.entry).mean():.0f} -> {dol.mean():.0f} ({dol.sum()/(t.shares*t.entry).sum():.0%})  med $risk {risk.median():.1f}  cost/R {cpr.mean():.4f}  cent fees {cent.mean():.4f}  lots at old size {(q==t.shares).mean():.1%}")
