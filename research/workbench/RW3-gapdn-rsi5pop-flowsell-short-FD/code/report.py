"""Side-by-side table + verdicts (owner pass rule 2026-11-16) from results.csv / extras.csv. Educational only - not financial advice."""
import math, pandas as pd
r = pd.read_csv("results.csv"); x = pd.read_csv("extras.csv").drop_duplicates(["cfg", "test"])
P = {t: r[(r.cfg == "PARENT") & (r.test == t) & (r.split == "ALL")].iloc[0] for t in ("replay", "2y")}
WB = {"V02 window start 09:50->10:30 (P6/P7)": "WB1", "V06 +skip SPY >+0.20% since 09:50 (new gate)": "WB2", "D1 SPY gate + start 10:30 + 1R >= 0.40%": "WB3"}
T0 = {t: r[(r.cfg == "T0 parent, testing book") & (r.test == t) & (r.split == "ALL")].iloc[0] for t in ("replay", "2y")}
def verdict(c):
    if c.startswith("T0"):
        return "info (destination book)", "parent re-scored in the testing-account book"
    why = []
    for t in ("replay", "2y"):
        a = r[(r.cfg == c) & (r.test == t) & (r.split == "ALL")].iloc[0]; p = (T0 if c.startswith("T") else P)[t]
        if not (a.avg >= p.avg - 0.01 or (p.avg > 0 and a.avg >= 0.95 * p.avg)): why.append(f"{t} avg R {a.avg:+.3f} < parent {p.avg:+.3f}")
        if a.avg_wo_best < p.avg_wo_best - 0.02: why.append(f"{t} w/o best day {a.avg_wo_best:+.3f} vs {p.avg_wo_best:+.3f}")
        if a.worst_day < p.worst_day * 1.10: why.append(f"{t} worst day {a.worst_day:+.1f}R vs {p.worst_day:+.1f}R (>10% worse)")
    return ("PASS" if not why else "FAIL") + (" vs T0" if c.startswith("T") else ""), "; ".join(why)
N = r.cfg.nunique() - 1
L = [f"Configs: {N}; counted bar max(1.5, sqrt(2 ln {N})) = {max(1.5, math.sqrt(2 * math.log(N))):.2f}", "",
     "| copy | config | test | trades | win % | avg R | avg R w/o best day | total R | worst day | t vs parent (day-paired) | dR vs parent | verdict / why |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
order = ["PARENT"] + [c for c in r.cfg.unique() if c != "PARENT"]
for c in order:
    v, why = ("—", "") if c == "PARENT" else verdict(c)
    for t in ("replay", "2y"):
        a = r[(r.cfg == c) & (r.test == t) & (r.split == "ALL")].iloc[0]
        L.append(f"| {WB.get(c, 'parent' if c == 'PARENT' else '')} | {c} | {t} | {a.trades} | {a.win:.1%} | {a.avg:+.3f} | {a.avg_wo_best:+.3f} | {a.total:+.1f} | "
                 f"{a.worst_day:+.1f} | {a.t_vs_PARENT:+.2f} | {a.dR_vs_PARENT:+.1f} | {v if t == 'replay' else why} |")
L += ["", "| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |", "|---|---|---|---|"]
for c in order:
    s = {sp: r[(r.cfg == c) & (r.test == "2y") & (r.split == sp)].iloc[0] for sp in ("TRAIN", "VALID", "FWD")}
    L.append(f"| {c} | " + " | ".join(f"{s[k].avg:+.3f} ({s[k].trades})" for k in s) + " |")
L += ["", "| config | test | avg win | avg loss | median hold | stop share | target share | time share | up-day avg R | flat | down |", "|---|---|---|---|---|---|---|---|---|---|---|"]
f = lambda v: "" if pd.isna(v) else f"{v:+.3f}"
for c in order:
    for t in ("replay", "2y"):
        e = x[(x.cfg == c) & (x.test == t)].iloc[0]
        L.append(f"| {c} | {t} | {e.avg_win:+.3f} | {e.avg_loss:+.3f} | {e.hold:.0f} | {e.stop:.0%} | {e.tgt:.0%} | {e.time:.0%} | {f(e.get('up'))} | {f(e.get('flat'))} | {f(e.get('down'))} |")
open("RESULTS_body.md", "w").write("\n".join(L) + "\n")
for c in order[1:]: print(f"{c:45s}", *verdict(c))
