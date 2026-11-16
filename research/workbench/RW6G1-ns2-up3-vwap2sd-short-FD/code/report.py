"""Side-by-side table + verdicts (owner pass rule 2026-11-16) from res_ROUND*.csv / extras.csv. Educational only - not financial advice."""
import math, pandas as pd
r = pd.concat([pd.read_csv(f"res_ROUND{i}.csv") for i in (1, 2, 3, 4)]).drop_duplicates(["cfg", "test", "split"])
r.to_csv("results_all.csv", index=False, float_format="%.4f")
x = pd.read_csv("extras.csv").drop_duplicates(["cfg", "test"])
WB = {"V04 window start 09:50->11:00 (P6/P7)": "WB1", "V27 close >= VWAP + 0.5 SD at signal (new sensor)": "WB2", "D2 C2 + gap <= +2%": "WB3"}
G = lambda c, t, s="ALL": r[(r.cfg == c) & (r.test == t) & (r.split == s)].iloc[0]
def verdict(c):
    ref = "T0 parent, testing book" if c.startswith("TB-") else "PARENT"
    if c.startswith("T0"):
        return "info (destination book)", "parent re-scored in the Testing book (no latch, cap 50, stop cost <= 0.15R)"
    why = []
    for t in ("replay", "2y"):
        a, p = G(c, t), G(ref, t)
        if pd.isna(a.avg): why.append(f"{t}: no trades"); continue
        if not (a.avg >= p.avg - 0.01 or (p.avg > 0 and a.avg >= 0.95 * p.avg)): why.append(f"{t} avg R {a.avg:+.3f} < {p.avg:+.3f}")
        if a.avg_wo_best < p.avg_wo_best - 0.02: why.append(f"{t} w/o best day {a.avg_wo_best:+.3f} vs {p.avg_wo_best:+.3f}")
        if a.worst_day < p.worst_day * 1.10: why.append(f"{t} worst day {a.worst_day:+.1f}R vs {p.worst_day:+.1f}R (>10% worse)")
    return ("PASS" if not why else "FAIL") + (" vs T0" if ref != "PARENT" else ""), "; ".join(why)
cfgs = [c for c in r.cfg.unique() if c != "PARENT"]
N = len(cfgs)
L = [f"Configs: {N}; counted bar max(1.5, sqrt(2 ln {N})) = {max(1.5, math.sqrt(2 * math.log(N))):.2f}", "",
     "| copy | config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | t vs parent (replay / 2y) | verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for c in ["PARENT"] + cfgs:
    a, b = G(c, "replay"), G(c, "2y")
    v, why = ("—", "") if c == "PARENT" else verdict(c)
    L.append(f"| {WB.get(c, 'parent' if c == 'PARENT' else '')} | {c} | {a.trades} | {a.avg:+.3f} | {a.avg_wo_best:+.3f} | {a.worst_day:+.1f} | {b.trades} | {b.avg:+.3f} | {b.avg_wo_best:+.3f} | {b.worst_day:+.1f} | {a.t_vs_PARENT:+.2f} / {b.t_vs_PARENT:+.2f} | {v}{' — ' + why if why else ''} |")
L += ["", "| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |", "|---|---|---|---|"]
for c in ["PARENT"] + cfgs:
    L.append(f"| {c} | " + " | ".join(f"{G(c, '2y', s).avg:+.3f} ({G(c, '2y', s).trades})" for s in ("TRAIN", "VALID", "FWD")) + " |")
f = lambda v: "" if pd.isna(v) else f"{v:+.3f}"
L += ["", "| config | test | win % | avg win | avg loss | median hold (min) | stop / target / time share | up-day avg R (n) | flat (n) | down (n) |", "|---|---|---|---|---|---|---|---|---|---|"]
for c in ["PARENT"] + cfgs:
    for t in ("replay", "2y"):
        a = G(c, t); e = x[(x.cfg == c) & (x.test == t)].iloc[0]
        L.append(f"| {c} | {t} | {a.win:.0%} | {f(a.avg_win)} | {f(a.avg_loss)} | {a.hold:.0f} | {a.sh_stop:.0%} / {a.sh_target:.0%} / {a.sh_time:.0%} | {f(e.up)} ({e.n_up}) | {f(e.flat)} ({e.n_flat}) | {f(e.down)} ({e.n_down}) |")
open("RESULTS_body.md", "w").write("\n".join(L) + "\n")
for c in cfgs: print(f"{c:52s}", *verdict(c))
