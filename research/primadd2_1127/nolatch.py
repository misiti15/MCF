"""PRIMADD2-1127: Primary-book with and without the -2R latch for RW7 / L3-lowdist (run from the scratch dir holding pa2work/all.pkl). Educational only - not financial advice."""
import pandas as pd,sys
sys.argv=[sys.argv[0],'pa2work/all.pkl','/dev/null']
src=open(__file__.replace('nolatch.py','an.py')).read().split('res={}')[0]
exec(src)
for s in ['RW7-gapdn-bounce-early-short-FD','L3-gap-slope-lowdist-FD']:
    x=live[live.strategy==s]
    for lab,kw in [('cap30 no latch',dict(latch=None)),('cap30 + latch',{})]:
        b=book(x,**kw); r=rec(b); print(s[:12],lab,{k:r[k] for k in ['n','sess','tot','avg','wo1','share','dayt','worst','worst_day']})
    b=book(x[x.date<='2026-11-24'],latch=None); print(' to 11-24 no latch',rec(b)['tot'], 'latch',rec(book(x[x.date<='2026-11-24']))['tot'])
