import sys, importlib, pandas as pd
from load import *
decl = importlib.import_module(sys.argv[1]); cfgs = getattr(decl, sys.argv[2])
rows = []; base = {}; allt = {}
for name, v in cfgs.items():
    o = run(v); allt[name] = o
    for test, t in o.items():
        if name == "PARENT": base[test] = t
        days = DAYS[test]
        parts = [("ALL", t)] + ([(s, t[t.split == s]) for s in ("TRAIN", "VALID", "FWD")] if test == "2y" else [])
        for sp, tt in parts:
            dd = [d for d in days if sp == "ALL" or split(d) == sp]
            r = dict(cfg=name, test=test, split=sp, **sim.stats(tt), per_day=tt.r.sum() / len(dd))
            b = base.get(test)
            bb = b if sp == "ALL" else b[b.split == sp]
            r["t_vs_parent"], r["dR_vs_parent"] = sim.paired_t(bb, tt, dd)
            r["avg_win"] = tt.r[tt.r > 0].mean(); r["avg_loss"] = tt.r[tt.r <= 0].mean(); r["hold"] = (tt.xm - tt.em).median()
            rows.append(r)
    a = [x for x in rows if x["cfg"] == name and x["split"] == "ALL"] + [x for x in rows if x["cfg"] == name and x["split"] != "ALL"]
    print(f"{name[:42]:42s} " + " | ".join(f"{x['test'][:2]}/{x['split'][:2]} n{x['trades']} {x['avg']:+.3f} wo{x['avg_wo_best']:+.3f} wd{x['worst_day']:+.1f} t{x['t_vs_parent']:+.1f}" for x in a), flush=True)
import os
sfx = "_ro" if os.environ.get("REPLAY_ONLY") else ""
pd.DataFrame(rows).to_csv(f"res_{sys.argv[2]}{sfx}.csv", index=False, float_format="%.4f")
pd.to_pickle(allt, f"trades_{sys.argv[2]}{sfx}.pkl")
