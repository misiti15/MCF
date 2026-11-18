"""L3-AM (L3AM_PLAN.md): parent vs entries 09:50-13:00, -2R latch, same engine / book / costs. 1 configuration.
Run from the data folder with load4.py / sim4.py / live.py importable. Educational only - not financial advice."""
import math
import numpy as np, pandas as pd
import load4 as L, sim4
from live import T, replay, stats as lstats

assert not L.C.date.between(*L.LOCK).any()
BAR = max(1.5, math.sqrt(2 * math.log(44)))
CFG = {"PARENT 09:50-15:00": (950, 1500), "AM 09:50-13:00": (950, 1300)}
rows, books = [], {}
for test, (c, g) in L.TESTS.items():
    days = L.DAYS[test]
    for name, w in CFG.items():
        v = dict(sim4.P, w=w)
        books[(test, name)] = sim4.book(sim4.trades(c, v, g), v, -2.0)
    base = books[(test, "PARENT 09:50-15:00")]
    for name in CFG:
        b = books[(test, name)]
        segs = [("ALL", b, base, days)]
        if test == "2y":
            for sp in ("TRAIN", "VALID", "FWD"):
                segs.append((sp, b[b.date.map(L.split) == sp], base[base.date.map(L.split) == sp],
                             [d for d in days if L.split(d) == sp]))
        for seg, bb, bs, dd in segs:
            t, dr = sim4.paired_t(bs, bb, dd)
            rows.append(dict(test=test, seg=seg, cfg=name, sessions=len(dd), **sim4.stats(bb, dd), t_vs_parent=t, dR_vs_parent=dr))
# live: -2R latch replay over Primary + On Deck, then AM keeps entries at or before 13:00 (later entries never change
# an earlier latch state, so the AM book is the parent's AM subset)
m = replay(T, -2.0)
for name, w in CFG.items():
    x = T[m & (T.tod <= w[1])]
    for acct_sel in (["Primary"], ["Primary", "On Deck"]):
        xx = x[x.acct.isin(acct_sel)]
        rows.append(dict(test="live " + "+".join(acct_sel), seg="ALL", cfg=name, **lstats(xx)))
df = pd.DataFrame(rows)
df.to_csv("L3AM.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print(df[["test", "seg", "cfg", "trades", "avg", "total", "avg_wo_best", "total_wo_best", "best_share", "worst_day",
          "t_vs_parent", "dR_vs_parent"]].round(4).to_string())

V = df[(df.test == "2y") & (df.seg == "VALID")].set_index("cfg")
p, a = V.loc["PARENT 09:50-15:00"], V.loc["AM 09:50-13:00"]
Lv = df[df.test == "live Primary+On Deck"].set_index("cfg")
lp, la = Lv.loc["PARENT 09:50-15:00"], Lv.loc["AM 09:50-13:00"]
checks = {"1 VALID avg R >= parent": a.avg >= p.avg, "2 VALID total R >= parent": a.total >= p.total,
          "3 VALID avg R w/o best day > parent": a.avg_wo_best > p.avg_wo_best,
          f"4 VALID day-paired t >= {BAR:.2f}": a.t_vs_parent >= BAR,
          "live avg R >= parent": la.avg >= lp.avg, "live total R w/o best day >= parent": la.total_wo_best >= lp.total_wo_best}
for k, ok in checks.items():
    print(("PASS " if ok else "FAIL ") + k)
print("VERDICT:", "PASS" if all(checks.values()) else "FAIL")
