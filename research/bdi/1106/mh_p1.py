"""MH1106-P1 (MH_PLAN.md, pre-registered): defensive-rotation long at the 09:50 lab bar on up opens.
Usage: python mh_p1.py   -> mh_p1_out.txt. Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
import lib  # noqa: E402
from mcf.research.gates import tod_cost_mult  # noqa: E402
HERE = Path(__file__).resolve().parent; LOCK = ("2024-11-01", "2025-02-28"); TZ = "America/New_York"
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
# 60-session daily beta, lagged one session
D = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet"); D["date"] = D.date.astype(str)
C = D.pivot_table(index="date", columns="symbol", values="close").sort_index(); R = C.pct_change(fill_method=None)
sp = R["SPY"]; cov = R.rolling(60, min_periods=40).cov(sp); var = sp.rolling(60, min_periods=40).var()
BETA = cov.div(var, axis=0).shift(1)                           # known before the session
spy_d = D[D.symbol == "SPY"].set_index("date"); oc = (spy_d.close / spy_d.open - 1) * 100
dtype = pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index)
rows = []
for m in lib.months():
    if m in lib.LOCKED_MONTHS: continue
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "fromOpen", "atr_d", "adv20", "r_long_t1s1", "win_long_t1s1"])
    f = f[f.tod == 950].copy(); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    assert not ((f.date >= LOCK[0]) & (f.date <= LOCK[1])).any()
    cx = pd.read_parquet(f"/home/user/MCF/research/history2y/data/context/month={m}.parquet"); cx = cx[cx.tod == 950][["date", "spy_fo"]]
    cx["date"] = cx.date.astype(str); f = f.merge(cx, on="date", how="left"); rows.append(f)
F = pd.concat(rows, ignore_index=True)
F = F[(F.adv20 >= 95e6) & (F.close >= 5) & F.r_long_t1s1.notna() & (F.spy_fo >= 0.40)].copy()
F["beta"] = [BETA.at[d, s] if (d in BETA.index and s in BETA.columns) else np.nan for d, s in zip(F.date, F.symbol)]
# production costs (bt_all): entry + exit (0.01 + 1 bp) x tod multiplier, + 0.02 stop slip on losers; lab r already has 2 x 0.01
Ru = 0.25 * F.atr_d; e = F.close
extra = (2 * (0.01 + e * 1e-4) * tod_cost_mult(F.tod.to_numpy()) - 2 * 0.01 + np.where(F.r_long_t1s1 < 0, 0.02, 0.0)) / Ru
F["r"] = F.r_long_t1s1 - extra
F["A"] = (F.beta <= 0.50) & (F.fromOpen <= 0.10)
F["half"] = np.where(F.date <= "2026-02-28", "TRAIN", "VALID"); F["dtype"] = F.date.map(dtype); F["month"] = F.date.str[:7]
A, Bs = F[F.A], F[~F.A]
pr(f"qualifying days (SPY >= +0.40% at the 09:50 bar) {F.date.nunique()}; class A {len(A):,} on {A.date.nunique()} days; base {len(Bs):,}; beta known {F.beta.notna().mean():.0%}")
def dt(x):
    g = x.groupby("date").ex.mean(); return g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 else np.nan
bm = Bs.groupby("date").r.mean(); A = A.assign(ex=A.r - A.date.map(bm))
for h in ("TRAIN", "VALID", "ALL"):
    a = A if h == "ALL" else A[A.half == h]; b = Bs if h == "ALL" else Bs[Bs.half == h]
    pr(f"{h}: A n {len(a):,} days {a.date.nunique()} win {a.win_long_t1s1.mean():.1%} avg R {a.r.mean():+.3f} | base n {len(b):,} win {b.win_long_t1s1.mean():.1%} avg {b.r.mean():+.3f} | excess {a.ex.mean():+.3f} day-t {dt(a):.2f}")
g = A.groupby("dtype").agg(n=("r", "size"), days=("date", "nunique"), avgR=("r", "mean"), ex=("ex", "mean")).round(3)
pr("\nQDAY split (SPY open-to-close; SPY above its open at 10:00 by construction):\n" + g.to_string())
gb = Bs.groupby("dtype").r.mean().round(3); pr("base avg R by day type: " + gb.to_dict().__repr__())
dsum = A.groupby("date").r.sum().sort_values(); best = dsum.index[-1]
wo = A[A.date != best].r.mean(); share = dsum.iloc[-1] / dsum.sum() if dsum.sum() > 0 else np.nan
mo = A.groupby("month").r.mean(); pr(f"avg R w/o best day {wo:+.3f} (best {best} {dsum.iloc[-1]:+.1f}R, share of total {share:.0%}); months positive {(mo > 0).mean():.0%} of {len(mo)}")
pr("per month avg R: " + " ".join(f"{k[2:]} {v:+.2f}" for k, v in mo.items()))
ok = (A[A.half == "TRAIN"].r.mean() > 0 and A[A.half == "VALID"].r.mean() > 0 and dt(A) >= 1.35 and g.loc["up", "avgR"] > 0 and
      ("down" in g.index and g.loc["down", "avgR"] > 0) and (mo > 0).mean() >= 0.54 and wo > 0 and len(A) >= 300 and A.date.nunique() >= 30)
pr(f"\nVERDICT (BAR90 1.35, N = 2 tonight): {'PASS -> Live Lab candidate' if ok else 'FAIL'}")
# live check 11-06 (in-sample): the same rule on the 11-06 frames
pr("Locked block never read (asserted). Configurations: 1. Educational only - not financial advice.")
(HERE / "mh_p1_out.txt").write_text("\n".join(P) + "\n")
