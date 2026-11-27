"""PMDIR-1127 scoring (PREREG.md). Fit on FIT only, freeze, score CHECK / T2 / EARLY; secondary: fit EARLY, score T2/CHECK.
    python research/pmdir_1127/pm_score.py <days.csv> <results.json>
Educational only - not financial advice."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from mcf.research.gates import tod_cost_mult  # noqa: E402
CELLS = json.load(open(HERE.parent / "primshorts_1126/cells_live.json"))
LOCK = ("2024-11-01", "2025-02-28")
NUM = ["mret", "mrange", "vwap", "breadth", "rvm", "rv20", "qi", "prev", "gap", "lmom", "w60"]
WIDTH_BP = 50.0
OOS = ["CHECK", "T2", "EARLY"]


def costs(price, px, kind, side, extra_bp=0.0):
    a = np.where(kind == 1, CELLS["100+|stop"][0], CELLS["100+|market"][0])
    b = np.where(kind == 1, CELLS["100+|stop"][1], CELLS["100+|market"][1])
    livel = a / WIDTH_BP + b
    risk = price * WIDTH_BP / 1e4
    ec = (0.01 + price * 1e-4) * tod_cost_mult(np.full(len(price), 1201))
    xc = 0.01 + px * 1e-4 + np.where(kind == 1, 0.02, 0.0)
    br = np.where(side < 0, 1.2e-4 * price, 0.0)
    lr8 = (ec + xc + br) / risk
    ex = extra_bp / WIDTH_BP
    return livel + ex, lr8 + ex


def trade(df, side, late=False, extra=0.0):
    """R after LIVE-L / LR8 / gross for sides (+1/-1/0 = no trade)."""
    L = side == 1
    suf = "1" if late else ""
    g = np.where(L, df["rL" + suf], df["rS" + suf]).astype(float)
    kind = np.where(L, df["kL" + suf], df["kS" + suf]).astype(int)
    px = np.where(L, df["xL" + suf], df["xS" + suf]).astype(float)
    price = (df["eL1"] if late else df["entry"]).to_numpy(float)
    cl, c8 = costs(price, px, kind, side, extra)
    keep = side != 0
    return g[keep], (g - cl)[keep], (g - c8)[keep], keep


def tstat(x):
    x = np.asarray(x, float)
    if len(x) < 3: return np.nan
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def summ(r, dates):
    r = np.asarray(r, float)
    if len(r) == 0: return dict(n=0)
    tot = r.sum(); best = r.max()
    return dict(n=int(len(r)), mean=round(float(r.mean()), 4), t=round(tstat(r), 2),
                best_share=round(float(best / tot), 3) if tot > 0 else None,
                wo_best=round(float((tot - best) / (len(r) - 1)), 4) if len(r) > 1 else None)


def prep(df, mu=None, sd=None):
    X = df[NUM].astype(float).copy()
    if mu is None: mu, sd = X.mean(), X.std(ddof=0).replace(0, 1)
    Xs = (X - mu) / sd
    for k in range(1, 5): Xs[f"d{k}"] = (df.dow == k).astype(float)
    return Xs, mu, sd


def fit_models(tr):
    Xs, mu, sd = prep(tr); y = tr.y.to_numpy()
    m1 = LogisticRegression(C=1.0, max_iter=2000).fit(Xs, y)
    m2 = LogisticRegression(C=1.0, max_iter=2000).fit(Xs[["mret"]], y)
    Xt = tr[NUM + ["dow"]].astype(float)
    m3 = DecisionTreeClassifier(max_depth=2, min_samples_leaf=25, random_state=0).fit(Xt, y)
    m4 = DecisionTreeClassifier(max_depth=1, min_samples_leaf=25, random_state=0).fit(Xt, y)
    return dict(mu=mu, sd=sd, m1=m1, m2=m2, m3=m3, m4=m4)


def predict(M, df):
    Xs, _, _ = prep(df, M["mu"], M["sd"]); Xt = df[NUM + ["dow"]].astype(float)
    p = dict(M1=M["m1"].predict_proba(Xs)[:, 1], M2=M["m2"].predict_proba(Xs[["mret"]])[:, 1],
             M3=M["m3"].predict_proba(Xt)[:, 1], M4=M["m4"].predict_proba(Xt)[:, 1])
    return p


def sides(p, df):
    s = {k: np.where(v > 0.5, 1, np.where(v < 0.5, -1, 0)) for k, v in p.items()}
    s["M5"] = df.w60.to_numpy(int)
    s["M6"] = np.ones(len(df), int)
    s["M1c"] = np.where(np.abs(p["M1"] - 0.5) >= 0.05, s["M1"], 0)
    s["M3c"] = np.where(np.abs(p["M3"] - 0.5) >= 0.05, s["M3"], 0)
    return s


def score_split(df, side, prob, rng):
    out = {}
    keep = side != 0
    y = df.y.to_numpy()
    hit = (np.where(side == 1, y == 1, y == 0))[keep]
    out["n"] = int(keep.sum())
    out["hit"] = round(float(hit.mean()), 4) if keep.any() else None
    out["base_up"] = round(float(y.mean()), 4)
    if prob is not None and len(np.unique(y)) > 1:
        out["auc"] = round(float(roc_auc_score(y, prob)), 4)
    g, rl, r8, _ = trade(df, side)
    out["gross"] = summ(g, None); out["livel"] = summ(rl, None); out["lr8"] = summ(r8, None)
    _, rl1, _, _ = trade(df, side, late=True); out["late1m_livel"] = summ(rl1, None)
    _, rl2, _, _ = trade(df, side, extra=2.0); out["plus2bp_livel"] = summ(rl2, None)
    # signed afternoon return in bp (no-stop hold, gross)
    out["hold_bp_gross"] = round(float((side * df.ret_pm.to_numpy())[keep].mean() * 1e4), 2) if keep.any() else None
    # random direction control: same days, random sides
    if keep.any():
        sub = df[keep]; ms = []
        for _ in range(500):
            rs = rng.choice([-1, 1], size=len(sub))
            ms.append(trade(sub, rs)[1].mean())
        out["rand_pct"] = round(float((np.array(ms) < rl.mean()).mean() * 100), 1)
    return out


def pooled(dfs, sds, rng):
    df = pd.concat(dfs); side = np.concatenate(sds)
    keep = side != 0; y = df.y.to_numpy()
    hit = (np.where(side == 1, y == 1, y == 0))[keep]
    n = int(keep.sum()); h = float(hit.mean())
    z = (h - 0.5) / np.sqrt(0.25 / n)
    g, rl, r8, _ = trade(df, side)
    sub = df[keep]; ms = []
    for _ in range(500):
        ms.append(trade(sub, rng.choice([-1, 1], size=len(sub)))[1].mean())
    return dict(n=n, hit=round(h, 4), z=round(float(z), 2), gross=summ(g, None), livel=summ(rl, None),
                lr8=summ(r8, None), rand_pct=round(float((np.array(ms) < rl.mean()).mean() * 100), 1))


def main():
    df = pd.read_csv(sys.argv[1])
    assert not ((df.date >= LOCK[0]) & (df.date <= LOCK[1])).any()
    df = df.dropna(subset=NUM).reset_index(drop=True)
    rng = np.random.default_rng(20261127)
    res = {"counts": df.split.value_counts().to_dict()}
    for view, trn, tests in (("primary_fitFIT", "FIT", OOS), ("secondary_fitEARLY", "EARLY", ["T2", "CHECK"])):
        tr = df[df.split == trn]
        M = fit_models(tr)
        res[view] = {"logit_coef": dict(zip(prep(tr)[0].columns, np.round(M["m1"].coef_[0], 3).tolist())),
                     "mret_coef": float(np.round(M["m2"].coef_[0][0], 3)),
                     "tree": export_text(M["m3"], feature_names=NUM + ["dow"]),
                     "stump": export_text(M["m4"], feature_names=NUM + ["dow"])}
        names = ["M1", "M2", "M3", "M4", "M5", "M6", "M1c", "M3c"] if view.startswith("primary") else ["M1", "M2", "M3", "M4"]
        for nm in names:
            res[view][nm] = {}
            parts = []
            for s in [trn] + tests:
                d = df[df.split == s].reset_index(drop=True)
                p = predict(M, d); sd_ = sides(p, d)[nm]
                prob = p.get(nm.rstrip("c")) if nm not in ("M5", "M6") else None
                res[view][nm][s] = score_split(d, sd_, prob, rng)
                if s in tests: parts.append((d, sd_))
            res[view][nm]["POOLED_OOS"] = pooled([a for a, _ in parts], [b for _, b in parts], rng)
    json.dump(res, open(sys.argv[2], "w"), indent=1, default=str)
    for view in ("primary_fitFIT", "secondary_fitEARLY"):
        print("==", view)
        for nm, v in res[view].items():
            if not isinstance(v, dict) or "POOLED_OOS" not in v: continue
            line = [nm]
            for s, x in v.items():
                if s == "POOLED_OOS":
                    line.append(f"POOL n{x['n']} hit{x['hit']} z{x['z']} L{x['livel']['mean']} t{x['livel']['t']} g{x['gross']['mean']} rp{x['rand_pct']}")
                else:
                    line.append(f"{s}: n{x['n']} hit{x['hit']} auc{x.get('auc')} g{x['gross'].get('mean')} L{x['livel'].get('mean')}(t{x['livel'].get('t')}) 8:{x['lr8'].get('mean')} bp{x['hold_bp_gross']}")
            print(" | ".join(line))


if __name__ == "__main__":
    main()
