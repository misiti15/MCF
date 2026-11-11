"""FASTDEC walk-forward (research, 2026-11-11). Educational only - not financial advice.

For every checkpoint (after live session 6 .. 21 of 26, so that 5 forward sessions exist), every method sees only the
trades closed up to that session and calls promote / demote per setup (setups with >= 5 trades then). A call is scored on
the setup's trades over the NEXT 5 live sessions (R after costs; scored when >= 3 forward trades):
  promote correct  <=> forward avg R > 0;   demote correct <=> forward avg R < 0   (also reported: < -0.05).
Each setup's FIRST call per method and direction is the unit for precision (Wilson 95% CI) and timing; repeated calls at
later checkpoints are reported too, with a session-block bootstrap.
Timing: live sessions between the call and the session the setup first reached REPS-MIN 8 traded sessions / 30 trades
(censored at the end of data when it never did), and vs the REPS-MIN baseline's own first same-direction call.

Usage: python -m research.fastdec.study <journals dir with p/t1/t2/gy/gen/ex1/ll/journal.db> [asof]
Writes research/fastdec/out/{wf_calls.csv, wf_summary.csv, wf_summary.json, reliability.json}.
"""
from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, pearsonr, spearmanr

from research.fastdec import engine as E

OUT = E.HERE / "out"
FWD = 5
MIN_FWD_TRADES = 3
rng = np.random.default_rng(20261111)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def baseline_calls(T: pd.DataFrame, S: pd.DataFrame, P: pd.DataFrame, rule: str) -> pd.Series:
    """REPS-MIN 8/30. B1 = ROT balanced Candidate bar (promote) / Graveyard-floor shape (demote); B2 = sign rule."""
    D = E.day_table(T)
    day = D.set_index(["strategy", "date"])
    out = {}
    for s, r in S.iterrows():
        if r.k < 8 or r.N < 30:
            out[s] = ""
            continue
        g = day.loc[s]
        shrunk = r.m * r.N / (r.N + 20)
        if rule == "B2":
            out[s] = "promote" if r.m > 0 else ("demote" if r.m < -0.05 else "")
            continue
        dsum = g.y
        tday = dsum.mean() / (dsum.std(ddof=1) / len(dsum) ** .5) if len(dsum) > 2 and dsum.std(ddof=1) > 0 else np.nan
        l5 = g.sort_index().iloc[-5:]
        last5 = l5.y.sum() / l5.n.sum()
        bt = P.loc[s, "bt_mean"] if s in P.index else np.nan
        share = r.best_share
        prom = (shrunk >= 0.03 and (r.exbest > 0) and (np.isnan(share) or share <= 0.60) and (tday >= 0.73)
                and last5 > -0.15 and (np.isnan(bt) or bt >= -0.10))
        dem = shrunk <= -0.10 and (r.exbest < 0 or np.isnan(r.exbest)) and last5 < 0
        out[s] = "promote" if prom else ("demote" if dem else "")
    return pd.Series(out)


METHODS = {
    # name: (kind, engine method, param overrides)
    "B1 REPS-MIN 8/30 balanced bar": ("base", "B1", {}),
    "B2 REPS-MIN 8/30 sign rule": ("base", "B2", {}),
    "M1a EB family x side": ("eng", "eb", {"own_agree": False}),
    "M1b EB family x side + own-sign guard": ("eng", "eb", {}),
    "M1c EB on day-factor excess + own-sign guard": ("eng", "ebx", {}),
    "M2a Bayes sequential, weak prior": ("eng", "flat", {}),
    "M2b SPRT -0.05 vs +0.05, a=b=0.10": ("eng", "sprt", {}),
    "M3a 2y-backtest prior (raw) + gap": ("eng", "bt", {}),
    "M3b 2y-backtest prior (E90 borrow) + gap": ("eng", "bt", {"_col": "bt_e90"}),
    "M1d EB family x side + guard + no 1-day promote": ("eng", "eb", {"_oneday": True}),
    "M4 Bayes sequential + REPS-MIN demote floor (post hoc)": ("eng", "flat", {"repsmin_demote_floor": True}),
}
# every engine config except M4 runs WITHOUT the REPS-MIN demote floor (it is M4's addition)
for _k, _v in METHODS.items():
    if _v[0] == "eng" and not _k.startswith("M4"):
        _v[2].setdefault("repsmin_demote_floor", False)


def run(journals, asof="2026-11-10"):
    T = E.load_trades(journals, asof)
    dates = sorted(T.date.unique())
    P = E.expand_priors(E.load_priors(), T.strategy.unique())
    D = E.day_table(T)
    # session at which each setup first reaches REPS-MIN 8/30
    reach = {}
    for s, g in D.sort_values("date").groupby("strategy"):
        ok = (np.arange(1, len(g) + 1) >= 8) & (g.n.cumsum().to_numpy() >= 30)
        reach[s] = dates.index(g.date.to_numpy()[ok.argmax()]) if ok.any() else None
    rows = []
    cps = list(range(5, len(dates) - FWD))            # 0-based index of the last session seen
    for ci in cps:
        d = dates[ci]
        Tc = T[T.date <= d]
        fw = T[T.date.isin(dates[ci + 1: ci + 1 + FWD])].groupby("strategy").R.agg(["mean", "size", "sum"])
        rest = T[T.date > d].groupby("strategy").R.agg(["mean", "size"])
        Sbase = E.setup_stats(E.day_table(Tc))
        Sbase = Sbase[Sbase.N >= 5]
        for name, (kind, m, over) in METHODS.items():
            if kind == "base":
                calls = baseline_calls(Tc, Sbase, P, m)
                pp = pd.Series(np.nan, index=calls.index)
            else:
                p = deepcopy(E.PARAMS)
                p.update({k: v for k, v in over.items() if not k.startswith("_")})
                S = E.evaluate(Tc, m, P, p, bt_col=over.get("_col", "bt_mean"))
                S = S[S.N >= 5]
                calls = S.call.copy()
                if over.get("_oneday"):
                    calls[(calls == "promote") & S.one_day.fillna(False).astype(bool)] = ""
                pp = S.p_pos
            for s, c in calls.items():
                if not c:
                    continue
                f = fw.loc[s] if s in fw.index else None
                rr = rest.loc[s] if s in rest.index else None
                rows.append(dict(method=name, ci=ci, date=d, setup=s, call=c, p_pos=pp.get(s),
                                 k=int(Sbase.loc[s, "k"]), N=int(Sbase.loc[s, "N"]), avgR=Sbase.loc[s, "m"],
                                 fwd_n=0 if f is None else int(f["size"]), fwd_avgR=np.nan if f is None else f["mean"],
                                 rest_n=0 if rr is None else int(rr["size"]), rest_avgR=np.nan if rr is None else rr["mean"],
                                 reach_ci=reach.get(s)))
        print(d, len(rows), flush=True)
    C = pd.DataFrame(rows)
    C.to_csv(OUT / "wf_calls.csv", index=False, float_format="%.4f")
    # base rates over all scorable setup-checkpoints
    base = []
    for ci in cps:
        d = dates[ci]
        seen = T[T.date <= d].groupby("strategy").size()
        seen = seen[seen >= 5].index
        fw = T[T.date.isin(dates[ci + 1: ci + 1 + FWD])].groupby("strategy").R.agg(["mean", "size"])
        fw = fw[(fw["size"] >= MIN_FWD_TRADES) & fw.index.isin(seen)]
        base.append(fw.assign(ci=ci))
    B = pd.concat(base)
    return T, dates, C, B, reach, cps


def summarise(T, dates, C, B, reach, cps):
    last = len(dates) - 1
    res = []
    b1 = C[C.method.str.startswith("B1")].sort_values("ci").groupby(["setup", "call"]).ci.first()
    for name in METHODS:
        X = C[C.method == name]
        for call in ("promote", "demote"):
            Y = X[X.call == call]
            first = Y.sort_values("ci").groupby("setup").first().reset_index()
            sc = first[first.fwd_n >= MIN_FWD_TRADES]
            good = (sc.fwd_avgR > 0) if call == "promote" else (sc.fwd_avgR < 0)
            good05 = (sc.fwd_avgR > 0.05) if call == "promote" else (sc.fwd_avgR < -0.05)
            lo, hi = wilson(int(good.sum()), len(sc))
            # pooled forward avg R per trade with setup bootstrap
            fsum = (sc.fwd_avgR * sc.fwd_n)
            fr = fsum.sum() / sc.fwd_n.sum() if len(sc) else np.nan
            boots = []
            for _ in range(2000 if len(sc) else 0):
                i = rng.integers(0, len(sc), len(sc))
                boots.append(fsum.to_numpy()[i].sum() / sc.fwd_n.to_numpy()[i].sum())
            blo, bhi = (np.percentile(boots, [2.5, 97.5]) if boots else (np.nan, np.nan))
            # earliness vs REPS-MIN 8/30 reach (censored when never reached)
            early = []
            cens = 0
            for _, r in first.iterrows():
                rc = r.reach_ci
                if rc is None or (isinstance(rc, float) and np.isnan(rc)):
                    early.append(last - r.ci)
                    cens += 1
                else:
                    early.append(int(rc) - r.ci)
            early = np.array(early, float)
            # vs B1's own first same-direction call
            vs = [b1[(r.setup, call)] - r.ci for _, r in first.iterrows() if (r.setup, call) in b1.index]
            # repeated calls, session-block bootstrap of forward avg R
            Ys = Y[Y.fwd_n >= MIN_FWD_TRADES]
            rep_good = ((Ys.fwd_avgR > 0) if call == "promote" else (Ys.fwd_avgR < 0)).mean() if len(Ys) else np.nan
            res.append(dict(
                method=name, call=call, setups_called=len(first), scored=len(sc),
                correct=int(good.sum()), precision=good.mean() if len(sc) else np.nan, ci_lo=lo, ci_hi=hi,
                precision_strict=good05.mean() if len(sc) else np.nan,
                false_calls=int(len(sc) - good.sum()),
                fwd_avgR=fr, fwd_ci_lo=blo, fwd_ci_hi=bhi, fwd_trades=int(sc.fwd_n.sum()),
                rest_avgR=(first.rest_avgR * first.rest_n).sum() / first.rest_n.sum() if first.rest_n.sum() else np.nan,
                median_sessions_before_repsmin=float(np.median(early)) if len(early) else np.nan,
                share_before_repsmin=float((early > 0).mean()) if len(early) else np.nan,
                never_reached_repsmin=cens,
                median_vs_B1_call=float(np.median(vs)) if vs else np.nan, n_vs_B1=len(vs),
                repeated_calls=len(Ys), repeated_precision=rep_good,
                median_k_at_call=float(first.k.median()) if len(first) else np.nan,
                median_N_at_call=float(first.N.median()) if len(first) else np.nan,
            ))
    R = pd.DataFrame(res)
    base = dict(scorable=len(B), fwd_pos=float((B["mean"] > 0).mean()), fwd_neg=float((B["mean"] < 0).mean()),
                fwd_lt_m05=float((B["mean"] < -0.05).mean()))
    return R, base


def reliability(T):
    """Split-half reliability of setup avg R: raw, and with the common day x side factor removed."""
    D = E.day_table(T)
    Dx, fbar = E.excess_day_table(D)
    dates = sorted(T.date.unique())
    idx = {d: i for i, d in enumerate(dates)}
    out = {}
    for lab, X in (("raw", D), ("excess", Dx)):
        for split in ("odd_even", "time_halves"):
            pairs = []
            for s, g in X.groupby("strategy"):
                g = g.sort_values("date")
                if split == "odd_even":
                    a, b = g[g.date.map(idx) % 2 == 0], g[g.date.map(idx) % 2 == 1]
                else:
                    h = len(g) // 2
                    a, b = g.iloc[:h], g.iloc[h:]
                if len(a) >= 3 and len(b) >= 3:
                    pairs.append((a.y.sum() / a.n.sum(), b.y.sum() / b.n.sum()))
            A = np.array(pairs)
            r, pv = pearsonr(A[:, 0], A[:, 1])
            out[f"{lab}_{split}"] = dict(setups=len(A), pearson=round(r, 3), p=round(pv, 4),
                                         spearman=round(spearmanr(A[:, 0], A[:, 1])[0], 3),
                                         tau_from_cov=round(float(np.sqrt(max(0, np.cov(A.T)[0, 1]))), 3))
    out["side_pool_long_run"] = {k: dict(mean=round(v[0], 4), se=round(v[1] ** .5, 4), sessions=v[2]) for k, v in fbar.items()}
    return out


if __name__ == "__main__":
    J = sys.argv[1]
    asof = sys.argv[2] if len(sys.argv) > 2 else "2026-11-10"
    OUT.mkdir(parents=True, exist_ok=True)
    T, dates, C, B, reach, cps = run(J, asof)
    R, base = summarise(T, dates, C, B, reach, cps)
    R.to_csv(OUT / "wf_summary.csv", index=False, float_format="%.4f")
    rel = reliability(T)
    json.dump(dict(asof=asof, sessions=len(dates), checkpoints=[dates[c] for c in cps], base_rates=base,
                   configs=len(METHODS), reliability=rel), open(OUT / "wf_summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 250)
    print(R.round(3).to_string())
    print(base)
    print(json.dumps(rel, indent=1))
