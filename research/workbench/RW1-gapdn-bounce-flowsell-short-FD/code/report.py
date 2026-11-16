"""RW1-FD Mechanic: merge res_ROUND1..3 -> results.csv + extras.csv (shape, SPY day-type split) + RESULTS_body.md tables with
the owner's pass rule (2026-11-16: meets or exceeds the parent's avg R in BOTH tests - meets = within 0.01R or >= 95% -, and
not worse on avg R w/o best day by > 0.02R or on worst day by > 10%). Educational only - not financial advice."""
import math, pandas as pd, numpy as np
R = pd.concat([pd.read_csv(f"res_ROUND{i}.csv") for i in (1, 2, 3)]).drop_duplicates(["cfg", "test", "split"])
R.to_csv("results.csv", index=False, float_format="%.4f")
T = {}
for i in (1, 2, 3):
    for k, v in pd.read_pickle(f"trades_ROUND{i}.pkl").items():
        T.setdefault(k, v)
s = pd.read_parquet("spy1m.parquet"); s.index = pd.DatetimeIndex(pd.to_datetime(s.index, utc=True)).tz_convert("America/New_York")
s = s[(s.index.hour * 60 + s.index.minute >= 570) & (s.index.hour * 60 + s.index.minute < 960)]
g = s.groupby(s.index.strftime("%Y-%m-%d")); oc = (g.close.last() / g.open.first() - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "flat")), index=oc.index)
X = []
for c, o in T.items():
    for test, t in o.items():
        e = dict(cfg=c, test=test, avg_win=t.r[t.r > 0].mean(), avg_loss=t.r[t.r <= 0].mean(), hold=(t.xm - t.em).median(),
                 stop=(t.kind == "stop").mean(), tgt=(t.kind == "target").mean(), time=(t.kind == "time").mean())
        dt = t.date.map(dtype)
        for k in ("up", "flat", "down"):
            e[k] = t.r[dt == k].mean(); e["n_" + k] = int((dt == k).sum())
        X.append(e)
X = pd.DataFrame(X); X.to_csv("extras.csv", index=False, float_format="%.4f")
P = {t: R[(R.cfg == "PARENT") & (R.test == t) & (R.split == "ALL")].iloc[0] for t in ("replay", "2y")}
def verdict(c):
    why = []
    for t in ("replay", "2y"):
        a = R[(R.cfg == c) & (R.test == t) & (R.split == "ALL")].iloc[0]; p = P[t]
        if not (a.avg >= p.avg - 0.01 or (p.avg > 0 and a.avg >= 0.95 * p.avg)): why.append(f"{t} avg R {a.avg:+.3f} < parent {p.avg:+.3f}")
        if a.avg_wo_best < p.avg_wo_best - 0.02: why.append(f"{t} w/o best day {a.avg_wo_best:+.3f} vs {p.avg_wo_best:+.3f}")
        if a.worst_day < p.worst_day * 1.10: why.append(f"{t} worst day {a.worst_day:+.1f} vs {p.worst_day:+.1f}R")
    return ("PASS" if not why else "FAIL — " + "; ".join(why))
WB = {"V05 window end 15:00->13:00 (P6)": "WB1", "V13 RSI(14) 55-60 (P11 hi)": "WB2", "D8 C5 + SPY gate 0.20 (sibling)": "WB3"}
order = list(dict.fromkeys(R.cfg))
N = len(order) - 1
L = [f"Configurations: {N} (parent excluded); configs-counted bar max(1.5, sqrt(2 ln {N})) = {max(1.5, math.sqrt(2 * math.log(N))):.2f}", "",
     "| copy | config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | t vs parent (replay / 2y) | verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for c in order:
    a, b = (R[(R.cfg == c) & (R.test == t) & (R.split == "ALL")].iloc[0] for t in ("replay", "2y"))
    L.append(f"| {WB.get(c, 'parent' if c == 'PARENT' else '')} | {c} | {a.trades} | {a.avg:+.3f} | {a.avg_wo_best:+.3f} | {a.worst_day:+.1f} | {b.trades} | "
             f"{b.avg:+.3f} | {b.avg_wo_best:+.3f} | {b.worst_day:+.1f} | {a.t_vs_PARENT:+.2f} / {b.t_vs_PARENT:+.2f} | {'—' if c == 'PARENT' else verdict(c)} |")
L += ["", "| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |", "|---|---|---|---|"]
for c in order:
    q = {sp: R[(R.cfg == c) & (R.test == "2y") & (R.split == sp)].iloc[0] for sp in ("TRAIN", "VALID", "FWD")}
    L.append(f"| {c} | " + " | ".join(f"{q[k].avg:+.3f} ({q[k].trades})" for k in q) + " |")
L += ["", "| config | test | avg win | avg loss | median hold (min) | stop | target | time | up-day avg R (n) | flat (n) | down (n) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for c in ["PARENT"] + list(WB) + ["C5 C1 + end 13:00"]:
    for t in ("replay", "2y"):
        e = X[(X.cfg == c) & (X.test == t)].iloc[0]
        L.append(f"| {c} | {t} | {e.avg_win:+.3f} | {e.avg_loss:+.3f} | {e.hold:.0f} | {e.stop:.0%} | {e.tgt:.0%} | {e.time:.0%} | "
                 + " | ".join(f"{e[k]:+.3f} ({e['n_' + k]})" for k in ("up", "flat", "down")) + " |")
open("RESULTS_body.md", "w").write("\n".join(L) + "\n")
for c in order[1:]:
    print(f"{c:52s}", verdict(c))
