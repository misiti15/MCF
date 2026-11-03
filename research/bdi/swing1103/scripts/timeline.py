import warnings; warnings.filterwarnings('ignore')
exec(open('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swing1103/load.py').read())
day=pd.Timestamp('2026-11-03',tz=NY)
o={s:B[s].open.iloc[0] for s in B}
T['xpx']=T.exit
last=B['SPY'].index[-1]+pd.Timedelta(minutes=1)
def state(t):
    out=dict(t=t.strftime('%H:%M'),open_r=0,open_usd=0,real_r=0,real_usd=0,nl=0,ns=0,beta_usd=0,beta_r=0)
    for _,r in T.iterrows():
        if r.et>t: continue
        if pd.notna(r.xt) and r.xt<=t:
            pnl=r.side*(r.exit-r.entry)*r.qty
            out['real_usd']+=pnl; out['real_r']+=pnl/r.risk; continue
        p=px(r.sym,t); pnl=r.side*(p-r.entry)*r.qty
        out['open_usd']+=pnl; out['open_r']+=pnl/r.risk
        out['nl' if r.side>0 else 'ns']+=1
        out['beta_usd']+=r.side*r.qty*p*r.beta
        out['beta_r']+=r.side*r.qty*p*r.beta*0.01/r.risk
    out['spy']=px('SPY',t)/o['SPY']*100-100; out['qqq']=px('QQQ',t)/o['QQQ']*100-100
    out['iwm']=px('IWM',t)/o['IWM']*100-100
    return out
ts_=[day+pd.Timedelta(hours=9,minutes=50)+pd.Timedelta(minutes=5*i) for i in range(60)]
ts_=[t for t in ts_ if t<=last]
L=pd.DataFrame([state(t) for t in ts_]).round(2)
L['tot_r']=L.open_r+L.real_r; L['tot_usd']=L.open_usd+L.real_usd
pd.set_option('display.width',250)
print(L.to_string())
# minute-level trough
M=pd.DataFrame([state(day+pd.Timedelta(hours=10,minutes=30+i)) for i in range(45)])
M['tot_r']=M.open_r+M.real_r; M['tot_usd']=M.open_usd+M.real_usd
print(M[['t','tot_r','tot_usd','spy','qqq','iwm','nl','ns','beta_r']].round(2).to_string())
L.to_csv('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swing1103/timeline.csv',index=False)
