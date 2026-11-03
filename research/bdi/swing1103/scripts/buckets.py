import warnings; warnings.filterwarnings('ignore')
exec(open('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swing1103/load.py').read())
now=B['SPY'].index[-1]+pd.Timedelta(minutes=1)
def fin(r):
    if pd.notna(r.xt): return r.side*(r.exit-r.entry)*r.qty/r.risk
    return r.side*(px(r.sym,now)-r.entry)*r.qty/r.risk
T['R']=T.apply(fin,axis=1)
T['bucket']=pd.cut(T.et.dt.hour*60+T.et.dt.minute,[0,650,665,800,900],labels=['<10:50','10:50-11:04','11:05-13:19','13:20+'])
print(T.groupby('bucket').R.agg(['count','sum','mean']).round(2))
print('as of',now)
# SPY level and IWM-SPY spread at entry
for _,r in T.iterrows():
    print(r.et.strftime('%H:%M'),r.sym,r.strat[:4],round(r.R,2), 'spy%',round(px('SPY',r.et)/B['SPY'].open.iloc[0]*100-100,2),
          'qqq-iwm',round((px('QQQ',r.et)/B['QQQ'].open.iloc[0]-px('IWM',r.et)/B['IWM'].open.iloc[0])*100,2))
