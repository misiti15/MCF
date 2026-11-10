"""COMPASS-LEARN round 1 (PLAN.md): score the baselines and the 205 pre-registered configs. Usage:
    python study.py <scratch>     (needs panel.parquet from panel.py, hunch_agg.parquet from research/bdi/hc1/hunch_probs.py)
Writes the CSVs next to this file. Educational only - not financial advice."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402

S = Path(sys.argv[1])
P = pd.read_parquet(S / "panel.parquet")
A = pd.read_parquet(S / "hunch_agg.parquet")
A = A[A.scored].copy(); A["T"] = 573 + 3 * A.b
A = A.sort_values(["date", "T"])
pan = E.Panel(P, A[["date", "T", "share_up"]])
PER = ["TRAIN", "VALID", "FWD", "LIVE"]
sub = {k: pan.sub(pan.period == k) for k in PER}
N_CONFIGS = 205
BAR = max(1.5, math.sqrt(2 * math.log(N_CONFIGS)))
print("days", {k: len(v.dates) for k, v in sub.items()}, "bar", round(BAR, 2))


def run(fn):
    """fn(panel) -> (held, R, marks). Returns {period: (metrics, day_scores)}."""
    return {k: E.score(sub[k], *fn(sub[k])) for k in PER}


rows, dayS = [], {}


def add(fam, name, fn, **kw):
    res = run(fn)
    r = dict(family=fam, config=name, **kw)
    for k, (m, ds) in res.items():
        for a, b in m.items():
            r[f"{k}_{a}"] = b
        dayS[(name, k)] = ds
    rows.append(r)
    return r


# ---------------------------------------------------------------------------------------------- baselines
add("BASE", "B-W60", lambda p: E.vote(p, 15, 60, 0.0))
add("BASE", "B-C30", E.c30)
add("BASE", "B-CHK", E.b_chk)

# ---------------------------------------------------------------------------------------------- 1 VOTE (48)
for I in (5, 10, 15, 30):
    for W in (30, 60, 90):
        for th in (0.0, 0.002, 0.003, 0.004):
            add("VOTE", f"VOTE-I{I}-W{W}-t{th * 100:.1f}", lambda p, I=I, W=W, th=th: E.vote(p, I, W, th), I=I, W=W, theta=th)

# ---------------------------------------------------------------------------------------------- 2 CHK (36)
for I in (5, 10, 15, 30):
    for th in (0.002, 0.003, 0.004):
        for W in (None, 30, 60):
            add("CHK", f"CHK-I{I}-t{th * 100:.1f}-P{W or 0}", lambda p, I=I, th=th, W=W: E.chk(p, I, th, W), I=I, theta=th, W=W or 0)

R0 = pd.DataFrame(rows)
best_chk = R0[R0.family == "CHK"].sort_values("TRAIN_S", ascending=False).iloc[0]
bI, bth, bW = int(best_chk.I), float(best_chk.theta), int(best_chk.W) or None
print("best CHK by TRAIN:", best_chk.config)

# ---------------------------------------------------------------------------------------------- 3 ADD-ONE (16)
FN = ["orb15", "orb30", "sector", "br15", "atr", "gap", "prevday", "hunch"]
for f in FN:
    add("ADD1", f"W60+{f}", lambda p, f=f: E.vote(p, 15, 60, 0.0, filt=E.filters(p)[f]), filt=f, base="B-W60")
for f in FN:
    add("ADD1", f"{best_chk.config}+{f}", lambda p, f=f: E.chk(p, bI, bth, bW, filt=E.filters(p)[f]), filt=f,
        base=best_chk.config)

# ---------------------------------------------------------------------------------------------- 4 LOGIT (72)
MODELS = ["base", "sector", "br15", "orb30", "gap", "prevday", "hunch", "qqq_iwm", "all"]
tr = sub["TRAIN"]; y = (tr.eod > 0).astype(float)
coefs = {}
for mdl in MODELS:
    X = E.logit_X(tr, mdl)
    cols = E.mi(np.arange(585, 956, 5))
    Xf = X[:, cols].reshape(-1, X.shape[-1]); yf = np.repeat(y[:, None], len(cols), 1).reshape(-1)
    ok = np.isfinite(Xf).all(1)
    coefs[mdl] = E.fit_logit(Xf[ok], yf[ok])
    for ps in (0.75, 0.80, 0.85, 0.90):
        for I in (5, 15):
            add("LOGIT", f"LOGIT-{mdl}-p{int(ps * 100)}-I{I}",
                lambda p, mdl=mdl, ps=ps, I=I: E.logit_read(E.logit_P(p, mdl, coefs[mdl]), I, ps), model=mdl, pstar=ps, I=I)
pd.DataFrame({m: pd.Series(w) for m, w in coefs.items()}).to_csv(HERE / "logit_coefs.csv")

R = pd.DataFrame(rows)
assert len(R[R.family != "BASE"]) == 48 + 36 + 16 + 72, len(R)

# paired vs B-W60 and plateau
for k in PER:
    b = dayS[("B-W60", k)]
    R[f"{k}_dS"] = [dayS[(c, k)].mean() - b.mean() for c in R.config]
    R[f"{k}_t"] = [E.paired_t(dayS[(c, k)], b) for c in R.config]


def neighbours(r):
    if r.family == "VOTE":
        Is, Ws, Ts = [5, 10, 15, 30], [30, 60, 90], [0.0, 0.002, 0.003, 0.004]
        out = []
        for dim, vals in (("I", Is), ("W", Ws), ("theta", Ts)):
            i = vals.index(r[dim] if dim != "theta" else float(r[dim]))
            for j in (i - 1, i + 1):
                if 0 <= j < len(vals):
                    q = dict(I=int(r.I), W=int(r.W), theta=float(r.theta)); q[dim] = vals[j]
                    out.append(f"VOTE-I{q['I']}-W{q['W']}-t{q['theta'] * 100:.1f}")
        return out
    if r.family == "CHK":
        Is, Ts, Ws = [5, 10, 15, 30], [0.002, 0.003, 0.004], [0, 30, 60]
        out = []
        for dim, vals in (("I", Is), ("theta", Ts), ("W", Ws)):
            i = vals.index(int(r[dim]) if dim != "theta" else float(r[dim]))
            for j in (i - 1, i + 1):
                if 0 <= j < len(vals):
                    q = dict(I=int(r.I), theta=float(r.theta), W=int(r.W)); q[dim] = vals[j]
                    out.append(f"CHK-I{q['I']}-t{q['theta'] * 100:.1f}-P{q['W']}")
        return out
    if r.family == "LOGIT":
        Ps = [0.75, 0.80, 0.85, 0.90]; i = Ps.index(float(r.pstar))
        out = [f"LOGIT-{r.model}-p{int(Ps[j] * 100)}-I{int(r.I)}" for j in (i - 1, i + 1) if 0 <= j < 4]
        out.append(f"LOGIT-{r.model}-p{int(r.pstar * 100)}-I{20 - int(r.I)}")
        return out
    if r.family == "ADD1":
        return [c for c in R.config if c.endswith("+" + r.filt) and c != r.config]
    return []


vd = dict(zip(R.config, R.VALID_dS))
R["nbrs"] = [";".join(neighbours(r)) for _, r in R.iterrows()]
R["plateau"] = [np.mean([vd[c] > 0 for c in n.split(";")]) if n else np.nan for n in R.nbrs]
bp = R.set_index("config").loc["B-W60", "VALID_first_prec"]
R["clearly_better"] = (R.VALID_t >= BAR) & (R.TRAIN_dS > 0) & (R.plateau >= 0.5) & (R.VALID_first_prec >= bp - 0.02)
R.to_csv(HERE / "configs.csv", index=False)
show = ["config", "TRAIN_S", "VALID_S", "VALID_dS", "VALID_t", "TRAIN_dS", "plateau", "VALID_stay", "VALID_cover",
        "VALID_first_med", "VALID_by1030", "VALID_first_prec", "VALID_flips", "VALID_false_flips", "FWD_S", "LIVE_S"]
pd.set_option("display.width", 250)
print(R[R.family == "BASE"][show].round(3).to_string())
print(R.sort_values("VALID_S", ascending=False)[show].head(25).round(3).to_string())
print("clearly better:", R[R.clearly_better].config.tolist())
pd.to_pickle(dayS, S / "dayS.pkl"); pd.to_pickle(coefs, S / "coefs.pkl")
