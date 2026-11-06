"""FB1 (research/bdi/1105/FB1_PLAN.md, pre-registered): does entering a short within 0.15 daily ATR of the session low
(selling the flush) lose across lab short families, and does selling the bounce (dist_lod >= 0.5 ATR, rsi5 >= 50) win?
ONE run of 4 configs on the 2-year lab trade lists (bt_lab1104), entry-bar features from the lab frames.
Usage: python fb1.py      Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib
from mcf.research.gates import t_required
N = 4; BAR = t_required(N); HERE = Path(__file__).resolve().parent
LK0, LK1 = "2024-11-01", "2025-02-28"; SPLIT = "2025-09-01"
T = pd.concat([pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet"))], ignore_index=True)
T["date"] = T.date.astype(str); assert not T.date.between(LK0, LK1).any()
F = []
for m in lib.months():
    f = lib.load_month(m, columns=["symbol", "date", "tod", "dist_lod_atr", "dist_hod_atr", "rsi5", "fromOpen"])
    f["date"] = f.date.astype(str); F.append(f)
F = pd.concat(F, ignore_index=True); assert not F.date.between(LK0, LK1).any()
Q = F[F.symbol == "QQQ"][["date", "tod", "dist_lod_atr", "fromOpen"]].rename(columns={"dist_lod_atr": "q_lod", "fromOpen": "q_fo"})
T = T.merge(F, on=["symbol", "date", "tod"], how="left").merge(Q, on=["date", "tod"], how="left")
dly = lib.daily(); dly = dly[dly.symbol == "SPY"].copy(); dly["date"] = dly.date.astype(str)
oc = (dly.set_index("date").close / dly.set_index("date").open - 1) * 100
T["dtype"] = T.date.map(pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index))
T["split"] = np.where(T.date < SPLIT, "train", "valid")
T["ex"] = T.r - T.groupby(["setup", "split"]).r.transform("mean"); T["fam"] = T.setup.str.split("-").str[0]
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
pr(f"trade lists {len(T)} trades, {T.setup.nunique()} setups, {T.date.nunique()} sessions {T.date.min()}..{T.date.max()} (locked block absent); "
   f"feature coverage {T.dist_lod_atr.notna().mean():.1%}, QQQ {T.q_lod.notna().mean():.1%}; configs N={N}, bar t {BAR:.2f}")
def ctt(x):
    g = x.groupby("date").ex.agg(["sum", "size"]); mu = g["sum"].sum() / g["size"].sum(); G = len(g)
    v = ((g["sum"] - mu * g["size"]) ** 2).sum() / g["size"].sum() ** 2 * G / max(G - 1, 1)
    return mu, (mu / np.sqrt(v) if v > 0 else np.nan), G
out, FAM = [], []
def run(name, pool, A, kind):
    pool = pool.copy(); pool["A"] = A.reindex(pool.index).fillna(False).astype(bool); a, b = pool[pool.A], pool[~pool.A]
    mu, t, G = ctt(a); top = pool.r >= pool.r.quantile(0.9); keep, keep_top = 1 - pool.A.mean(), 1 - pool.A[top].mean()
    sp = {s: (pool[(pool.split == s) & pool.A].ex.mean(), int(((pool.split == s) & pool.A).sum())) for s in ("train", "valid")}
    dA = a.groupby("date").ex.sum(); wob = (dA.sum() - dA.max()) / max(len(a) - (a.date == dA.idxmax()).sum(), 1)
    share = dA.max() / dA.sum() if dA.sum() != 0 else np.nan
    fam = pool.groupby("fam").apply(lambda g: pd.Series(dict(n=len(g), nA=int(g.A.sum()), exA=g[g.A].ex.mean() if g.A.any() else np.nan,
                                                              delta_avg=(g[~g.A].r.mean() - g.r.mean()) if g.A.any() else 0.0)), include_groups=False)
    fam["config"] = name; FAM.append(fam.reset_index())
    if kind == "guard":
        worse = int((fam.exA > 0).sum()); better = int((fam.exA < 0).sum())
        ok = bool(sp["train"][0] <= -0.10 and sp["valid"][0] <= -0.10 and t <= -BAR and len(a) >= 300 and G >= 30 and keep >= 0.8
                  and keep_top >= 0.9 and worse <= len(fam[fam.nA > 0]) / 3)
    else:
        worse = int((fam.exA < 0).sum()); better = int((fam.exA > 0).sum())
        ok = bool(sp["train"][0] >= 0.05 and sp["valid"][0] >= 0.05 and t >= BAR and len(a) >= 300 and G >= 30)
    pr(f"\n{name}: pool {len(pool)} / {pool.setup.nunique()} setups (avg {pool.r.mean():+.3f}R); class A n {len(a)} ({len(a) / len(pool):.1%}) on {G} days "
       f"raw {a.r.mean():+.3f}R, excess {mu:+.3f}R, day-t {t:+.2f}; class B raw {b.r.mean():+.3f}R")
    pr(f"   train A excess {sp['train'][0]:+.3f} (n {sp['train'][1]}) | valid A excess {sp['valid'][0]:+.3f} (n {sp['valid'][1]}); "
       f"A excess w/o best day {wob:+.3f}R (best day share {share:.0%})")
    if kind == "guard":
        pr(f"   as a filter: keeps {keep:.1%} of trades, {keep_top:.1%} of top-decile; pool avg {pool.r.mean():+.3f} -> {b.r.mean():+.3f}R")
    pr(f"   families (with class-A trades): {len(fam[fam.nA > 0])}; helped by the rule {better}, harmed {worse}; "
       + "; ".join(f"{k} nA {int(r.nA)} exA {r.exA:+.3f}" for k, r in fam[fam.nA > 0].sort_values("exA").iterrows()))
    pr("   by SPY day type: " + "; ".join(f"{k} A n {int(g.A.sum())} raw {g[g.A].r.mean():+.3f} ex {g[g.A].ex.mean():+.3f} | B raw {g[~g.A].r.mean():+.3f}"
                                         for k, g in pool.groupby("dtype")))
    pr(f"   PASS {ok}")
    out.append(dict(config=name, n_A=len(a), share_A=len(a) / len(pool), days=G, excess=mu, t=t, train=sp["train"][0], valid=sp["valid"][0],
                    keep=keep, keep_top=keep_top, wob=wob, best_share=share, fam_helped=better, fam_harmed=worse, PASS=ok))
S_ = T[T.side == -1]; L_ = T[T.side == 1]
run("FB1-S stock flush-chase guard (shorts, dist_lod_atr <= 0.15)", S_, S_.dist_lod_atr <= 0.15, "guard")
run("FB1-I index flush-chase guard (shorts, QQQ dist_lod <= 0.15 & fo <= -0.5%)", S_, (S_.q_lod <= 0.15) & (S_.q_fo <= -0.5), "guard")
run("FB1-L squeeze-chase guard (longs, dist_hod_atr <= 0.15)", L_, L_.dist_hod_atr <= 0.15, "guard")
run("FB1-B bounce-sold boost (shorts, dist_lod >= 0.5 & rsi5 >= 50)", S_, (S_.dist_lod_atr >= 0.5) & (S_.rsi5 >= 50), "boost")
pr("\ndescriptive (not scored): short raw R by entry dist_lod_atr bucket: " + "; ".join(
    f"{k} n {len(g)} {g.r.mean():+.3f} ex {g.ex.mean():+.3f}" for k, g in S_.groupby(pd.cut(S_.dist_lod_atr, [-1, .15, .3, .5, 1, 99]), observed=True)))
pr("descriptive: long raw R by entry dist_hod_atr bucket: " + "; ".join(
    f"{k} n {len(g)} {g.r.mean():+.3f} ex {g.ex.mean():+.3f}" for k, g in L_.groupby(pd.cut(L_.dist_hod_atr, [-1, .15, .3, .5, 1, 99]), observed=True)))
pd.DataFrame(out).to_csv(HERE / "fb1_results.csv", index=False); pd.concat(FAM).to_csv(HERE / "fb1_families.csv", index=False)
pr("\nEducational only - not financial advice."); (HERE / "fb1_out.txt").write_text("\n".join(P) + "\n")
