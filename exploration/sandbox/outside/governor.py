"""Idea B: per-setup equity-curve governor. A setup trades on day d only if the sum of its R over its last K sessions
(walk-forward, shadow results, before d) >= 0. Live (all journals deduped) and bench (8 setups, CHECK / T2).
Usage: python governor.py <scratch_dir> <cand.parquet>. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import tstat
from bench_book import load

SCR, CAND = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(5)


def run(sd, label, K):
    """sd: DataFrame setup, date, R (setup-day sum), n (lots). Returns summary row and per-setup table."""
    rows = []
    for s, g in sd.groupby("setup"):
        g = g.sort_values("date").reset_index(drop=True)
        trail = g.R.rolling(K).sum().shift(1)
        g["elig"] = trail.notna(); g["on"] = ~g.elig | (trail >= 0)
        g["setup"] = s
        rows.append(g)
    a = pd.concat(rows)
    e = a[a.elig]
    skip = e[~e.on]; kept = e[e.on]
    dR = -skip.R.sum()
    # random control: per setup skip the same number of eligible days at random
    nsk = skip.groupby("setup").size()
    eg = e.groupby("setup").indices
    eR = e.R.to_numpy()
    ctrl = []
    for _ in range(1000):
        tot = 0.0
        for s, n in nsk.items():
            tot -= eR[rng.choice(eg[s], n, replace=False)].sum()
        ctrl.append(tot)
    ctrl = np.array(ctrl)
    kpl = kept.R.sum() / kept.n.sum(); spl = skip.R.sum() / skip.n.sum() if len(skip) else np.nan
    # day-clustered t of book difference (sum of skipped setup-day R by date, sign flipped)
    dates = a.date.unique()
    dd = (-skip.groupby("date").R.sum()).reindex(dates, fill_value=0.0)
    ps = []
    for s, g in e.groupby("setup"):
        sk = g[~g.on]
        ps.append((s, len(g), len(sk), -sk.R.sum(), g.R.sum()))
    ps = pd.DataFrame(ps, columns=["setup", "elig_days", "skipped_days", "dR", "R_elig"])
    best = dd.max()
    return dict(set=label, K=K, setups=sd.setup.nunique(), elig_setup_days=len(e), skipped_days=len(skip),
                lots_skipped_share=skip.n.sum() / e.n.sum(), kept_R_per_lot=kpl, skipped_R_per_lot=spl,
                t_daydiff=tstat(skip.R.to_numpy() / skip.n.to_numpy()) if len(skip) > 2 else np.nan,
                welch_t=(kept.R / kept.n).mean() - (skip.R / skip.n).mean(),
                dR_total=dR, dR_day=dd.mean(), t_dateclust=tstat(dd), pct_vs_random=(ctrl < dR).mean() * 100,
                random_mean=ctrl.mean(), setups_better=int((ps.dR > 0).sum()), setups_worse=int((ps.dR < 0).sum()),
                worst_setup_dR=ps.dR.min(), dR_wo_best_day=(dd.sum() - best) / max(len(dd) - 1, 1),
                best_share=best / dd.sum() if dd.sum() > 0 else np.nan), ps


def welch(kept, skip):
    x, y = kept.R / kept.n, skip.R / skip.n
    return (x.mean() - y.mean()) / np.sqrt(x.var() / len(x) + y.var() / len(y))


# live
t = pd.read_parquet(f"{SCR}/live_acct.parquet").drop_duplicates("k")
live = t.groupby(["strategy", "date"]).agg(R=("r", "sum"), n=("r", "size")).reset_index().rename(columns={"strategy": "setup"})
big = live.groupby("setup").n.sum(); live = live[live.setup.isin(big[big >= 20].index)]
# bench: 8 setups, <= 30 lots / setup-day, <= 3 per symbol per setup
c = load(CAND, setups=sorted(pd.read_parquet(CAND).setup.unique()))
c["rk"] = c.groupby(["date", "setup"]).cumcount(); c["sk"] = c.groupby(["date", "setup", "symbol"]).cumcount()
c = c[(c.rk < 30) & (c.sk < 3)]
bench = c.groupby(["setup", "date", "per"]).agg(R=("r", "sum"), n=("r", "size")).reset_index()

out, tabs = [], {}
for K in [5, 10]:
    for label, sd in [("live", live), ("bench CHECK", bench[bench.per == "CHECK"]), ("bench T2", bench[bench.per == "T2"])]:
        row, ps = run(sd[["setup", "date", "R", "n"]], label, K)
        # proper Welch t on setup-day avg R, kept vs skipped
        rows = []
        for s, g in sd.groupby("setup"):
            g = g.sort_values("date"); tr = g.R.rolling(K).sum().shift(1)
            rows.append(g.assign(elig=tr.notna(), on=tr.isna() | (tr >= 0)))
        a = pd.concat(rows); e = a[a.elig]
        row["welch_t"] = welch(e[e.on], e[~e.on])
        out.append(row); tabs[(label, K)] = ps
pd.set_option("display.width", 250)
print(pd.DataFrame(out).drop(columns=["t_daydiff"]).round(3).T.to_string())
print("\nBench per-setup dR (K=5):")
for lab in ["bench CHECK", "bench T2"]:
    print(lab); print(tabs[(lab, 5)].round(2).to_string(index=False))
