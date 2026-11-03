import warnings; warnings.filterwarnings('ignore')
exec(open('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swing1103/load.py').read())
syms='SPY QQQ IWM IWR DIA KRE KBE XLF XLK SMH XLV XLE XLI XLU XLP SPLV VIXY UVXY'.split()
X=pd.DataFrame({s:B[s].close/B[s].open.iloc[0]*100-100 for s in syms})
pd.set_option('display.width',250)
print(X.loc['2026-11-03 10:36':'2026-11-03 11:20'].round(2).to_string())
v=pd.DataFrame({s:B[s].volume for s in ['SPY','QQQ','IWM']}).loc['2026-11-03 09:30':'2026-11-03 11:30']
print(v.resample('5min').sum().to_string())
# previous close gap
for s in ['SPY','QQQ','IWM','KRE']:
    h=H[s]; pc=h.close[h.index.date==h.index.date[-1]].iloc[-1]; print(s,'gap %',round(B[s].open.iloc[0]/pc*100-100,2))
