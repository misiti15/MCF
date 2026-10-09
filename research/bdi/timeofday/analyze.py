"""Score the time-of-day study (NOTES.md 0.4-0.7) from data/trades.parquet and data/baseline.parquet.
Outputs: results.csv (one row per setup x trade set), tests.csv (one row per setup), pooled.csv, data/report.json.
    python research/bdi/timeofday/analyze.py
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(HERE)]
from lib import regimes  # noqa: E402
from mcf.research import gates as G  # noqa: E402

DATA = HERE / "data"
BK = ["B1", "B2", "B3", "B4", "B5"]
BLABEL = {"B1": "09:50-10:30", "B2": "10:35-11:30", "B3": "11:35-13:00", "B4": "13:05-14:00", "B5": "14:05-15:00"}
NPERM, SEED, MIN_N = 2000, 20261009, 30


def perm_test(tr: pd.DataFrame, rng) -> tuple[float, float]:
    """Within-session permutation of bucket labels; F = sum_b n_b (mean_b - mean)^2."""
    t = tr.sort_values("date", kind="mergesort")
    r = t["r"].to_numpy(float)
    b = pd.Categorical(t["set"], categories=BK).codes
    d = pd.factorize(t["date"])[0]
    mu = r.mean()

    def F(lbl):
        s = np.bincount(lbl, weights=r, minlength=5)
        n = np.bincount(lbl, minlength=5)
        m = np.where(n > 0, s / np.maximum(n, 1), mu)
        return float((n * (m - mu) ** 2).sum())

    f0 = F(b)
    cnt = 0
    for _ in range(NPERM):
        order = np.lexsort((rng.random(len(b)), d))       # random order within each session (d is sorted)
        cnt += F(b[order]) >= f0 - 1e-12
    return f0, (1 + cnt) / (NPERM + 1)


def block_perm_test(tr: pd.DataFrame, rng) -> tuple[float, float]:
    """Corrected primary test (NOTES.md 0.5a): within each session, the five bucket labels are relabelled by one random
    permutation (whole bucket blocks move together), so the one-trade-per-symbol-day-per-bucket structure and the
    within-day correlation of a symbol's trades are preserved. Same F statistic."""
    r = tr["r"].to_numpy(float)
    b = pd.Categorical(tr["set"], categories=BK).codes
    d = pd.factorize(tr["date"])[0]
    mu = r.mean()

    def F(lbl):
        s = np.bincount(lbl, weights=r, minlength=5)
        n = np.bincount(lbl, minlength=5)
        m = np.where(n > 0, s / np.maximum(n, 1), mu)
        return float((n * (m - mu) ** 2).sum())

    f0 = F(b)
    nd = d.max() + 1
    cnt = 0
    for _ in range(NPERM):
        perms = np.argsort(rng.random((nd, 5)), axis=1)
        cnt += F(perms[d, b]) >= f0 - 1e-12
    return f0, (1 + cnt) / (NPERM + 1)


def cluster_wald(tr: pd.DataFrame) -> tuple[float, float]:
    """OLS r ~ bucket dummies (B1 base), CR1 session-clustered covariance; Wald chi2 for equal bucket means."""
    present = [k for k in BK if (tr["set"] == k).sum() > 0]
    if len(present) < 2:
        return np.nan, np.nan
    X = np.column_stack([np.ones(len(tr))] + [(tr["set"] == k).to_numpy(float) for k in present[1:]])
    y = tr["r"].to_numpy(float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    u = y - X @ beta
    g = pd.factorize(tr["date"])[0]
    S = np.zeros((X.shape[1], X.shape[1]))
    Xu = X * u[:, None]
    sums = np.zeros((g.max() + 1, X.shape[1]))
    np.add.at(sums, g, Xu)
    S = sums.T @ sums
    G_, N, K = g.max() + 1, len(y), X.shape[1]
    V = XtX_inv @ S @ XtX_inv * (G_ / (G_ - 1)) * ((N - 1) / (N - K))
    b = beta[1:]
    W = float(b @ np.linalg.pinv(V[1:, 1:]) @ b)
    return W, float(stats.chi2.sf(W, len(b)))


def bh(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float)
    n = len(p)
    o = np.argsort(p)
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(q, 1)
    return out


def main():
    reg = regimes()
    sessions = sorted(reg.index)
    n_sess = len(sessions)
    med = sessions[(n_sess - 1) // 2]
    half = {d: ("H1" if d <= med else "H2") for d in sessions}
    n_half = {h: sum(1 for v in half.values() if v == h) for h in ("H1", "H2")}
    x = pd.read_parquet(DATA / "trades.parquet")
    x["date"] = pd.to_datetime(x["date"]).dt.date
    x = x[x["date"].isin(set(sessions))]
    x["half"] = x["date"].map(half)
    x["regime"] = x["date"].map(reg["regime"])
    x["leg"] = x["setup"] + np.where(x["setup"].str.startswith("heat"), "", "")
    rng = np.random.default_rng(SEED)
    rows, tests = [], []
    for setup, xs in x.groupby("setup", sort=False):
        side = xs["side"].iloc[0]
        per = {}
        for st in ["current", "full"] + BK:
            tr = xs[xs["set"] == st]
            o = G.summary(tr)
            rs = {k: G.summary(tr[tr["regime"] == k]) for k in ("up", "down")}
            hs = {h: G.summary(tr[tr["half"] == h]) for h in ("H1", "H2")}
            row = {"setup": setup, "side": side, "set": st, "label": BLABEL.get(st, st), "n": o.get("n", 0),
                   "per_day": round(o.get("n", 0) / n_sess, 2), "exp_r": o.get("exp_r"), "t": o.get("t"),
                   "win_rate": o.get("win_rate"), "ex_best_day": o.get("ex_best_day"),
                   "up_n": rs["up"].get("n", 0), "up_exp": rs["up"].get("exp_r"),
                   "down_n": rs["down"].get("n", 0), "down_exp": rs["down"].get("exp_r"),
                   "h1_n": hs["H1"].get("n", 0), "h1_exp": hs["H1"].get("exp_r"), "h1_t": hs["H1"].get("t"),
                   "h2_n": hs["H2"].get("n", 0), "h2_exp": hs["H2"].get("exp_r"), "h2_t": hs["H2"].get("t")}
            per[st] = row
            rows.append(row)
        bt = xs[xs["set"].isin(BK)]
        f0, pp = perm_test(bt, rng) if len(bt) else (np.nan, np.nan)
        fb, pb = block_perm_test(bt, rng) if len(bt) else (np.nan, np.nan)
        W, pw = cluster_wald(bt) if len(bt) else (np.nan, np.nan)
        # out-of-sample bucket choice: best bucket (n >= MIN_N) on one half, scored on the other
        oos = {}
        for a, b in (("H1", "H2"), ("H2", "H1")):
            ins = {k: per[k][f"{a.lower()}_exp"] for k in BK if per[k][f"{a.lower()}_n"] >= MIN_N and per[k][f"{a.lower()}_exp"] is not None}
            if not ins:
                oos[a] = None
                continue
            best = max(ins, key=ins.get)
            oos[a] = {"best": best, "ins_exp": ins[best], "ins_full": per["full"][f"{a.lower()}_exp"],
                      "oos_exp": per[best][f"{b.lower()}_exp"], "oos_n": per[best][f"{b.lower()}_n"],
                      "oos_full": per["full"][f"{b.lower()}_exp"], "oos_cur": per["current"][f"{b.lower()}_exp"]}
        cur, full = per["current"], per["full"]
        tests.append({"setup": setup, "side": side, "window": None, "perm_F": round(f0, 3), "rowperm_p": round(pp, 4), "perm_p": round(pb, 4),
                      "wald_chi2": round(W, 2) if np.isfinite(W) else None, "wald_p": round(pw, 4) if np.isfinite(pw) else None,
                      "cur_n": cur["n"], "cur_per_day": cur["per_day"], "cur_exp": cur["exp_r"], "cur_t": cur["t"],
                      "full_n": full["n"], "full_per_day": full["per_day"], "full_exp": full["exp_r"], "full_t": full["t"],
                      "cur_h1": cur["h1_exp"], "full_h1": full["h1_exp"], "cur_h2": cur["h2_exp"], "full_h2": full["h2_exp"],
                      "best_h1": oos["H1"]["best"] if oos["H1"] else None, "best_h1_ins": oos["H1"]["ins_exp"] if oos["H1"] else None,
                      "best_h1_oos_h2": oos["H1"]["oos_exp"] if oos["H1"] else None, "full_h2_ref": oos["H1"]["oos_full"] if oos["H1"] else None,
                      "best_h2": oos["H2"]["best"] if oos["H2"] else None, "best_h2_ins": oos["H2"]["ins_exp"] if oos["H2"] else None,
                      "best_h2_oos_h1": oos["H2"]["oos_exp"] if oos["H2"] else None, "full_h1_ref": oos["H2"]["oos_full"] if oos["H2"] else None})
    res = pd.DataFrame(rows)
    te = pd.DataFrame(tests)
    te["bh_q"] = bh(te["perm_p"].to_numpy()).round(4)
    te["bh_q_rowperm"] = bh(te["rowperm_p"].to_numpy()).round(4)
    te["bh_q_wald"] = bh(te["wald_p"].fillna(1).to_numpy()).round(4)

    def rec(r):
        both = (r.cur_h1 is not None and r.full_h1 is not None and r.cur_h2 is not None and r.full_h2 is not None
                and r.cur_h1 > r.full_h1 and r.cur_h2 > r.full_h2)
        if r.bh_q <= 0.10:
            return "keep window" if both else "unclear"
        return "widen to full day"
    te["recommendation"] = te.apply(rec, axis=1)
    res = res.merge(te[["setup", "rowperm_p", "perm_p", "wald_p", "bh_q", "recommendation"]], on="setup", how="left")

    # pooled view: bucket exp minus the setup's full-day exp, equal weight per setup, by side x half / regime
    pooled = []
    for (setup, side), xs in x.groupby(["setup", "side"]):
        for dim, vals in (("half", ("H1", "H2")), ("regime", ("up", "down")), ("all", ("all",))):
            for v in vals:
                sub = xs if dim == "all" else xs[xs[dim] == v]
                fe = sub.loc[sub["set"] == "full", "r"].mean()
                for k in BK:
                    rb = sub.loc[sub["set"] == k, "r"]
                    pooled.append({"setup": setup, "side": side, "dim": dim, "val": v, "bucket": k, "n": len(rb),
                                   "exp": rb.mean() if len(rb) else np.nan, "rel": rb.mean() - fe if len(rb) >= 10 else np.nan})
    pooled = pd.DataFrame(pooled)
    pv = pooled.groupby(["side", "dim", "val", "bucket"]).agg(setups=("rel", "count"), mean_rel=("rel", "mean"),
                                                               sd_rel=("rel", "std"), mean_exp=("exp", "mean")).reset_index()
    pv["se_rel"] = pv["sd_rel"] / np.sqrt(pv["setups"])
    # random-bar baseline per bucket and side, by half / regime
    b = pd.read_parquet(DATA / "baseline.parquet")
    b["date"] = pd.to_datetime(b["date"]).dt.date
    b = b[b["date"].isin(set(sessions))]
    b["half"], b["regime"] = b["date"].map(half), b["date"].map(reg["regime"])
    base = []
    for dim, vals in (("half", ("H1", "H2")), ("regime", ("up", "flat", "down")), ("all", ("all",))):
        for v in vals:
            sub = b if dim == "all" else b[b[dim] == v]
            g = sub.groupby(["side", "bucket"])[["sum", "size"]].sum()
            for (side, k), r in g.iterrows():
                base.append({"side": side, "dim": dim, "val": v, "bucket": k, "n": int(r["size"]), "exp": r["sum"] / r["size"]})
    base = pd.DataFrame(base)
    res.to_csv(HERE / "results.csv", index=False)
    te.to_csv(HERE / "tests.csv", index=False)
    pv.round(4).to_csv(HERE / "pooled.csv", index=False)
    base.round(4).to_csv(HERE / "baseline.csv", index=False)
    # OOS summary across setups
    o = []
    for _, r in te.iterrows():
        for a, oc, fr in (("H1", "best_h1_oos_h2", "full_h2_ref"), ("H2", "best_h2_oos_h1", "full_h1_ref")):
            if r[oc] is not None and r[fr] is not None and np.isfinite(r[oc]) and np.isfinite(r[fr]):
                o.append({"setup": r.setup, "chosen_on": a, "diff": r[oc] - r[fr],
                          "ins_diff": (r["best_h1_ins"] if a == "H1" else r["best_h2_ins"]) - (r["full_h1"] if a == "H1" else r["full_h2"])})
    o = pd.DataFrame(o)
    rep = {"sessions": n_sess, "median_date": str(med), "halves": n_half,
           "oos_pairs": len(o), "oos_share_beats_full": round(float((o["diff"] > 0).mean()), 3),
           "oos_mean_diff": round(float(o["diff"].mean()), 4), "oos_se_diff": round(float(o["diff"].std() / np.sqrt(len(o))), 4),
           "ins_mean_diff": round(float(o["ins_diff"].mean()), 4),
           "cur_vs_full_h1_share": round(float((te.cur_h1.astype(float) > te.full_h1.astype(float)).mean()), 3),
           "cur_vs_full_h2_share": round(float((te.cur_h2.astype(float) > te.full_h2.astype(float)).mean()), 3),
           "cur_minus_full_h1_mean": round(float((te.cur_h1.astype(float) - te.full_h1.astype(float)).mean()), 4),
           "cur_minus_full_h2_mean": round(float((te.cur_h2.astype(float) - te.full_h2.astype(float)).mean()), 4),
           "n_bh10": int((te.bh_q <= 0.10).sum()), "n_bh05": int((te.bh_q <= 0.05).sum()),
           "n_raw05": int((te.perm_p <= 0.05).sum()), "recs": te["recommendation"].value_counts().to_dict()}
    o.to_csv(DATA / "oos_pairs.csv", index=False)
    (DATA / "report.json").write_text(json.dumps(rep, indent=1, default=str))
    print(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()
