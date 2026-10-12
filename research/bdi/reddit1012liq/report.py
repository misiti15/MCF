"""Reddit liquidity study: statistics and gates per configuration from data/daystats.npz (PLAN.md section 5).

    python research/bdi/reddit1012liq/report.py      # -> results.csv (all 7,680), finalists.csv, summary.json
Stats are computed from per-session sums with the formulas of mcf.research.gates (summary / regime_split /
walk_forward); `check()` confirms them against gates.summary on control trades. Educational only - not financial advice.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(HERE))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from score import KS, LEVELS, XS, exits, sigsets  # noqa: E402

DATA = HERE / "data"
TRAIN_END = "2025-12-31"
N_EXTRA = 4 + 32            # B3 replicas + daily grid; finalist robustness re-scores are added in NOTES
LINEAGE = {"CWT B3": 96, "bdi-rdt-r15-sweep": 128}
T1_MEDIAN_FD = -0.046       # median full-day backtest exp of Testing 1's -FD setups (config/account_testing.yaml)
CWT14_BEST = -0.086         # best live CWT14 configuration (research/bdi/cwt/live/NOTES.md)


def stats(S, N, W, SS, mask):
    """Vectorised gates.summary over configurations (rows) for the sessions in `mask`."""
    S, N, W, SS = S[:, mask], N[:, mask], W[:, mask], SS[:, mask]
    n = N.sum(1)
    tot = S.sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = tot / n
        se = np.sqrt(((S - N * mu[:, None]) ** 2 * (N > 0)).sum(1)) / n
        t = mu / se
        Sb = np.where(N > 0, S, -np.inf)
        b = Sb.argmax(1)
        rows = np.arange(len(S))
        exb = (tot - S[rows, b]) / np.maximum(1, n - N[rows, b])
        busy = N.max(1) / n
        win = W.sum(1) / n
        mus = SS.sum(1) / n
    return dict(n=n, exp=mu, t=t, exb=exb, busy=busy, win=win, exps=mus, days=(N > 0).sum(1))


def walk_forward(S, N, months_of_day):
    """gates.walk_forward on monthly sums: 3 consecutive train months, the next month as test (locked skipped);
    share of test months (n >= 10) with exp > 0."""
    ms = sorted(set(months_of_day))
    per = [pd.Period(m, freq="M") for m in ms]
    MS = np.stack([S[:, months_of_day == m].sum(1) for m in ms], 1)
    MN = np.stack([N[:, months_of_day == m].sum(1) for m in ms], 1)
    pos = np.zeros(len(S)); cnt = np.zeros(len(S))
    for i in range(len(ms) - 3):
        w = per[i:i + 4]
        if any((b - a).n != 1 for a, b in zip(w, w[1:])):
            continue
        te = i + 3
        ok = MN[:, te] >= gates.FOLD_MIN_N
        with np.errstate(invalid="ignore", divide="ignore"):
            pos += ok & (MS[:, te] / MN[:, te] > 0)
        cnt += ok
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cnt > 0, pos / cnt, np.nan)


def main():
    z = np.load(DATA / "daystats.npz")
    S, SS, N, W = z["S"].astype(float), z["SS"].astype(float), z["N"].astype(float), z["W"].astype(float)
    meta = json.load(open(DATA / "controls.json"))
    dates = np.array(meta["dates"])
    reg = lib.regimes()
    regime = reg["regime"].reindex(pd.to_datetime(dates).date).to_numpy()
    SG, EX = sigsets(), exits()
    rows = []
    for sg in SG:
        for ex in EX:
            rows.append(dict(level=sg[0], side=sg[1], x=sg[2], trig=sg[3], k=sg[4], att=ex[0], stop=ex[1], tgt=ex[2], mgmt=ex[3]))
    df = pd.DataFrame(rows)
    df.insert(0, "name", meta["names"])
    NT = len(df) + N_EXTRA
    treq = gates.t_required(NT)
    treq_lin = gates.t_required(NT + sum(LINEAGE.values()))
    tr = dates <= TRAIN_END
    for tag, m in (("tr", tr), ("va", ~tr), ("all", np.ones(len(dates), bool))):
        st = stats(S, N, W, SS, m)
        for k, v in st.items():
            df[f"{tag}_{k}"] = v
    for rg in ("up", "flat", "down"):
        st = stats(S, N, W, SS, regime == rg)
        df[f"{rg}_n"], df[f"{rg}_exp"], df[f"{rg}_t"] = st["n"], st["exp"], st["t"]
    df["wf_share"] = walk_forward(S, N, np.array([d[:7] for d in dates]))
    df["live_ok"] = df["level"].isin(["PD", "OR", "H60"]) & (df["att"] == 1)
    # plateau: one-step neighbours in x and k (everything else equal)
    key = ["level", "side", "trig", "att", "stop", "tgt", "mgmt"]
    ix = df.set_index(key + ["x", "k"])["all_exp"]
    pl = []
    for _, r in df.iterrows():
        nb = [ix.get(tuple(r[key]) + (x2, r["k"])) for x2 in XS if x2 != r["x"]]
        nb += [ix.get(tuple(r[key]) + (r["x"], k2)) for k2 in KS if k2 != r["k"]]
        nb = [v for v in nb if v is not None and np.isfinite(v)]
        pl.append(min(nb) if nb else np.nan)
    df["plateau_min"] = pl
    df["regime_pass"] = (df.up_n >= 30) & (df.down_n >= 30) & (df.up_exp > 0) & (df.down_exp > 0)
    df["gates_keep"] = (df.all_exp > 0) & (df.all_t >= treq) & df.regime_pass & (df.wf_share >= gates.WF_MIN_SHARE)
    df["bar_a"] = (df.live_ok & (df.all_n >= 150) & (df.all_exp > 0) & (df.all_t >= 1.5) & (df.tr_exp > 0)
                   & (df.va_exp > 0) & (df.all_exb > 0) & (df.all_busy <= 0.10))
    df["bar_b"] = (df.live_ok & (df.all_n >= 150) & (df.all_exp >= T1_MEDIAN_FD) & (df.va_exp > 0)
                   & (df.all_exp > CWT14_BEST) & (((df.up_n >= 30) & (df.up_exp > 0)) | ((df.down_n >= 30) & (df.down_exp > 0))))
    df.round(4).to_csv(HERE / "results.csv", index=False)
    # finalists (PLAN 5): top 10 by train t (n_train >= 150, train exp > 0) + best by train t per level
    el = df[(df.tr_n >= 150) & (df.tr_exp > 0)].sort_values("tr_t", ascending=False)
    fin = pd.concat([el.head(10)] + [el[el.level == L].head(1) for L in LEVELS]).drop_duplicates("name")
    fin.round(4).to_csv(HERE / "finalists.csv", index=False)
    summ = {"n_configs": int(len(df)), "N_total": NT, "t_required": treq, "t_required_with_lineage": treq_lin,
            "exp_pos_all": int((df.all_exp > 0).sum()), "exp_pos_all_n150": int(((df.all_exp > 0) & (df.all_n >= 150)).sum()),
            "t_ge_2_all": int((df.all_t >= 2).sum()), "max_t_all": float(np.nanmax(df.all_t)),
            "gates_keep": int(df.gates_keep.sum()), "bar_a": int(df.bar_a.sum()), "bar_b": int(df.bar_b.sum()),
            "eligible_finalists": int(len(el)), "controls": meta["controls"]}
    json.dump(summ, open(HERE / "summary.json", "w"), indent=1, default=float)
    pd.set_option("display.width", 300, "display.max_columns", 40, "display.max_rows", 200)
    cols = ["name", "tr_n", "tr_exp", "tr_t", "va_n", "va_exp", "va_t", "all_n", "all_exp", "all_exps", "all_t",
            "up_exp", "down_exp", "wf_share", "all_exb", "all_busy", "plateau_min", "bar_a", "bar_b"]
    print(json.dumps({k: v for k, v in summ.items() if k != "controls"}, default=float))
    print(fin[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
