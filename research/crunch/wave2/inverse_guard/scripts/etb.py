import sys,pandas as pd,numpy as np
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ig_tmp'
sys.path.insert(0,'/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/forward/compass_gate'); import shadow as S
G1=set(S.INVERSE)|set(S.LONG_VOL)
s=pd.read_pickle(f'{W}/sig.pkl'); s=s[s.run_id==1]
s['etb']=(s.status=='skipped')&(s.reason=='not shortable/ETB'); s['sub']=s.status=='submitted'
s['cls']=np.where(s.symbol.isin(G1),'inv/vol','other')
p=s.groupby(['acct','strategy','symbol','day','cls']).agg(etb=('etb','any'),sub=('sub','any')).reset_index()
p=p[p.etb|p['sub']]; p['per']=np.where(p.day>='2026-11-19','11-19 (U9-ETB)','before')
print(p.groupby(['cls','per']).agg(pairs=('sub','size'),submitted=('sub','sum'),etb=('etb','sum')).assign(pass_rate=lambda d:(d.submitted/d.pairs).round(3)).to_string())
q=p[p.cls=='inv/vol']; d=q.groupby(['symbol']).agg(days=('day','nunique'),pass_days=('sub','sum'),etb_days=('etb','sum'))
d=d[(d.pass_days>0)]; print('in-class symbols that got through at least once:'); print(d.sort_values('pass_days',ascending=False).to_string())
# symbols with mixed status (ETB some days, through others)
m=q.groupby(['symbol','day']).agg(e=('etb','any'),u=('sub','any')).reset_index()
x=m.groupby('symbol').agg(etb_days=('e','sum'),sub_days=('u','sum'))
print('mixed-status symbols', x[(x.etb_days>0)&(x.sub_days>0)].to_string())
# lab ETB proxy: symbol HTB if >=50% of its live short signal pairs (any account, run 1) were ETB-skipped
a=s.groupby(['acct','strategy','symbol','day']).agg(etb=('etb','any'),sub=('sub','any'),n=('etb','size')).reset_index()
r=a.groupby('symbol').etb.mean(); htb=set(r[r>=0.5].index); pd.Series(sorted(htb)).to_csv(f'{W}/htb.csv',index=False)
print('HTB proxy symbols',len(htb),'of which in G1',len(htb&G1),'G1 symbols seen',len(set(r.index)&G1))
w=pd.read_pickle(f'{W}/wi.pkl'); w['inv']=w.symbol.isin(G1)
print('what-if ETB-skipped shorts (run 2): ', w.groupby('inv').r_multiple.agg(['count','sum','mean']).round(3).to_string())
wi=w[w.inv]; print(wi.groupby('symbol').r_multiple.agg(['count','sum']).round(1).sort_values('sum').T.to_string())
print('by period', wi.assign(p=np.where(wi.date>='2026-11-19','11-19','before')).groupby('p').r_multiple.agg(['count','sum']).round(1).to_string())
