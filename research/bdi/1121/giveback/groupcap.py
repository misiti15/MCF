"""Give-back remedy GC1 / GC2 (PLAN.md): correlated-group lot cap inside each setup's book, scored on the 11-19 top-10
benchmark T1 signals (bench10 normal way: add_r LR8 + borrow, home-account book). Groups = average-linkage clusters of
daily-return correlation >= 0.85 on FIT-period closes only. Also a descriptive replay on Primary's live week.
Usage: python groupcap.py <scratch dir with trades_t1.parquet, etb_rate.parquet, j/week_trades.parquet>
Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402
THR = 0.85
etb = pd.read_parquet(S / "etb_rate.parquet").rate
T = B.add_r(pd.read_parquet(S / "trades_t1.parquet"))
T["half"] = B.half(T.date)
T = T[T.half != "none"].reset_index(drop=True)
B.no_locked(T.date.unique())
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402  (lib.daily drops the locked block, as every 2-year study)
D = lib.daily()[["symbol", "date", "close"]].copy()
D["date"] = D.date.astype(str); D["symbol"] = D.symbol.astype(str)
B.no_locked(D.date.unique())
fit = (B.half(D.date) == "fit")
C = D[fit].pivot_table(index="date", columns="symbol", values="close").sort_index().pct_change(fill_method=None)


def groups_for(syms):
    syms = [s for s in syms if s in C.columns and C[s].notna().sum() >= 60]
    if len(syms) < 2:
        return {}
    cm = np.array(C[syms].corr(min_periods=60).fillna(0).to_numpy(), copy=True)
    np.fill_diagonal(cm, 1.0)
    dist = np.clip(1 - cm, 0, 2)
    Z = linkage(squareform(dist, checks=False), "average")
    lab = fcluster(Z, t=1 - THR, criterion="distance")
    return {s: f"g{l}" for s, l in zip(syms, lab)}


def book_g(t, rules, grp, gcap):
    """bench10.book + a per-group open-lot cap (gcap None = the plain book)."""
    t = t[t.entry >= 5.0]
    t = t[(t.side > 0) | t.symbol.map(etb).fillna(0).ge(0.9)]
    if rules["cf"] is not None:
        t = t[t.stop_cost_r <= rules["cf"]]
    if not len(t):
        return t
    t = t.sort_values(["date", "em", "symbol"], kind="mergesort").reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    em, xm, sy, rr = t.em.values, t.xm.values, t.symbol.values, t.r.values
    gg = np.array([grp.get(s, s) for s in sy])
    for _, idx in t.groupby("date").indices.items():
        open_, real = [], 0.0
        for i in idx:
            still = []
            for (x, s, g, r) in open_:
                if x <= em[i]:
                    real += r
                else:
                    still.append((x, s, g, r))
            open_ = still
            if rules["latch"] is not None and real <= rules["latch"] + 1e-12:
                continue
            if len(open_) >= rules["cap"] or sum(1 for o in open_ if o[1] == sy[i]) >= rules["symcap"]:
                continue
            if gcap is not None and sum(1 for o in open_ if o[2] == gg[i]) >= gcap:
                continue
            keep[i] = True
            open_.append((xm[i], sy[i], gg[i], rr[i]))
    return t[keep].reset_index(drop=True)


def st(b):
    if not len(b):
        return dict(n=0, R=0.0)
    d = b.groupby("date").r.sum()
    return dict(n=len(b), R=round(b.r.sum(), 2), avg=round(b.r.mean(), 4),
                wobd=round(b[b.date != d.idxmax()].r.mean(), 4), t=round(B.clustered_t(b), 2))


rng = np.random.default_rng(1121)
inv = {s: a for s, _, a in B.SETUPS}
rows, gsz = [], {}
for setup, g in T.groupby("setup"):
    rules = B.BOOK[inv[setup]]
    grp = groups_for(sorted(g.symbol.unique()))
    multi = pd.Series(grp).value_counts(); gsz[setup] = int((multi >= 2).sum())
    base = book_g(g, rules, grp, None)
    top = base.r.quantile(0.9)
    for cfg, gcap in (("GC1", 1), ("GC2", 2)):
        v = book_g(g, rules, grp, gcap)
        for h in ("fit", "check"):
            b0, b1 = base[base.half == h], v[v.half == h]
            s0, s1 = st(b0), st(b1)
            k0 = set(zip(b0.symbol, b0.date, b0.tod)); k1 = set(zip(b1.symbol, b1.date, b1.tod))
            removed = len(k0 - k1); added = len(k1 - k0)
            tw = b0[b0.r >= top]; tw_kept = np.mean([(s, d, x) in k1 for s, d, x in zip(tw.symbol, tw.date, tw.tod)]) if len(tw) else 1.0
            # random removal control: drop the same number of the base's trades at random from the same setup-days
            pct = np.nan
            if h == "check" and removed > 0:
                dR = s1["R"] - s0["R"]
                draws = [-(b0.r.sample(removed, random_state=int(rng.integers(1e9))).sum()) for _ in range(500)]
                pct = round(float((np.array(draws) < dR).mean() * 100), 1)
            rows.append(dict(setup=setup, home=inv[setup], cfg=cfg, half=h, groups_multi=gsz[setup], n0=s0["n"], n1=s1["n"],
                             kept=round(s1["n"] / s0["n"], 3) if s0["n"] else np.nan, removed=removed, added=added,
                             R0=s0["R"], R1=s1["R"], dR=round(s1["R"] - s0["R"], 2), avg0=s0.get("avg"), avg1=s1.get("avg"),
                             wobd0=s0.get("wobd"), wobd1=s1.get("wobd"), top10_kept=round(float(tw_kept), 3), rand_pct=pct))
R = pd.DataFrame(rows)
R.to_csv(HERE / "groupcap_results.csv", index=False)
pd.set_option("display.width", 250)
out = [R.to_string(index=False)]
for cfg in ("GC1", "GC2"):
    for h in ("fit", "check"):
        x = R[(R.cfg == cfg) & (R.half == h) & (R.removed + R.added > 0)]
        out.append(f"{cfg} {h}: setups affected {len(x)}, better {int((x.dR > 0).sum())} ({x[x.dR > 0].dR.sum():+.1f}R), "
                   f"worse {int((x.dR < 0).sum())} ({x[x.dR < 0].dR.sum():+.1f}R), total {x.dR.sum():+.1f}R")
# live week replay (descriptive): Primary journal 11-16..11-20, entry order, the same groups (FIT correlations)
W = pd.read_parquet(S / "j/week_trades.parquet")
W = W[W.acct == "Primary"].copy()
W["et"] = pd.to_datetime(W.entry_time, utc=True, format="mixed"); W["xt_"] = pd.to_datetime(W.exit_time, utc=True, format="mixed")
for cfg, gcap in (("GC1", 1), ("GC2", 2)):
    blocked = []
    for (d, s), g in W.sort_values("et").groupby(["date", "strategy"]):
        grp = groups_for(sorted(g.symbol.unique()))
        open_ = []
        for r in g.itertuples():
            open_ = [o for o in open_ if o[0] > r.et]
            gg = grp.get(r.symbol, r.symbol)
            if sum(1 for o in open_ if o[1] == gg) >= gcap:
                blocked.append((d, s, r.symbol, r.R)); continue
            open_.append((r.xt_, gg))
    bl = pd.DataFrame(blocked, columns=["date", "strategy", "symbol", "R"])
    out.append(f"live week Primary {cfg}: blocked {len(bl)} lots, their R {bl.R.sum():+.2f} (cap gain = {-bl.R.sum():+.2f}R) | "
               + (bl.groupby(["date", "strategy"]).R.agg(["size", "sum"]).round(2).to_string() if len(bl) else ""))
txt = "\n".join(out)
(HERE / "groupcap_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
