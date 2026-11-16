"""All-configs table + verdicts for L3-gap-slope-rsi5hi-FD (Mechanic 2026-11-16). Educational only - not financial advice."""
import math, pandas as pd
r = pd.concat([pd.read_csv(f"res_ROUND{i}.csv") for i in (1, 2, 3, 4)]).drop_duplicates(["cfg", "test", "split"])
r.to_csv("results_all.csv", index=False, float_format="%.4f")
P = {t: r[(r.cfg == "PARENT") & (r.test == t) & (r.split == "ALL")].iloc[0] for t in ("replay", "2y")}
def verdict(c):
    why = []
    for t in ("replay", "2y"):
        a = r[(r.cfg == c) & (r.test == t) & (r.split == "ALL")].iloc[0]; p = P[t]
        meets = a.avg >= p.avg - 0.01 or (p.avg > 0 and a.avg >= 0.95 * p.avg)
        if not meets: why.append(f"{t} avg R {a.avg:+.3f} < parent {p.avg:+.3f}")
        if a.avg_wo_best < p.avg_wo_best - 0.02: why.append(f"{t} w/o best day {a.avg_wo_best:+.3f} vs {p.avg_wo_best:+.3f}")
        if a.worst_day < p.worst_day * 1.10: why.append(f"{t} worst day {a.worst_day:+.1f}R vs {p.worst_day:+.1f}R")
    return ("PASS" if not why else "FAIL"), "; ".join(why)
cfgs = [c for c in r.cfg.unique() if c != "PARENT"]
N = len(cfgs); bar = max(1.5, math.sqrt(2 * math.log(N)))
L = [f"Configs counted: {N} (PARENT excluded; X10 re-run in round 4 counted once). Paired-by-day t bar max(1.5, sqrt(2 ln {N})) = {bar:.2f}.", "",
     "| config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | TRAIN | VALID | FWD | t vs parent (replay / 2y) | verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for c in ["PARENT"] + cfgs:
    a = r[(r.cfg == c) & (r.test == "replay") & (r.split == "ALL")].iloc[0]; b = r[(r.cfg == c) & (r.test == "2y") & (r.split == "ALL")].iloc[0]
    s = {sp: r[(r.cfg == c) & (r.test == "2y") & (r.split == sp)].iloc[0].avg for sp in ("TRAIN", "VALID", "FWD")}
    v, why = ("—", "") if c == "PARENT" else verdict(c)
    L.append(f"| {c} | {a.trades} | {a.avg:+.3f} | {a.avg_wo_best:+.3f} | {a.worst_day:+.1f} | {b.trades} | {b.avg:+.3f} | {b.avg_wo_best:+.3f} | {b.worst_day:+.1f} | "
             f"{s['TRAIN']:+.3f} | {s['VALID']:+.3f} | {s['FWD']:+.3f} | {a.t_vs_parent:+.2f} / {b.t_vs_parent:+.2f} | {v}{(': ' + why) if why else ''} |")
open("alltable.md", "w").write("\n".join(L) + "\n")
print(sum(verdict(c)[0] == "PASS" for c in cfgs), "pass of", N)
for c in cfgs:
    v = verdict(c)
    if v[0] == "PASS": print("PASS", c)
