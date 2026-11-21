from base import *
t=load_raw(); F=pd.read_parquet('idx_feats.parquet')
b=book(t); b=b.merge(F,on=['date','tod'],how='left')
print(b.groupby('half').agg(n=('r','size'),avg=('r','mean'),tot=('r','sum')))
b['nbar']=b.groupby(['date','tod']).r.transform('size')
b['nlong']=b.groupby(['date','tod']).inv.transform(lambda x:(~x).sum())
for h in ['fit','check','t2']:
    x=b[b.half==h]
    print('==',h); print(x.groupby(pd.cut(x.nbar,[0,1,2,3,5,7,100])).agg(n=('r','size'),avg=('r','mean'),tot=('r','sum'),days=('date','nunique')))
big=b[b.nbar>=5].groupby(['half','date','tod']).agg(n=('r','size'),nl=('nlong','first'),R=('r','sum'),spy_fo=('spy_fo','first'),spy_vw=('spy_vw','first'),s950=('spy_s950','first'),r60=('spy_r60','first'),s1300=('spy_s1300','first'),pos=('spy_pos','first'),lowage=('spy_lowage','first'),qfo=('qqq_fo','first'))
pd.set_option('display.width',250); print(big.round(2).to_string())
