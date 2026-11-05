"""HC1 (PLAN.md): does Hunch breadth add lift to the 30-min GATE1 compass for 'staying' / 'heading'?
Usage: python hc1.py <scratch> <guesses_2026-11-05.csv>. Needs <scratch>/hunch_agg.parquet (hunch_probs.py),
<scratch>/compass15.parquet (comp15.py), <scratch>/live_1105_bars.parquet (state15.py). Educational only."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
S = Path(sys.argv[1])
CPS = list(range(600, 901, 30))
rng = np.random.default_rng(0)

# --- Hunch aggregates per bar (replay) + live 11-05 from the shadow's guesses
A = pd.read_parquet(S / "hunch_agg.parquet")
A = A[A.scored].copy()
gz = pd.read_csv(sys.argv[2])
lv = gz.groupby("b").agg(n=("p_pooled", "size"), share_up=("p_pooled", lambda p: (p > 0.5).mean()), mean_p=("p_pooled", "mean")).reset_index()
# live pressure: clv x vol20 on 3-min bars of 11-05 (vol20 from same-day bars only - approximation, flagged)
B = pd.read_parquet(S / "live_1105_bars.parquet")
B["m"] = B.index.hour * 60 + B.index.minute; B = B[(B.m >= 570) & (B.m < 960)].copy(); B["b"] = (B.m - 570) // 3
b3 = B.groupby(["sym", "b"]).agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"), v=("volume", "sum")).reset_index()
b3["clv"] = np.where(b3.h > b3.l, ((b3.c - b3.l) - (b3.h - b3.c)) / (b3.h - b3.l), 0.0)
b3["vol20"] = b3.groupby("sym").v.transform(lambda v: v / v.shift(1).rolling(20, min_periods=5).mean())
b3["press"] = (b3.clv * b3.vol20).clip(-20, 20)
lv = lv.merge(b3.groupby("b").press.mean().reset_index(), on="b", how="left")
lv["date"] = "2026-11-05"; lv["period"] = "LIVE"
A = pd.concat([A[["date", "b", "n", "share_up", "mean_p", "press", "period"]], lv], ignore_index=True)
A = A.sort_values(["date", "b"]).reset_index(drop=True)
g = A.groupby("date")
for k in (3, 6):
    A[f"dsu{k}"] = A.share_up - g.share_up.shift(k)
    A[f"dmp{k}"] = A.mean_p - g.mean_p.shift(k)
    A[f"ps{k}"] = g.press.transform(lambda x: x.rolling(k, min_periods=1).sum())
A["T"] = 573 + 3 * A.b                                 # bar close minute
rows = []
for T in CPS:                                          # last Hunch bar closing <= T
    x = A[A["T"] <= T].groupby("date").tail(1).copy(); x["T"] = T; rows.append(x)
H = pd.concat(rows)
C = pd.read_parquet(S / "compass15.parquet")
D = C[C["T"].isin(CPS)].merge(H.drop(columns=["period"]), on=["date", "T"], how="inner")
D["w"] = D.date.map(lambda d: "TRAIN" if d <= "2026-02-28" else ("VALID" if d <= "2026-10-07" else ("FWD" if d <= "2026-11-04" else "LIVE")))
print(D.groupby("w").date.nunique())

BLOCKS = {"share_up": ["share_up"], "mean_p": ["mean_p"], "dshare3": ["dsu3"], "dshare6": ["dsu6"],
          "dmeanp3_6": ["dmp3", "dmp6"], "press": ["press"], "press_sum3_6": ["ps3", "ps6"],
          "all": ["share_up", "mean_p", "dsu3", "dsu6", "dmp3", "dmp6", "press", "ps3", "ps6"]}
Q = {"staying": "y_stay", "rest_of_day": "y_rod", "next30": "y_30", "next60": "y_60"}


def design(d, cols, mu=None, sd=None):
    oh = [(d.C30 == c).astype(float).values for c in [-2, -1, 1, 2]] + [(d["T"] == t).astype(float).values for t in CPS[1:]]
    X = np.column_stack([np.ones(len(d))] + oh)
    if cols:
        Z = d[cols].astype(float).values
        Z = np.nan_to_num((Z - mu) / sd)
        X = np.column_stack([X, Z])
    return X


def fit(X, y, l2=1e-3):
    w = np.zeros(X.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ w)); Wt = p * (1 - p)
        Hm = X.T @ (X * Wt[:, None]) + l2 * len(y) * np.eye(X.shape[1]); gr = X.T @ (p - y) + l2 * len(y) * w
        st = np.linalg.solve(Hm, gr); w -= st
        if np.abs(st).max() < 1e-8:
            break
    return w


def tday(x):
    x = pd.Series(x).dropna()
    return round(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))), 2) if len(x) > 2 and x.std() > 0 else np.nan


out = []
for qn, q in Q.items():
    d = D[(D[q] != 0) & D.C30.notna()].copy(); y = (d[q] > 0).astype(float).values
    tr = (d.w == "TRAIN").values
    wb = fit(design(d[tr], []), y[tr]); pb = 1 / (1 + np.exp(-design(d, []) @ wb))
    for bn, cols in BLOCKS.items():
        mu = d.loc[tr, cols].astype(float).mean().values; sd = d.loc[tr, cols].astype(float).std().values
        wa = fit(design(d[tr], cols, mu, sd), y[tr]); pa = 1 / (1 + np.exp(-design(d, cols, mu, sd) @ wa))
        ll = lambda p: -(y * np.log(p) + (1 - y) * np.log(1 - p))
        dll = ll(pb) - ll(pa); dacc = ((pa > .5) == y).astype(float) - ((pb > .5) == y).astype(float)
        for w in ["TRAIN", "VALID", "FWD", "LIVE"]:
            i = (d.w == w).values
            if not i.any():
                continue
            out.append(dict(q=qn, block=bn, w=w, n=int(i.sum()), days=d.date[i].nunique(),
                            acc_base=round(((pb[i] > .5) == y[i]).mean(), 4), acc_aug=round(((pa[i] > .5) == y[i]).mean(), 4),
                            d_acc=round(dacc[i].mean(), 4), d_ll=round(dll[i].mean(), 5),
                            t_ll=tday(pd.Series(dll[i]).groupby(d.date.values[i]).mean()),
                            t_acc=tday(pd.Series(dacc[i]).groupby(d.date.values[i]).mean())))
R = pd.DataFrame(out); R.to_csv(HERE / "hc1_lift.csv", index=False)

# split looks: within directional compass readings, Hunch share_up side agrees vs disagrees
sp = []
for qn, q in Q.items():
    d = D[(D[q] != 0) & D.C30.notna() & (D.C30 != 0)].copy()
    d["hit"] = (np.sign(d.C30) == d[q]).astype(float); d["agree"] = np.sign(d.share_up - 0.5) == np.sign(d.C30)
    for w in ["TRAIN", "VALID", "FWD", "LIVE"]:
        e = d[d.w == w]
        if e.empty:
            continue
        days = e.date.unique(); diff = lambda e: e[e.agree].hit.mean() - e[~e.agree].hit.mean()
        bs = [diff(e.set_index("date").loc[rng.choice(days, len(days))].reset_index()) for _ in range(500)] if len(days) > 5 else []
        dd = diff(e)
        sp.append(dict(q=qn, w=w, n_agree=int(e.agree.sum()), hit_agree=round(e[e.agree].hit.mean(), 4), n_dis=int((~e.agree).sum()),
                       hit_dis=round(e[~e.agree].hit.mean(), 4), diff=round(dd, 4), t_boot=round(dd / np.nanstd(bs), 2) if len(bs) else np.nan))
P = pd.DataFrame(sp); P.to_csv(HERE / "hc1_split.csv", index=False)
L = D[D.w == "LIVE"][["T", "C30", "share_up", "mean_p", "dsu3", "dsu6", "press", "fo"]].copy()
L.round(4).to_csv(HERE / "hc1_live_1105.csv", index=False)
# descriptive: correlation of share_up with SPY's same-bar / next-30 move (TRAIN, VALID)
cr = D.assign(r30=np.log(D.px30 / D.px)).groupby("w")[["share_up", "mean_p", "dsu3", "press", "fo", "r30"]].corr()["r30"].unstack().round(3)
cr.to_csv(HERE / "hc1_corr.csv")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
print(R.to_string(index=False)); print(P.to_string(index=False)); print(L.round(4).to_string(index=False)); print(cr)
