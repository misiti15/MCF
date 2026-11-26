"""PRIMSHORTS-1126: score the lineup options (bench_book.py day files + live_book.py day files) -> options.json.
Per option x LATCH-OPEN x cost x window: avg book R / session (zero-candidate sessions count 0), w/o best day, best-day
share, worst-5 days, red-day %, L3 leg R, lots / session, paired day t vs option a. Educational only - not financial advice."""
import json, math, os, sys
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
NSES = {"FIT": 170, "CHECK": 276, "T2": 427}
OPTS = ["a_keep", "b_L3_out", "c_L3_half", "d_L3_latchopen"]


def summ(d, base, l3, lots, nses):
    d = d.reindex(base.index).fillna(0.0)
    tot = float(d.sum()); best = d.idxmax()
    dd = d - base; se = dd.std(ddof=1) / math.sqrt(len(dd)) if len(dd) > 1 else float("nan")
    pad = nses - len(d)
    return {"avg_day": round(tot / nses, 3), "wo_best_day": round((tot - d.max()) / (nses - 1), 3),
            "best_share": round(float(d.max() / tot), 2) if tot > 0 else None, "worst5": round(float(d.nsmallest(5).sum()), 1),
            "red_pct": round(float((d < 0).sum() / nses * 100), 1), "L3_R": round(float(l3), 1),
            "lots_per_session": round(float(lots) / nses, 1), "total": round(tot, 1),
            "d_vs_a_per_session": round(float(dd.sum()) / nses, 3), "t_vs_a": round(float(dd.mean() / se), 2) if se and se > 0 else None,
            "d_wo_best_day": round(float(dd.sum() - dd.max()) / nses, 3) if len(dd) else None}


res = {"bench": {}, "live": {}}
for cost in ("live", "lr8"):
    for lo in ("BASE", "LO"):
        A = pd.read_parquet(f"{OUT}/book_{cost}_{lo}_a_keep.parquet")
        for opt in OPTS:
            X = pd.read_parquet(f"{OUT}/book_{cost}_{lo}_{opt}.parquet")
            for per in ("FIT", "CHECK", "T2"):
                a = A[A.per == per].set_index("date").R; x = X[X.per == per]
                lots = sum(x[f"N{s}"].sum() for s in range(4) if f"N{s}" in x)
                res["bench"][f"{cost}|{lo}|{opt}|{per}"] = summ(x.set_index("date").R, a, x["R0"].sum() if "R0" in x else 0, lots, NSES[per])
L = pd.read_csv(H + "/live_book_days_lineup.csv")
L3 = "S|L3-gap-slope-fromopen-FD"
for lo in (False, True):
    a = L[(L.lo == lo) & (L.opt == "a_keep")].set_index("date").R
    for opt in OPTS:
        x = L[(L.lo == lo) & (L.opt == opt)]
        res["live"][f"{'LO' if lo else 'BASE'}|{opt}"] = summ(x.set_index("date").R, a, x[L3].sum() if L3 in x else 0, x.lots.sum(), len(a))
json.dump(res, open(H + "/options.json", "w"), indent=1)
rows = []
for k, v in res["bench"].items():
    c, lo, o, p = k.split("|")
    rows.append([c, lo, o, p, v["avg_day"], v["wo_best_day"], v["worst5"], v["red_pct"], v["L3_R"], v["lots_per_session"], v["d_vs_a_per_session"], v["t_vs_a"]])
for k, v in res["live"].items():
    lo, o = k.split("|")
    rows.append(["actual", lo, o, "LIVE18", v["avg_day"], v["wo_best_day"], v["worst5"], v["red_pct"], v["L3_R"], v["lots_per_session"], v["d_vs_a_per_session"], v["t_vs_a"]])
pd.set_option("display.width", 250)
print(pd.DataFrame(rows, columns=["cost", "LO", "opt", "per", "avg_day", "woBest", "worst5", "red%", "L3_R", "lots/s", "d_vs_a", "t_vs_a"]).to_string(index=False))
