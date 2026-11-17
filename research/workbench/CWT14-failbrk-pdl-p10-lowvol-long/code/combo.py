"""Layered combos (supervisor standard). Educational only - not financial advice."""
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/code")
from ana import *
SDIST = {"A": .25, "S375": .375, "S45": .45, "S45T15": .45, "S45T10": .45, "S60": .60, "S60T15": .60, "S30T15": .30, "S45MH120": .45, "S45BE": .45}
def bp(t, ex):  # net per $ traded, risk recomputed for the config's stop
    risk = t.fill - (t.close - SDIST[ex] * t.atr_d)
    return t[f"{ex}_r"] * risk / t.fill * 1e4
s = load(); P = pick(s)
c10 = lambda s: cost_ps(s.close) / (0.25 * s.atr_d) <= .10
c08 = lambda s: cost_ps(s.close) / (0.25 * s.atr_d) <= .08
c12 = lambda s: cost_ps(s.close) / (0.25 * s.atr_d) <= .12
adv = lambda s: s.adv20 >= 150e6
g20 = lambda s: s.spy_d950 >= -0.20
gvw = lambda s: s.spy_vw >= 0
grp = lambda s: s.spy_rpos >= 0.3
rc = lambda s: s.reclaim >= .05
gp = lambda s: s.gap < 0
def AND(*f): return lambda s: np.logical_and.reduce([g(s) for g in f])
C = {
 "parent": ({}, "A"),
 "X1 S45T15": ({}, "S45T15"), "X2 S60": ({}, "S60"), "X3 S375": ({}, "S375"), "X4 S45": ({}, "S45"),
 "S45T15+c10": (dict(extra=c10), "S45T15"), "S45T15+c08": (dict(extra=c08), "S45T15"), "S45T15+c12": (dict(extra=c12), "S45T15"),
 "S45T15+c10+g20": (dict(extra=AND(c10, g20)), "S45T15"), "S45T15+c10+gvw": (dict(extra=AND(c10, gvw)), "S45T15"),
 "S45T15+c10+grp": (dict(extra=AND(c10, grp)), "S45T15"),
 "S45T15+c10+adv": (dict(extra=AND(c10, adv)), "S45T15"), "S45T15+c10+rc": (dict(extra=AND(c10, rc)), "S45T15"),
 "S45T15+c10+gp": (dict(extra=AND(c10, gp)), "S45T15"),
 "S45T15+c10+g20+adv": (dict(extra=AND(c10, g20, adv)), "S45T15"), "S45T15+c10+grp+adv": (dict(extra=AND(c10, grp, adv)), "S45T15"),
 "S45T15+c10+g20+e12": (dict(extra=AND(c10, g20), window=(950, 1200)), "S45T15"),
 "S45T15+c10+g20+gp": (dict(extra=AND(c10, g20, gp)), "S45T15"),
 "S60+c10+g20": (dict(extra=AND(c10, g20)), "S60"), "S60+c10+grp": (dict(extra=AND(c10, grp)), "S60"),
 "S45T15+c10+g20+rc": (dict(extra=AND(c10, g20, rc)), "S45T15"),
}
rows = []
for nm, (kw, ex) in C.items():
    t = pick(s, **kw); t = t.assign(R=t[f"{ex}_r"], bp=bp(t, ex))
    for tn, rng in TESTS.items():
        a = period(t, rng); st = stats(a, "R"); pp = paired(a, period(P, rng), "R", "A_r")
        rows.append(dict(cfg=nm, test=tn, **st, bps=a.bp.mean(), d=pp["diff"], t=pp["t"]))
D = pd.DataFrame(rows); D.to_csv(OUT + "combo.csv", index=False)
pd.set_option("display.width", 250)
for tn in ("2y", "replay"):
    print("=====", tn); print(D[D.test == tn].set_index("cfg")[["n", "win", "avg", "wo_best", "worst_day", "bps", "d", "t"]].round(3).to_string())
print(D.pivot(index="cfg", columns="test", values="avg")[["train", "valid"]].round(3).to_string())
print("parent bps check", bp(P, "A").groupby(P.date >= "2026-10-12").mean())
