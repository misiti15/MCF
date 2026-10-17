"""Context-filter neighbourhoods of the module finalists (SPY threshold x window; RSI5 level x window). Counted.
Educational only - not financial advice."""
import json
import numpy as np
from common import DOW, HERE, TRAIN, col, core, dcode, dstat, tod, PARENT
from scan import pick_idx

spy, r5, bp = col["spy_fo"], col["rsi5"], col["buyPressure"]
res, n = [], 0


def ev(name, m, s, g, rf=False):
    global n
    n += 1
    idx = pick_idx(np.flatnonzero(m), s, g, rf)
    r = col[f"p_{s}_{g}"][idx].astype(float)
    tr = TRAIN[idx]
    a = dstat(r, dcode[idx])
    rec = {"cfg": name, "n": a[0], "exp": round(a[1], 4), "t": round(a[2], 2), "exp_tr": round(float(r[tr].mean()), 4),
           "exp_va": round(float(r[~tr].mean()), 4), "n_tr": int(tr.sum()), "n_va": int((~tr).sum())}
    res.append(rec)
    print(rec, flush=True)


with np.errstate(invalid="ignore"):
    for p, g in (("L3a", "t05s1"), ("L3c", "t05s1"), ("L3b", "t1s1")):
        c = core(p, PARENT[p])
        for lv in (0.25, 0.5, 0.75, 1.0):
            for a, b in ((1300, 1500), (1335, 1500), (1400, 1500)):
                ev(f"{p} spy>{lv} {a}-{b} short {g}", c & (spy > lv) & (tod >= a) & (tod <= b), "short", g)
    c = core("L3a", PARENT["L3a"])
    for lv in (20, 30, 40):
        for a, b in ((950, 1500), (1135, 1330), (950, 1130)):
            ev(f"L3a Mon rsi5<={lv} {a}-{b} long t1s1", c & (DOW == 0) & (r5 <= lv) & (tod >= a) & (tod <= b), "long", "t1s1")
    c = core("L3c", PARENT["L3c"])
    for wd in range(5):
        ev(f"L3c dow{wd} bp>0 1300-1430 short t05s1", c & (DOW == wd) & (bp > 0) & (tod >= 1300) & (tod <= 1430), "short", "t05s1")
json.dump({"configs": n, "rows": res}, open(HERE / "neigh2.json", "w"), indent=1)
print("configs", n)
