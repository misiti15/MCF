import sys, pandas as pd
S = sys.argv[1]
for s in ['SPY','QQQ','IWM']:
    b=pd.read_parquet(f'{S}/bars/{s}.parquet'); b=b.between_time('09:30','15:59'); o=b.open.iloc[0]
    pts=['09:50','10:00','10:15','10:30','11:00','11:30','12:00','13:00','14:00','14:50','15:30','15:59']
    print(s,'open',o,' '.join(f"{p}:{(b.close.at_time(p).iloc[0]/o-1)*100:+.2f}" for p in pts), 'lo',b.low.idxmin().strftime('%H:%M'),round((b.low.min()/o-1)*100,2),'hi',b.high.idxmax().strftime('%H:%M'),round((b.high.max()/o-1)*100,2))
# breadth among t2 traded symbols: share above open
import glob
rows={}
for f in glob.glob(f'{S}/bars/*.parquet'):
    b=pd.read_parquet(f).between_time('09:30','15:59')
    if len(b)<300: continue
    rows[f.split('/')[-1][:-8]]=b.close/b.open.iloc[0]-1
D=pd.DataFrame(rows)
for p in ['10:00','10:30','11:00','12:00','13:00','14:00','14:50','15:55']:
    r=D.loc[D.index.strftime('%H:%M')==p].iloc[0]
    print(p,'breadth(above open) %.2f'%(r>0).mean(),'median %.2f%%'%(r.median()*100), 'n',r.notna().sum())
