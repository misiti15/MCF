"""python go.py <decl module> <ROUND>: score every config of the round on both tests (identical pipeline) -> res_<ROUND>.csv."""
import sys, importlib
from load import *
import sim_mf2 as S
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
            r = dict(cfg=name, test=test, split=sp, **S.stats(tt), per_day=tt.r.sum() / len(dd))
            b = base.get(test)
            if b is not None:
                bb = b if sp == "ALL" else b[b.split == sp]
                r["t_vs_PARENT"], r["dR_vs_PARENT"] = S.paired_t(bb, tt, dd)
            r["avg_native"] = tt.r_native.mean() if len(tt) else float("nan")
            r["avg_win"] = tt.r[tt.r > 0].mean(); r["avg_loss"] = tt.r[tt.r <= 0].mean(); r["hold"] = (tt.xm - tt.em).median()
            rows.append(r)
    a = [x for x in rows if x["cfg"] == name]
    print(f"{name:44s} " + " | ".join(f"{x['test']}/{x['split']} n{x['trades']} {x['avg']:+.3f} wo{x['avg_wo_best']:+.3f} wd{x['worst_day']:+.1f} t{x.get('t_vs_PARENT', 0):+.2f}" for x in a), flush=True)
pd.DataFrame(rows).to_csv(f"res_{sys.argv[2]}.csv", index=False, float_format="%.4f")
pd.to_pickle(allt, f"trades_{sys.argv[2]}.pkl")
