import math, pandas as pd, numpy as np, sys
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
r = pd.concat([pd.read_csv(f"res_{i}.csv") for i in ("ROUND1", "ROUND2", "ROUND3", "ROUND4", "BOOK")]).drop_duplicates(["cfg", "test", "split"])
T = {}
for i in ("ROUND1", "ROUND2", "ROUND3", "ROUND4", "BOOK"): T.update(pd.read_pickle(f"trades_{i}.pkl"))
A = r[r.split == "ALL"].set_index(["cfg", "test"])
P = {t: A.loc[("PARENT", t)] for t in ("replay", "2y")}
def verdict(c):
    why = []
    for t in ("replay", "2y"):
        a = A.loc[(c, t)]; p = P[t]
        meets = a.avg >= p.avg - 0.01 or (p.avg > 0 and a.avg >= 0.95 * p.avg)
        if not meets: why.append(f"{t} avg R {a.avg:+.3f} < parent {p.avg:+.3f}")
        if a.avg_wo_best < p.avg_wo_best - 0.02: why.append(f"{t} w/o best day {a.avg_wo_best:+.3f} vs {p.avg_wo_best:+.3f}")
        if a.worst_day < p.worst_day * 1.10: why.append(f"{t} worst day {a.worst_day:+.1f}R vs {p.worst_day:+.1f}R")
    return ("PASS" if not why else "FAIL"), "; ".join(why)
cfgs = list(dict.fromkeys(r.cfg))
N = len(cfgs) - 1
L = [f"| config | replay n | replay avg R | replay w/o best | replay worst day | 2y n | 2y avg R | 2y w/o best | 2y worst day | 2y TRAIN / VALID / FWD | t vs parent (replay / 2y) | verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
S = r.set_index(["cfg", "test", "split"])
for c in cfgs:
    a, b = A.loc[(c, "replay")], A.loc[(c, "2y")]
    sp = " / ".join(f"{S.loc[(c, '2y', s)].avg:+.3f}" for s in ("TRAIN", "VALID", "FWD"))
    v, why = ("—", "") if c == "PARENT" else verdict(c)
    L.append(f"| {c} | {a.trades:.0f} | {a.avg:+.3f} | {a.avg_wo_best:+.3f} | {a.worst_day:+.1f} | {b.trades:.0f} | {b.avg:+.3f} | {b.avg_wo_best:+.3f} | {b.worst_day:+.1f} | {sp} | "
             + ("" if c == "PARENT" else f"{a.t_vs_PARENT:+.2f} / {b.t_vs_PARENT:+.2f}") + f" | {v}{(': ' + why) if why else ''} |")
open("alltable.md", "w").write("\n".join(L) + "\n")
print(f"N={N} bar={max(1.5, math.sqrt(2*math.log(N))):.2f}")
# shape + day type + ex-April
d = lib.daily(); d = d[d.symbol == "SPY"].copy(); d["date"] = d.date.astype(str)
oc = (d.set_index("date").close / d.set_index("date").open - 1) * 100
typ = lambda x: "up" if x > 0.25 else ("down" if x < -0.25 else "flat")
key = {"PARENT": "parent", "V07 dist_lod lo 0.782->0.82 (P11)": "WB1", "V14 max hold 75 min (P26)": "WB2", "V12 rsi5 >= 50 (new layer)": "WB3", "R08 hold 75 + rsi5>=50 + dist lo 0.82": "WB4"}
rows = []
for c, nm in key.items():
    for t in ("replay", "2y"):
        x = T[c][t].copy(); x["hold"] = x.xm - x.em
        e = dict(copy=nm, test=t, avg_win=x.r[x.r > 0].mean(), avg_loss=x.r[x.r <= 0].mean(), hold=x.hold.median(),
                 stop=(x.kind == "stop").mean(), target=(x.kind == "target").mean(), time=(x.kind == "time").mean(),
                 best_share=A.loc[(c, t)].best_share, per_day=A.loc[(c, t)].per_day)
        if t == "2y":
            x["dt"] = x.date.map(oc).map(lambda v: typ(v) if pd.notna(v) else "na")
            for k in ("up", "flat", "down"): e[k] = x.r[x.dt == k].mean()
            y = x[~x.date.between("2025-04-01", "2025-04-30")]; e["exApr25"] = y.r.mean(); e["exApr25_n"] = len(y)
        else:
            e["ex1112"] = x[x.date != "2026-11-12"].r.mean()
        rows.append(e)
X = pd.DataFrame(rows); X.to_csv("shape.csv", index=False, float_format="%.4f"); print(X.round(3).to_string())
for c in cfgs[1:]:
    v, why = verdict(c); print(f"{c[:50]:50s} {v} {why}")
