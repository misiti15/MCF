"""Swing leads swing1104-L7 / L8 (research/bdi/swings/hypotheses.jsonl, pre-registered 2026-11-04 before any read):
ONE pre-registered 2-year backtest each, on the latch_1103-style two-year trade lists of every enabled lab setup
(research/bdi/1104/bt_all.py -> <scratch>/bt/sig_<month>.parquet; production costs + tod multiplier; stop first, 15:55
flatten). Locked block 2024-11-01..2025-02-28: not in the frame directory, asserted absent on every table here.
  L7  pool = every short lab setup; class A = entry-bar qqq_fo >= +0.75%.
  L8  pool = every CWT14-failbrk-*-long setup; class A = IWM fromOpen at the entry bar <= -0.50%.
R = excess over the setup's own mean on the same split (train < 2025-09-01, valid >= 2025-09-01). Day-clustered t.
PASS (fixed in hypotheses.jsonl): A excess <= -0.10R in train AND valid, t <= -bar, n_A >= 300 on >= 30 days, filter keeps
>= 80% of the pool's trades and >= 90% of its top-decile winners. Also: R by SPY day type (o-c > +0.25 up, < -0.25 down,
else quiet) and by SPY vs open at 10:00.
Usage: python leads_bt.py <scratch> <N_tonight>      Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib
from mcf.research.gates import t_required
S = Path(sys.argv[1]); N = int(sys.argv[2]); BAR = t_required(N); HERE = Path(__file__).resolve().parent
LK0, LK1 = "2024-11-01", "2025-02-28"; SPLIT = "2025-09-01"
T = pd.concat([pd.read_parquet(p) for p in sorted((S / "bt").glob("sig_*.parquet"))], ignore_index=True)
T["date"] = T.date.astype(str); assert not T.date.between(LK0, LK1).any()
ctx = pd.concat([lib.load_context(m) for m in lib.months()], ignore_index=True); ctx["date"] = ctx.date.astype(str)
assert not ctx.date.between(LK0, LK1).any()
iwm = pd.concat([lib.load_month(m, columns=["symbol", "date", "tod", "fromOpen"]).query("symbol == 'IWM'") for m in lib.months()])
iwm["date"] = iwm.date.astype(str); iwm = iwm.rename(columns={"fromOpen": "iwm_fo"})[["date", "tod", "iwm_fo"]]
dly = lib.daily(); dly = dly[dly.symbol == "SPY"].copy(); dly["date"] = dly.date.astype(str)
oc = (dly.set_index("date").close / dly.set_index("date").open - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
s10 = ctx[ctx.tod == 1000].set_index("date").spy_fo
T = T.merge(ctx[["date", "tod", "spy_fo", "qqq_fo"]], on=["date", "tod"], how="left").merge(iwm, on=["date", "tod"], how="left")
T["split"] = np.where(T.date < SPLIT, "train", "valid"); T["dtype"] = T.date.map(dtype)
T["s10"] = np.where(T.date.map(s10) >= 0, "SPY>open@10", "SPY<open@10")
T["ex"] = T.r - T.groupby(["setup", "split"]).r.transform("mean")
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
pr(f"trade lists: {len(T)} trades, {T.setup.nunique()} setups, {T.date.nunique()} sessions {T.date.min()}..{T.date.max()} (locked block absent); "
   f"configs tonight N={N}, bar t {BAR:.2f}; qqq_fo coverage {T.qqq_fo.notna().mean():.1%}, iwm coverage {T.iwm_fo.notna().mean():.1%}")
def ctt(x, col="ex"):
    g = x.groupby("date")[col].agg(["sum", "size"]); mu = g["sum"].sum() / g["size"].sum(); G = len(g)
    v = ((g["sum"] - mu * g["size"]) ** 2).sum() / g["size"].sum() ** 2 * G / max(G - 1, 1)
    return mu, mu / np.sqrt(v) if v > 0 else np.nan, G
def lead(name, pool, A):
    pool = pool.copy(); pool["A"] = A.reindex(pool.index).fillna(False).astype(bool)
    a, b = pool[pool.A], pool[~pool.A]
    mu, t, G = ctt(a); top = pool.r >= pool.r.quantile(0.9)
    keep, keep_top = 1 - pool.A.mean(), 1 - pool.A[top].mean()
    sp = {s: (pool[(pool.split == s) & pool.A].ex.mean(), int(((pool.split == s) & pool.A).sum()), pool[(pool.split == s) & ~pool.A].r.mean()) for s in ("train", "valid")}
    dA = a.groupby("date").ex.sum(); wob = (dA.sum() - dA.max()) / max(len(a) - (a.date == dA.idxmax()).sum(), 1) if len(dA) > 1 else np.nan
    ok = bool(sp["train"][0] <= -0.10 and sp["valid"][0] <= -0.10 and t <= -BAR and len(a) >= 300 and G >= 30 and keep >= 0.8 and keep_top >= 0.9)
    pr(f"\n{name}: pool {len(pool)} trades / {pool.setup.nunique()} setups (avg {pool.r.mean():+.3f}R); class A n {len(a)} on {G} days raw {a.r.mean():+.3f}R, "
       f"excess {mu:+.3f}R, day-clustered t {t:+.2f}; class B raw {b.r.mean():+.3f}R")
    pr(f"   train: A excess {sp['train'][0]:+.3f} (n {sp['train'][1]}), B raw {sp['train'][2]:+.3f} | valid: A excess {sp['valid'][0]:+.3f} (n {sp['valid'][1]}), B raw {sp['valid'][2]:+.3f}")
    pr(f"   as a filter: keeps {keep:.1%} of trades, {keep_top:.1%} of top-decile winners; pool avg after the filter {b.r.mean():+.3f}R vs {pool.r.mean():+.3f}R; "
       f"A excess w/o its best day {wob:+.3f}R")
    for col in ("dtype", "s10"):
        pr(f"   by {col}: " + "; ".join(f"{k} A n {len(g[g.A])} raw {g[g.A].r.mean():+.3f} ex {g[g.A].ex.mean():+.3f} | B n {len(g[~g.A])} raw {g[~g.A].r.mean():+.3f}" for k, g in pool.groupby(col)))
    pr(f"   PASS {ok}")
    return dict(lead=name, n_A=len(a), days=G, excess=mu, t=t, train=sp["train"][0], valid=sp["valid"][0], keep=keep, keep_top=keep_top, wob=wob, PASS=ok)
out = [lead("swing1104-L7 short guard (qqq_fo >= +0.75%)", T[T.side == -1], T.qqq_fo >= 0.75)]
fb = T[T.setup.str.match(r"CWT14-failbrk-.*-long$") & (T.side == 1)]
pr(f"\nL8 pool setups: {sorted(fb.setup.unique())}")
out.append(lead("swing1104-L8 failbrk-long guard (IWM fo <= -0.50%)", fb, fb.iwm_fo <= -0.5))
# descriptive, no test: the book's short side vs qqq_fo buckets
T["qb"] = pd.cut(T.qqq_fo, [-99, -0.75, -0.25, 0.25, 0.75, 99])
pr("\ndescriptive: short lab entries by qqq_fo bucket (raw R): " + "; ".join(f"{k} n {len(g)} {g.r.mean():+.3f}" for k, g in T[T.side == -1].groupby("qb", observed=True)))
pr("descriptive: long lab entries by qqq_fo bucket (raw R): " + "; ".join(f"{k} n {len(g)} {g.r.mean():+.3f}" for k, g in T[T.side == 1].groupby("qb", observed=True)))
pd.DataFrame(out).to_csv(HERE / "leads_bt_results.csv", index=False)
pr("\nEducational only - not financial advice."); (HERE / "leads_bt_out.txt").write_text("\n".join(P) + "\n")
