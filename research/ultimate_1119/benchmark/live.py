import pandas as pd, numpy as np, json
d=pd.read_parquet('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ev1119/w/trades.parquet')
S=["L3-gap-slope-fromopen-FD","L3-gap-slope-lowdist-FD","L3-gap-slope-rsi5hi-FD","RW3-gapdn-rsi5pop-flowsell-short-FD","RW5-heat30-flowsell-rsi5pop-gapdn-short-FD","NM-ETF-late-dip-di-long","ST7-rsi50dn-long-pm-t1s1-FD","GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long"]
out={}
for s in S:
    g=d[d.strategy==s]
    day=g.groupby('date').r_multiple.sum()
    tot=g.r_multiple.sum(); best=day.idxmax()
    out[s]=dict(trades=len(g),sessions_traded=int(day.size),first=str(g.date.min()),last=str(g.date.max()),
      accounts=g.groupby('account').size().to_dict(),win=round((g.r_multiple>0).mean(),3),avg_r=round(g.r_multiple.mean(),3),
      avg_r_wo_best_day=round(g[g.date!=best].r_multiple.mean(),3),best_day_share=round(day.max()/tot,3) if tot>0 else None,
      total_r=round(tot,2),worst_day=round(day.min(),2),trades_per_traded_session=round(len(g)/day.size,2))
    print(s[:40], out[s])
json.dump(out,open('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/bench_w/live.json','w'),indent=1)
