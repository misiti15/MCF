"""FREQ screen: parent + every config in a JSON list on BOTH tests (replay 2026-10-19..11-16, 21 sessions; 2-year
2024-10..2026-10-16 open months, 433 sessions), pass rule of this job applied. Usage: python exp.py e1.json out.csv
Educational only - not financial advice."""
import sys, json
from sim2 import *
D = load()
def pr(row, base):
    ok = row["tps"] >= 1.25 * base["tps"] and row["total"] >= base["total"] and row["avg"] >= base["avg"] - 0.03 \
         and row["wobest"] >= base["wobest"] - 0.03 and row["worst"] >= base["worst"] * 1.10
    return ok
def norm(v):
    v = dict(v)
    for k in ("univ", "excl"):
        if k in v: v[k] = tuple(v[k])
    if "extra" in v: v["extra"] = tuple(tuple(e) for e in v["extra"])
    return v
if __name__ == "__main__":
    cfgs = json.load(open(sys.argv[1])); rows = []; base = {}
    for name, v in [("parent", {})] + list(cfgs.items()):
        res = {}
        for test, (C, P, days) in D.items():
            t = trades(C, P, norm(v)); s = stats(t, len(days)); res[test] = s
            if name == "parent": base[test] = s
        ok = all(pr(res[k], base[k]) for k in res) if name != "parent" else None
        hs = all(res[k]["avg"] >= base[k]["avg"] and res[k]["wobest"] >= base[k]["wobest"] - 0.02 and res[k]["worst"] >= base[k]["worst"] * 1.1 for k in res) if name != "parent" else None
        row = dict(cfg=name, freq_pass=ok, success_pass=hs)
        for k in ("rep", "y2"):
            for f, x in res[k].items(): row[f"{k}_{f}"] = x
        rows.append(row)
        print(name, ok, hs, "| rep", {f: res["rep"].get(f) for f in ("n", "tps", "avg", "wobest", "total", "worst", "win")},
              "| 2y", {f: res["y2"].get(f) for f in ("n", "tps", "avg", "wobest", "total", "worst", "win")}, flush=True)
    pd.DataFrame(rows).to_csv(sys.argv[2], index=False)
