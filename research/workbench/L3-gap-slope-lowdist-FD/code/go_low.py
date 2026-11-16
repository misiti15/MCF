import sys, json, importlib
from load_low import *
import sim_low as sim2
import os; REF = os.environ.get("REF", "-"); decl = importlib.import_module(sys.argv[1]); cfgs = getattr(decl, sys.argv[2])
rows = []; base = {}; allt = {}
for name, v in cfgs.items():
    o = run(v); allt[name] = o
    for test, t in o.items():
        if name == "PARENT": base[test] = t
        if REF == name: base[test + "wb3"] = t
        days = DAYS[test]
        parts = [("ALL", t)] + ([(s, t[t.split == s]) for s in ("TRAIN", "VALID", "FWD")] if test == "2y" else [])
        for sp, tt in parts:
            dd = [d for d in days if sp == "ALL" or split(d) == sp]
            r = dict(cfg=name, test=test, split=sp, **sim2.stats(tt), per_day=tt.r.sum() / len(dd))
            for bn in ("PARENT", "REF"):
                b = base.get(test + ("wb3" if bn == "REF" else ""))
                if b is not None:
                    bb = b if sp == "ALL" else b[b.split == sp]
                    r["t_vs_" + bn], r["dR_vs_" + bn] = sim2.paired_t(bb, tt, dd)
            r["avg_win"] = tt.r[tt.r > 0].mean(); r["avg_loss"] = tt.r[tt.r <= 0].mean(); r["hold"] = (tt.xm - tt.em).median()
            rows.append(r)
    a = [x for x in rows if x["cfg"] == name]
    print(f"{name:40s} " + " | ".join(f"{x['test']}/{x['split']} n{x['trades']} {x['avg']:+.3f} wo{x['avg_wo_best']:+.3f} wd{x['worst_day']:+.1f} pd{x['per_day']:+.2f}" for x in a), flush=True)
pd.DataFrame(rows).to_csv(f"res_{sys.argv[2]}.csv", index=False, float_format="%.4f")
pd.to_pickle(allt, f"trades_{sys.argv[2]}.pkl")
