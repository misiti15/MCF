import sys, numpy as np, pandas as pd
S='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad'
sys.path.insert(0,S+'/inbox/research/ultimate_1119/top10'); sys.path.insert(0,S+'/inbox')
import bench10 as B
SET='NM-ETF-late-dip-di-long'
INV={'SOXS','SQQQ','SPXS','SPXU','SDS','SH','PSQ','QID','DOG','DXD','SDOW','TZA','TWM','SRTY','RWM','FAZ','ERY','LABD','DUST','TECS','SPDN','JDST','YANG','DRV','SOXS'}
GROUP={}
for g,ss in {'sp':'SPY IVV VOO SPLG SSO SPXL UPRO RSP VTI IVW SPYG VOOG IWF VUG MGK MTUM SPMO VLUE DIA DDM UDOW IJH MDY SPMD IWR VO IWP SCHG VONG',
             'ndx':'QQQ QQQM QLD TQQQ BULZ FNGU MAGS XLK VGT IYW TECL IGV CIBR ARKK',
             'semi':'SMH SOXX SOXQ SOXL',
             'small':'IWM IJR SPSM VB SCHA VTWO AVUV IWN IWO UWM TNA URTY',
             'gold':'GDX GDXJ NUGT JNUG GDXU SILJ',
             'bank':'XLF VFH KBE KRE KBWB FAS DPST',
             'energy':'XLE VDE OIH XOP ERX',
             'bio':'XBI IBB LABU ARKG IHI XLV'}.items():
    for s in ss.split(): GROUP[s]=g
def inv_sym(s): return s in INV
def load_raw():
    t1=pd.read_parquet(S+'/top10w/trades_t1.parquet'); t2=pd.read_parquet(S+'/top10w/trades_t2.parquet')
    t1=t1[t1.setup==SET]; t2=t2[t2.setup==SET]
    t1=B.add_r(t1); t2=B.add_r(t2)
    t1['half']=B.half(t1.date); t2['half']='t2'
    t=pd.concat([t1,t2],ignore_index=True)
    B.no_locked(t.date.unique())
    t['inv']=t.symbol.map(inv_sym); t['grp']=t.symbol.map(GROUP).fillna(t.symbol)
    return t
ETB=None
def book(t, rules=None, pre=None):
    """Primary book; pre(t)-> bool keep mask applied to candidates in entry order BEFORE cap (rule filters)."""
    global ETB
    if ETB is None: ETB=pd.Series(dtype=float)  # all longs: borrow filter not used
    rules=rules or B.BOOK['primary']
    if pre is not None: t=t[pre(t)]
    return B.book(t, rules, ETB)
def sessions():
    spy1=B.spy_t1(); d=pd.Series(spy1.index); d=d[d<='2026-11-04']; h=B.half(d)
    spy2=pd.read_parquet(B.FRESH/'spy_days.parquet'); spy2.index=spy2.index.astype(str)
    n2=int(((spy2.index>='2023-01-03')&(spy2.index<='2024-09-13')).sum())
    return {'fit':int((h=='fit').sum()),'check':int((h=='check').sum()),'t2':n2}
