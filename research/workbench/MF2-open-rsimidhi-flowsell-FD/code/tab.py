import pandas as pd, sys
r = pd.concat([pd.read_csv(f"res_{x}.csv") for x in sys.argv[1:]]).drop_duplicates(["cfg", "test", "split"])
a = r[r.split == "ALL"].pivot(index="cfg", columns="test", values=["trades", "avg", "avg_wo_best", "worst_day", "t_vs_PARENT", "total", "avg_native"])
sp = r[r.test == "2y"].pivot(index="cfg", columns="split", values="avg")
P = a.loc["PARENT"]
def verdict(x):
    f = []
    for t in ("replay", "2y"):
        pa, ca = P[("avg", t)], x[("avg", t)]
        if not (ca >= pa - 0.01 or (pa > 0 and ca >= 0.95 * pa)): f.append(f"{t} avg {ca:+.3f}<{pa:+.3f}")
        if x[("avg_wo_best", t)] < P[("avg_wo_best", t)] - 0.02: f.append(f"{t} wo {x[('avg_wo_best', t)]:+.3f}")
        if x[("worst_day", t)] < P[("worst_day", t)] * 1.10 - 1e-9: f.append(f"{t} wd {x[('worst_day', t)]:+.1f}")
    return "PASS" if not f else "FAIL: " + "; ".join(f)
order = list(dict.fromkeys(r.cfg))
for c in order:
    x = a.loc[c]
    print(f"{c[:58]:58s} R n{x[('trades','replay')]:4.0f} {x[('avg','replay')]:+.3f} wo{x[('avg_wo_best','replay')]:+.3f} wd{x[('worst_day','replay')]:+6.1f} | 2y n{x[('trades','2y')]:5.0f} {x[('avg','2y')]:+.3f} wo{x[('avg_wo_best','2y')]:+.3f} wd{x[('worst_day','2y')]:+6.1f} tot{x[('total','2y')]:+6.0f} t{x[('t_vs_PARENT','2y')]:+.2f} | TR{sp.loc[c,'TRAIN']:+.3f} VA{sp.loc[c,'VALID']:+.3f} FW{sp.loc[c,'FWD']:+.3f} | {verdict(x)}")
