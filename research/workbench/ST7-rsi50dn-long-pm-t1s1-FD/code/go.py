import sys, importlib, pandas as pd
from load import run, DAYS, split
import sim
decl = importlib.import_module(sys.argv[1]); cfgs = getattr(decl, sys.argv[2])
rows, base, allt = [], {}, {}
for name, v in cfgs.items():
    o = run(v); allt[name] = o
    for test, t in o.items():
        if name == "PARENT": base[test] = t
        for sp in (["ALL"] + (["TRAIN", "VALID"] if test == "2y" else [])):
            tt = t if sp == "ALL" else t[t.split == sp]
            dd = [d for d in DAYS[test] if sp == "ALL" or split(d) == sp]
            r = dict(cfg=name, test=test, split=sp, **sim.stats(tt))
            b = base[test] if sp == "ALL" else base[test][base[test].split == sp]
            r["t_vs_parent"], r["dR_vs_parent"] = sim.paired_t(b, tt, dd)
            r["avg_win"] = tt.r[tt.r > 0].mean(); r["avg_loss"] = tt.r[tt.r <= 0].mean(); r["hold"] = (tt.xm - tt.em).median()
            r["stop_share"] = (tt.kind.isin(["stop", "be"])).mean(); r["tgt_share"] = (tt.kind == "target").mean()
            for k in ("up", "flat", "down"): r[k] = tt.r[tt.dt == k].mean()
            rows.append(r)
    a = [x for x in rows if x["cfg"] == name and x["split"] == "ALL"]
    print(f"{name[:44]:44s} " + " | ".join(f"{x['test']} n{x['trades']} {x['avg']:+.3f} wo{x['avg_wo_best']:+.3f} wd{x['worst_day']:+.1f} t{x['t_vs_parent']:+.1f} u/f/d {x['up']:+.2f}/{x['flat']:+.2f}/{x['down']:+.2f}" for x in a), flush=True)
pd.DataFrame(rows).to_csv(f"/dev/shm/mech-st7/res_{sys.argv[2]}.csv", index=False, float_format="%.4f")
pd.to_pickle(allt, f"/dev/shm/mech-st7/trades_{sys.argv[2]}.pkl")
