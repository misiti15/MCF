"""COMPASS-5M (PLAN.md): do 5-/10-min rolling states between the 15-min marks say anything about SPY's next 5..90 min,
or about the close-vs-open side earlier / better than the 15-min W60? Usage:
    python study.py <scratch>     (needs <scratch>/panel.parquet from research/compass_learn/panel.py)
Writes horizons.csv and side.csv next to this file. Educational only - not financial advice."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "compass_learn"))
import engine as E  # noqa: E402

S = Path(sys.argv[1])
P = pd.read_parquet(S / "panel.parquet")
pan = E.Panel(P)
PER = ["TRAIN", "VALID", "FWD", "LIVE"]
N_TESTS = 10 * 7 * 2 + 2
BAR = max(1.5, math.sqrt(2 * math.log(N_TESTS)))
HS = [5, 10, 15, 30, 45, 60, 90]
MK = list(E.MARKS)


def glue(p, I):
    """W60 recomputed every I min; persistence = the 15-min marks of the last 60 min + the current reading."""
    marks = list(range(585, 956, I)) if I == 5 else list(range(590, 956, 10))
    cols = E.mi(marks)
    s, v1, v2, v3 = E.base_votes(p, cols)
    s15 = E.sgn(p.m["fo"])                                   # sign at every 5-min mark
    R = np.zeros_like(s)
    for j, T in enumerate(marks):
        m15 = [t for t in range(585, 956, 15) if T - 60 < t <= T]
        js = E.mi(m15 + ([T] if T not in m15 else []))
        w = s15[:, js]
        same = np.all(w == w[:, [-1]], axis=1) & (w[:, -1] != 0)
        pw = np.where(same, w[:, -1], 0)
        v = s[:, j] + v1[:, j] + v2[:, j] + v3[:, j] + pw
        ok = len(js) >= 2
        R[:, j] = np.where((v >= 4) & (pw == 1) & ok, 1, np.where((v <= -4) & (pw == -1) & ok, -1, 0))
    return E.hold(R, marks), R, marks


def ret(x, k):
    """return over the last k 5-min marks from a from-open matrix (open used before the first mark)."""
    y = 1 + np.nan_to_num(x)
    prev = np.concatenate([np.ones((y.shape[0], k)), y[:, :-k]], 1)
    return y / prev - 1


def thr(r, t):
    return np.where(r >= t, 1, np.where(r <= -t, -1, 0))


def tilt(p, k, db):
    a, b, c = (np.sign(ret(p.m[x], k)) for x in ("fo", "qfo", "ifo"))
    br = np.nan_to_num(p.m["br"], nan=0.5)
    d = br - np.concatenate([np.full((br.shape[0], k), 0.5), br[:, :-k]], 1)
    s = np.where((a == b) & (b == c), a, 0)
    return np.where((s > 0) & (d >= db), 1, np.where((s < 0) & (d <= -db), -1, 0))


def states(p):
    return {
        "S1 W60": E.vote(p, 15, 60, 0.0)[0],
        "S2 GLUE5": glue(p, 5)[0],
        "S3 GLUE10": glue(p, 10)[0],
        "S4 CHK15": E.chk(p, 15, 0.002, None)[0],
        "S5 MOM5": thr(ret(p.m["fo"], 1), 0.0005),
        "S6 MOM15": thr(ret(p.m["fo"], 3), 0.0010),
        "S7 MOM30": thr(ret(p.m["fo"], 6), 0.0015),
        "S8 TILT5": tilt(p, 1, 0.02),
        "S9 VWAP": thr(np.nan_to_num(p.m["vw"]), 0.0010),
        "S10 TILT10": tilt(p, 2, 0.03),
    }


def tstat(day_sum):
    d = np.asarray(day_sum, float)
    return d.mean() / (d.std(ddof=1) / math.sqrt(len(d))) if len(d) > 2 and d.std(ddof=1) > 0 else np.nan


def horizon_rows(p, per):
    px = p.m["px"]; out = []
    for name, H in states(p).items():
        for h in HS:
            k = h // 5
            js = [j for j, T in enumerate(MK) if 600 <= T <= 955 - h]
            st = H[:, js]; fut = px[:, [j + k for j in js]] / px[:, js] - 1
            ok = np.isfinite(fut) & (fut != 0)
            mv = np.sign(fut)
            for tgt in ("dir", "size"):
                ev = (mv == 1) if tgt == "dir" else (fut >= 0.001)
                ed = (mv == -1) if tgt == "dir" else (fut <= -0.001)
                bu, bd = ev[ok].mean(), ed[ok].mean()
                fire = ok & (st != 0)
                hit = np.where(st > 0, ev, ed)
                base = np.where(st > 0, bu, bd)
                exc = np.where(fire, hit - base, 0.0)
                n = int(fire.sum())
                anti = np.where(st > 0, ed, ev); abase = np.where(st > 0, bd, bu)     # diagnostic: move AGAINST the call
                out.append(dict(state=name, h=h, target=tgt, period=per, days=len(p.dates), n=n,
                                coverage=n / max(ok.sum(), 1), hit=hit[fire].mean() if n else np.nan,
                                base=base[fire].mean() if n else np.nan,
                                excess=exc.sum() / max(n, 1), t=tstat(exc.sum(1)),
                                against=anti[fire].mean() if n else np.nan,
                                against_base=abase[fire].mean() if n else np.nan))
    return out


rows = []
sub = {k: pan.sub(pan.period == k) for k in PER}
for k in PER:
    rows += horizon_rows(sub[k], k)
H = pd.DataFrame(rows)
H.to_csv(HERE / "horizons.csv", index=False, float_format="%.4f")

# rest-of-day side: GLUE5 / GLUE10 vs W60 (score S of COMPASS-LEARN)
side = []
for k in PER:
    p = sub[k]
    b, bs = E.score(p, *E.vote(p, 15, 60, 0.0))
    for name, fn in (("S1 W60", lambda p: E.vote(p, 15, 60, 0.0)), ("S2 GLUE5", lambda p: glue(p, 5)),
                     ("S3 GLUE10", lambda p: glue(p, 10))):
        m, ds = E.score(p, *fn(p))
        side.append(dict(state=name, period=k, S=m["S"], dS=ds.mean() - bs.mean(), t=E.paired_t(ds, bs),
                         stay=m["stay"], cover=m["cover"], first_med=m["first_med"], by1000=m["by1000"],
                         first_prec=m["first_prec"], flips=m["flips"], false_flips=m["false_flips"]))
SD = pd.DataFrame(side)
SD.to_csv(HERE / "side.csv", index=False, float_format="%.4f")
print("tests", N_TESTS, "bar", round(BAR, 2))
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
print(SD.round(3).to_string(index=False))
W = H.pivot_table(index=["state", "target", "h"], columns="period", values=["hit", "base", "t", "coverage"])
print(W.round(3).to_string())
V = H[H.period == "VALID"].copy()
tr = H[H.period == "TRAIN"].set_index(["state", "h", "target"]); fw = H[H.period == "FWD"].set_index(["state", "h", "target"])
V["tr_t"] = [tr.loc[(r.state, r.h, r.target), "t"] for r in V.itertuples()]
V["fwd_ex"] = [fw.loc[(r.state, r.h, r.target), "excess"] for r in V.itertuples()]
V["works"] = ((V.t.abs() >= BAR) & (np.sign(V.tr_t) == np.sign(V.t)) & (V.tr_t.abs() >= 1.5)
              & (np.sign(V.fwd_ex) == np.sign(V.t))
              & (((V.target == "dir") & ((V.hit >= 0.55) | (V.hit <= 0.45))) | ((V.target == "size") & (V.excess.abs() >= 0.05))))
print("passes:", V[V.works][["state", "h", "target", "hit", "base", "against", "against_base", "t", "tr_t", "fwd_ex"]].to_string(index=False))
print("max |t| VALID", V.loc[V.t.abs().idxmax(), ["state", "h", "target", "hit", "base", "t"]].to_dict())
