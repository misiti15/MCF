import sys, importlib, pandas as pd
from load3 import *
import sim3, sim
decl = importlib.import_module(sys.argv[1]); cfgs = getattr(decl, sys.argv[2])
rows = []; base = {}; allt = {}
for name, v in cfgs.items():
    o = run(v); allt[name] = o
    for test, t in o.items():
        if name in ("PARENT", "WB4"): base[(name, test)] = t
        days = DAYS[test]
        r = dict(cfg=name, test=test, **sim3.stats(t), per_day=t.r.sum() / len(days), wsum=t.w.sum())
        for dt in ("up", "down", "quiet"):
            x = t[t.dtype == dt]; r["n_" + dt] = len(x); r["avg_" + dt] = x.r.sum() / x.w.sum() if len(x) else float("nan"); r["R_" + dt] = x.r.sum()
        if test == "2y":
            for sp in ("TRAIN", "VALID", "FWD"):
                x = t[t.split == sp]; r["avg_" + sp] = x.r.sum() / x.w.sum()
        for bn in ("PARENT", "WB4"):
            b = base.get((bn, test))
            if b is not None:
                r["t_vs_" + bn], r["dR_vs_" + bn] = sim.paired_t(b, t, days)
        r["avg_win"] = t.r[t.r > 0].mean(); r["avg_loss"] = t.r[t.r <= 0].mean(); r["hold"] = (t.xm - t.em).median()
        r["U_share"] = t.U.mean()
        rows.append(r)
    a = [x for x in rows if x["cfg"] == name]
    print(f"{name:52s} " + " | ".join(f"{x['test']} n{x['trades']} {x['avg']:+.3f} wo{x['avg_wo_best']:+.3f} wd{x['worst_day']:+.1f} up{x['avg_up']:+.3f} dn{x['avg_down']:+.3f} q{x['avg_quiet']:+.3f}" for x in a), flush=True)
pd.DataFrame(rows).to_csv(f"res_{sys.argv[2]}.csv", index=False, float_format="%.4f")
pd.to_pickle(allt, f"trades_{sys.argv[2]}.pkl")
