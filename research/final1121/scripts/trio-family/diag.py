import pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from score import B, filt, TOP, TRIO
T=B.add_r(pd.read_parquet('trades_fit.parquet')); T=T[(B.half(T.date)=='fit')&(T.grp=='real')]
P=B.add_r(pd.read_parquet(TOP/'trades_t1.parquet')); P=P[(B.half(P.date)=='fit')&P.setup.isin(TRIO)].rename(columns={'setup':'cfg'})
X=pd.concat([filt(T),filt(P)])
X['tb']=pd.cut(X.tod,[0,1030,1130,1300,1600],labels=['<1030','1030-1130','1130-1300','>=1300'])
X['gb']=pd.cut(X.gap,[-100,-6,-4,-2.657,-1,0,100],labels=['<-6','-6..-4','-4..-2.66','-2.66..-1','-1..0','>0'])
pd.set_option('display.width',250)
for k in ['tb','gb']:
    print(X.pivot_table(index='cfg',columns=k,values='r',aggfunc='mean',observed=False).round(3).to_string())
    print(X.pivot_table(index='cfg',columns=k,values='r',aggfunc='size',observed=False).to_string())
