# Team-6 live stats for the EOW report (owner 2026-11-10). Run from a dir holding <branch>.db journals:
#   for b in mcf-data mcf-data-testing mcf-data-testing2 mcf-data-gen mcf-data-graveyard mcf-data-explore1 mcf-data-livelab; do git show origin/$b:journal.db > $b.db; done
import sqlite3,glob,collections
T6=['RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','L3-gap-slope-fromopen-FD','ST7-rsi50dn-long-pm-t1s1-FD','NS5-sma50-flush-oversold-long','NM-ETF-late-dip-di-long']
rows=[]
for f in glob.glob('*.db'):
    c=sqlite3.connect(f)
    for s in T6:
        for d,e,sp,sh,p in c.execute("select date,entry,stop,shares,pnl_adj from trades where run_id=1 and strategy=? and exit_time is not null and pnl_adj is not null",(s,)):
            risk=abs(e-sp)*sh
            if risk>0: rows.append((f[:-3],s,d,p/risk,p))
# primary all-setup daily (actual)
c=sqlite3.connect('mcf-data.db'); P=collections.defaultdict(float); Pn=collections.Counter()
for d,e,sp,sh,p in c.execute("select date,entry,stop,shares,pnl_adj from trades where run_id=1 and exit_time is not null and pnl_adj is not null"):
    r=abs(e-sp)*sh
    if r>0: P[d]+=p/r; Pn[d]+=1
days=sorted(set(r[2] for r in rows)|set(P))
print('days',len(days),days[0],days[-1])
day=collections.defaultdict(float); dn=collections.Counter(); dd=collections.defaultdict(float)
for a,s,d,R,p in rows: day[d]+=R; dn[d]+=1; dd[d]+=p
per=collections.defaultdict(lambda:[0,0.0,set(),collections.defaultdict(float),collections.Counter()])
for a,s,d,R,p in rows:
    x=per[s]; x[0]+=1; x[1]+=R; x[2].add(d); x[3][d]+=R; x[4][a]+=1
for s,x in per.items():
    best=max(x[3].values()); print(f"{s:45s} n={x[0]:4d} sess={len(x[2]):3d} R={x[1]:+7.2f} avg={x[1]/x[0]:+.3f} wo_best_avg={(x[1]-best)/max(1,x[0]):+.3f} best%={best/x[1]*100 if x[1]>0 else float('nan'):.0f} accts={dict(x[4])}")
tot=sum(day.values()); n=sum(dn.values())
g=sum(1 for d in day if day[d]>0)
print(f"TEAM6 total R {tot:+.2f} trades {n} sessions-with-trades {len(day)} green {g} worst {min(day.values()):+.2f} best {max(day.values()):+.2f}")
both=[d for d in days if d in P]
print(f"PRIMARY actual over its {len(P)} sessions: R {sum(P.values()):+.2f} trades {sum(Pn.values())} green {sum(1 for d in P if P[d]>0)} worst {min(P.values()):+.2f}")
print("TEAM6 restricted to Primary's sessions:",round(sum(day.get(d,0) for d in P),2))
for d in days: print(d, f"T6 {day.get(d,0):+6.2f} ({dn.get(d,0):3d}tr)  Primary {P.get(d,0):+6.2f} ({Pn.get(d,0):3d}tr)")
