"""COMPASSIDX-1126 Step 0 (information only): SPY return from the day's first W60 confirmation (entry = open of bar T+1)
to 15:55 (open of the 15:55 bar), signed by the confirmed side; mean / median / hit / t, by confirmation-time bucket and by
month; also the stop-distance distribution of the CI-1 stop rule (session extreme opposite, before any cap/floor).
Usage: python step0.py SPLIT OUT.json (SPLIT = FIT, or CHECK / T2 / LIVE only after the PREREG freeze).
Educational only - not financial advice."""
import json
import sys

import numpy as np
import pandas as pd

import ci_lib as C

SPLIT, OUT = sys.argv[1], sys.argv[2]
C.LIVE_MODE = SPLIT == "LIVE"
if SPLIT != "FIT":
    C.prereg_gate()
G, M = C.spy_days([SPLIT]), C.marks([SPLIT])
rows = []
for d in sorted(G):
    if d not in M:
        continue
    g = G[d]; T, L = M[d]
    t0, side = C.first_conf(T, L, 0, 9999)
    if t0 is None:
        continue
    m = g.m.to_numpy(); k0 = np.searchsorted(m, t0 + 1); kx = np.searchsorted(m, C.EXIT_M)
    if k0 >= len(g) or kx >= len(g) or k0 >= kx:
        continue
    e, x = float(g.open.iloc[k0]), float(g.open.iloc[kx])
    ext = float(g.low.iloc[:k0].min()) if side > 0 else float(g.high.iloc[:k0].max())
    rows.append(dict(date=d, T=t0, side=side, drift_bps=side * (x / e - 1) * 1e4, ext_bps=side * (e - ext) / e * 1e4))
x = pd.DataFrame(rows)
C.no_locked(x.date)


def summ(v):
    v = np.asarray(v, float)
    return dict(n=int(len(v)), mean_bps=round(float(v.mean()), 2), median_bps=round(float(np.median(v)), 2),
                hit=round(float((v > 0).mean()), 3), t=round(C.tstat(v), 2))


tb = pd.cut(x["T"], [0, 600, 630, 690, 780, 9999], labels=["10:00", "10:15-10:30", "10:45-11:30", "11:45-13:00", "13:15+"])
res = {"split": SPLIT, "days_bars": len(G), "all": summ(x.drift_bps),
       "by_confirm_time": {str(k): summ(v.drift_bps) for k, v in x.groupby(tb, observed=True)},
       "window_1015_1130": summ(x.drift_bps[(x["T"] >= 615) & (x["T"] <= 690)]),
       "window_0950_1300": summ(x.drift_bps[(x["T"] >= 600) & (x["T"] <= 780)]),
       "by_side": {int(k): summ(v.drift_bps) for k, v in x.groupby("side")},
       "by_month": {k: summ(v.drift_bps) for k, v in x.groupby(x.date.str[:7])},
       "stop_dist_bps_quantiles": {str(q): round(float(x.ext_bps.quantile(q)), 1) for q in (0.05, 0.1, 0.25, 0.5, 0.75, 0.9)}}
res["months_positive"] = f"{sum(v['mean_bps'] > 0 for v in res['by_month'].values())}/{len(res['by_month'])}"
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "by_month"}, indent=1))
print({k: (v["mean_bps"], v["n"]) for k, v in res["by_month"].items()})
