"""R3C: live realised implementation cost vs research and calibrated model, per benchmark / family setup (all 36 days;
the calibrated cells were fit on these same days, so this is an in-sample consistency check, not validation)."""
import json, numpy as np, pandas as pd
from calib import prep, BORROW
import rescore as RS
t = prep()
t["real_ps"] = t.ent_ps + t.ext_ps + np.where(t.side < 0, BORROW * t.ref_price, 0.0)
kd = t.kind.map({"target": 2, "stop": 1, "market": 0}).to_numpy()
t["cal_ps"] = RS.cal_ps(t.ref_price.to_numpy(), t.tod.to_numpy(), kd, t.side.to_numpy())
import calib as CB
t["cal2_ps"] = CB.predict2_ps(RS.CELLS, RS.CELLS2, t.ref_price.to_numpy(), t.tod.to_numpy(), t.kind.to_numpy(), t.side.to_numpy(), t.risk_ps.to_numpy())
for c in ("real", "res", "cal", "cal2"): t[c + "_R"] = t[c + "_ps"] / t.risk_ps
S = {"L3-fromopen": "L3-gap-slope-fromopen-FD", "RW3-FD": "RW3-gapdn-rsi5pop-flowsell-short-FD", "L3-lowdist": "L3-gap-slope-lowdist-FD",
     "RW5-FD": "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "L3-rsi5hi": "L3-gap-slope-rsi5hi-FD", "RW6-FD": "RW6-ns2-up3-short-FD",
     "NM-RWN4": "NM-RWN4-ns2-spyup05-notfri-short", "CWT14-orl-WB5": "CWT14-failbrk-orl-p10-long-WB5", "NM-ETF-late-dip": "NM-ETF-late-dip-di-long",
     "CWT09-g10": "CWT09-gapdn-vwaploss-g10-short", "RW7-FD": "RW7-gapdn-bounce-early-short-FD",
     "GEN-261029-06": "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short",
     "GEN-261027-01": "GEN-261027-01", "GEN-261019-02": "GEN-261019-02", "GEN-261023-06": "GEN-261023-06", "NM-AR-AM-capit": "NM-AR-AM-gapdown-capitulation-long"}
rows = []
for k, s in S.items():
    x = t[t.strategy.str.startswith(s)]
    if not len(x): continue
    lo, hi = x.real_R.quantile([.01, .99])
    rows.append(dict(setup=k, n=len(x), med_px=round(x.ref_price.median(), 1), lt20=round((x.ref_price < 20).mean(), 2),
                     med_stop_bps=round((x.risk_ps / x.ref_price * 1e4).median(), 0),
                     real_R=round(x.real_R.clip(lo, hi).mean(), 3), lr8_only_R=round(((x.lr8_usd / x.shares.abs()) / x.risk_ps).mean(), 3),
                     entry_slip_R=round((x.side * (x.entry - x.ref_price) / x.risk_ps).clip(-1, 1).mean(), 3),
                     res_R=round(x.res_R.mean(), 3), cal_R=round(x.cal_R.mean(), 3), cal2_R=round(x.cal2_R.mean(), 3)))
df = pd.DataFrame(rows); print(df.to_string(index=False)); df.to_csv("persetup_live_cost.csv", index=False)
