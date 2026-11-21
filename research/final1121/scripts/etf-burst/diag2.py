from base import *
t=load_raw(); F=pd.read_parquet('idx_feats.parquet'); D=pd.read_parquet('spy_daily.parquet')
b=book(t).merge(F,on=['date','tod'],how='left').merge(D,left_on='date',right_index=True,how='left')
b=b[b.half.isin(['fit','t2'])]
b['nbar']=b.groupby(['date','tod']).r.transform('size')
b['d']=np.where(b.inv,-1,1)
big=b[b.nbar>=4].groupby(['half','date','tod']).agg(n=('r','size'),d=('d','mean'),R=('r','sum'),fo=('spy_fo','first'),r15=('spy_r15','first'),r60=('spy_r60','first'),atr=('atr14p','first'),r5d=('ret5d','first'),q15=('qqq_r15','first'))
big['r15n']=big.r15/big.atr
pd.set_option('display.width',250); print(big.round(2).to_string())
