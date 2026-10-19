"""Score the 23 pre-declared index-chase veto configurations (PLAN.md) on the history entries of the live Primary /
Testing 1 setups. Skipped trades score 0 R. Train <= 2025-12-31, valid 2026-01-01..2026-10-07; locked block absent
(asserted). Writes results.csv (pooled), by_setup.csv, random_control.csv, veto_out.txt.
Usage: python veto.py <scratch>. Educational only - not financial advice."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
S = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "research/history2y"))
from lib import regimes  # noqa: E402

LOCK = ("2024-11-01", "2025-02-28")
N_CFG = 23
BAR = max(1.5, math.sqrt(2 * math.log(N_CFG)))
BAR_CONS = max(1.5, math.sqrt(2 * math.log(N_CFG + 71)))
DRAWS = 500
rng = np.random.default_rng(20261019)

E = pd.read_parquet(S / "entries.parquet")
X = pd.read_parquet(S / "idx.parquet")
assert not ((E.date >= LOCK[0]) & (E.date <= LOCK[1])).any() and not ((X.date >= LOCK[0]) & (X.date <= LOCK[1])).any()
E = E.merge(X, on=["date", "tod"], how="left")
miss = E.q_r60.isna().mean()
E = E[E.q_r60.notna()].reset_index(drop=True)
E["s"] = np.where(E.side == "long", 1, -1)
E["split"] = np.where(E.date <= "2025-12-31", "train", "valid")
rg = regimes().reset_index(); rg["date"] = rg["date"].astype(str)
E = E.merge(rg[["date", "regime"]], on="date", how="left")
s, tod = E.s.to_numpy(), E.tod.to_numpy()


def chase(col, thr, after=0):
    m = E[col].to_numpy()
    return (np.sign(m) == s) & (np.abs(m) > thr) & (tod >= after)


def against(col, thr):
    m = E[col].to_numpy()
    return (tod >= 1030) & (np.sign(m) == -s) & (np.abs(m) > thr)


def near(d):
    return ((s == 1) & (E.q_dhi.to_numpy() <= d)) | ((s == -1) & (E.q_dlo.to_numpy() <= d))


CFG = {}
for ix, k in (("QQQ", "q"), ("SPY", "s")):
    for L in (30, 60):
        for thr in (0.0, 0.2, 0.4):
            CFG[f"A-chase-{ix}-{L}m-{thr:.1f}"] = chase(f"{k}_r{L}", thr)
for ix, k in (("QQQ", "q"), ("SPY", "s")):
    for thr in (0.0, 0.25, 0.5):
        CFG[f"B-against-{ix}-fo-1030-{thr:.2f}"] = against(f"{k}_fo", thr)
for d in (0.10, 0.15, 0.25):
    CFG[f"C-near-QQQ-extreme-{d:.2f}"] = near(d)
for thr in (0.2, 0.4):
    CFG[f"D-chase-QQQ-60m-{thr:.1f}-after1100"] = chase("q_r60", thr, after=1100)
assert len(CFG) == N_CFG


def tday(dsum):
    x = np.asarray(dsum, float)
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 and x.std(ddof=1) > 0 else np.nan


def stats(x, v):
    r = x.r.to_numpy(); n = len(r)
    kept = r[~v]
    days = x.date.to_numpy()
    D = pd.Series(np.where(v, -r, 0.0)).groupby(days).sum()
    mu_s = x.groupby("setup").r.transform("mean").to_numpy()
    Ex = pd.Series(np.where(v, -(r - mu_s), 0.0)).groupby(days).sum()
    out = dict(n=n, days=len(D), par_win=(r > 0).mean(), par_avgR=r.mean(), skip_share=v.mean(),
               kept_n=len(kept), kept_win=(kept > 0).mean() if len(kept) else np.nan, kept_avgR=kept.mean() if len(kept) else np.nan,
               skipped_avgR=r[v].mean() if v.any() else np.nan,
               delta=D.sum() / n, t_delta=tday(D), delta_ex_best_day=(D.sum() - D.max()) / n,
               excess=Ex.sum() / n, t_excess=tday(Ex))
    for g in ("up", "flat", "down"):
        w = (x.regime == g).to_numpy()
        out[f"delta_{g}"] = -r[w & v].sum() / max(w.sum(), 1)
        out[f"kept_avgR_{g}"] = r[w & ~v].mean() if (w & ~v).any() else np.nan
        out[f"par_avgR_{g}"] = r[w].mean() if w.any() else np.nan
    return out


def random_ctrl(x, v):
    code = pd.factorize(x.setup)[0]
    r = x.r.to_numpy(); n = len(r)
    k = np.bincount(code, weights=v.astype(float), minlength=code.max() + 1).astype(int)
    order0 = np.argsort(code, kind="stable")
    start = np.r_[0, np.cumsum(np.bincount(code))[:-1]]
    res = np.empty(DRAWS)
    for i in range(DRAWS):
        o = np.lexsort((rng.random(n), code))
        rank = np.empty(n, int); rank[o] = np.arange(n) - start[code[o]]
        res[i] = -r[rank < k[code]].sum() / n
    return res.mean(), res.std(), res


rows, srows, out = [], [], []
P = lambda *a: out.append(" ".join(str(y) for y in a))
P(f"entries {len(E)} (dropped {miss:.4%} without index context); setups {E.setup.nunique()}; train days {E[E.split=='train'].date.nunique()}, "
  f"valid days {E[E.split=='valid'].date.nunique()}; N {N_CFG}, bar {BAR:.2f} (conservative incl. giveback lineage {BAR_CONS:.2f})")
for name, vv in CFG.items():
    for sp in ("train", "valid"):
        w = (E.split == sp).to_numpy()
        x, v = E[w], vv[w]
        st = stats(x, v)
        rm, rsd, res = random_ctrl(x, v)
        st.update(config=name, split=sp, rand_delta_mean=rm, rand_delta_sd=rsd, beats_random_share=(res < st["delta"]).mean())
        rows.append(st)
        for su, xs in x.groupby("setup"):
            vs = v[(x.setup == su).to_numpy()]
            a = stats(xs, vs)
            srows.append(dict(config=name, split=sp, setup=su, **{k_: a[k_] for k_ in
                         ("n", "par_win", "par_avgR", "skip_share", "kept_n", "kept_win", "kept_avgR", "skipped_avgR", "delta", "t_delta", "excess", "t_excess")}))
R = pd.DataFrame(rows)
cols = ["config", "split"] + [c for c in R.columns if c not in ("config", "split")]
R = R[cols]


def verdict(c):
    tr, va = R[(R.config == c) & (R.split == "train")].iloc[0], R[(R.config == c) & (R.split == "valid")].iloc[0]
    fails = []
    if not (tr.delta > 0 and va.delta > 0): fails.append("delta<=0 train or valid")
    if not va.t_delta >= BAR: fails.append(f"valid t {va.t_delta:.2f} < {BAR:.2f}")
    if not (tr.excess > 0 and va.excess > 0 and va.t_excess >= 1.65): fails.append(f"random-skip control (excess t {va.t_excess:.2f})")
    if not (va.delta_up > 0 and va.delta_down > 0): fails.append("valid up/down")
    return "CANDIDATE" if not fails else "fail: " + "; ".join(fails)


R["verdict"] = R.config.map({c: verdict(c) for c in CFG})
R.round(4).to_csv(OUT / "results.csv", index=False)
B = pd.DataFrame(srows); B.round(4).to_csv(OUT / "by_setup.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 50)
show = ["config", "split", "n", "days", "par_win", "par_avgR", "skip_share", "kept_win", "kept_avgR", "skipped_avgR", "delta", "t_delta",
        "delta_ex_best_day", "rand_delta_mean", "beats_random_share", "excess", "t_excess", "delta_up", "delta_flat", "delta_down"]
P("\nPOOLED (R per parent trade; skipped = 0 R)")
P(R[show].round(4).to_string(index=False))
P("\nVERDICTS"); P(R[R.split == "valid"][["config", "verdict"]].to_string(index=False))
P("\nparent by regime (avg R):"); P(R[R.config == list(CFG)[0]][["split", "par_avgR_up", "par_avgR_flat", "par_avgR_down"]].round(4).to_string(index=False))
open(OUT / "veto_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
