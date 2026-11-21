import sys,os; os.chdir(sys.argv[1]); sys.path.insert(0,sys.argv[1])
from grid import *
t=load_raw().merge(pd.read_parquet('idx_feats.parquet'),on=['date','tod'],how='left').merge(pd.read_parquet('spy_daily.parquet'),left_on='date',right_index=True,how='left')
tt=t.sort_values(['date','em','symbol'],kind='mergesort').reset_index(drop=True)
nb=tt.groupby(['date','tod']).symbol.transform('size')
tt['nb']=nb; tt['d']=np.where(tt.inv,-1,1); tt['r15n']=tt.d*tt.spy_r15/tt.atr14p
b0=book(t)
bars=tt[tt.nb>=4].groupby(['half','date','tod']).agg(n=('r','size'),ninv=('inv','sum'),r15n=('r15n','first'),rawR=('r','sum')).reset_index()
bk=b0.groupby(['date','tod']).r.agg(['size','sum']).rename(columns={'size':'nbook','sum':'bookR'})
bars=bars.merge(bk,left_on=['date','tod'],right_index=True,how='left')
pd.set_option('display.width',250); print(bars.round(3).to_string())
# CHECK: distribution of booked per-day R and effect
for c in ['V30','V25','V35']:
  for a in ['A3']:
    o=run(t,c,a,['check'])['check']; print(c,a,{k:round(float(v),3) for k,v in o.items() if v==v})
# what if CHECK day 2026-06-17 removed
x=b0[b0.half=='check']; print('check base w/o 06-17', x[x.date!='2026-06-17'].r.sum(), len(x))
print(x[x.date=='2026-06-17'].groupby('tod').r.agg(['size','sum']))
