"""HIST-MOM score (4 pre-declared feature tests, written before scoring): within-day paired lift of strong-prior names vs
the rest among the same generic longs (same day, same entry time). LIVE-L costs (primshorts_1126 cells_live.json; stop
exits 'stop', else 'market'); LR8-style flat add not used here. Splits: FIT 2024-09..10 + 2025-03..09 (report only),
CHECK 2025-10-01..2026-11-04, T2 2023-01-03..2024-09-13. Day t = mean/SE of the daily (feature - rest) difference.
Usage: python hist_score.py <scratch>. Educational only - not financial advice."""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wtx_long_edge/research/primshorts_1126")
import calib_live as CL  # noqa: E402
S = sys.argv[1]
CELLS = json.load(open("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wtx_long_edge/research/primshorts_1126/cells_live.json"))
X = pd.read_parquet(f"{S}/hist.parquet")
X["cost"] = CL.predict_R(CELLS, X.entry.values, X.risk.values, np.where(X.stopped == 1, "stop", "market"))
X["r"] = X.gross_r - X.cost
X["stop_bp"] = X.risk / X.entry * 1e4
d = X.date
X["split"] = np.select([(X.src == "t2") & (d >= "2023-01-03") & (d <= "2024-09-13"), (X.src == "t1") & (d >= "2025-10-01"),
                        X.src == "t1"], ["T2", "CHECK", "FIT"], "other")
X = X[X.split != "other"]
H = {"H1 prev-day > +1%": X.prev_ret > 1, "H2 5-day > +3%": X.ret5 > 3, "H3 prev>+1% or 5d>+3%": (X.prev_ret > 1) | (X.ret5 > 3)}
def paired(sub, m):
    a = sub[m].groupby(["date", "t"]).r.mean(); b = sub[~m].groupby(["date", "t"]).r.mean()
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    dd = (j.a - j.b).groupby(level=0).mean()
    return dd.mean(), dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))), len(dd)
def dayt(x): return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
out = []
for sp in ["FIT", "CHECK", "T2"]:
    U = X[X.split == sp]
    print(f"\n#### {sp}: generic longs {len(U):,}, days {U.date.nunique()}, avg net {U.r.mean():.3f} (gross {U.gross_r.mean():.3f}, cost {U.cost.mean():.3f})")
    for name, m in H.items():
        for sub_name, sub in [("all", U), ("stop>=100bp", U[U.stop_bp >= 100])]:
            mm = m.loc[sub.index]
            lift, t, nd = paired(sub, mm)
            g = sub[mm]; dg = g.groupby("date").r.mean()
            row = {"split": sp, "test": name, "subset": sub_name, "n_feat": int(mm.sum()), "share": mm.mean(), "avg_feat": g.r.mean(),
                   "avg_rest": sub[~mm].r.mean(), "gross_feat": g.gross_r.mean(), "lift": lift, "lift_t": t, "days": nd,
                   "feat_day_t": dayt(dg)}
            out.append(row)
    print("prev-day return buckets (net avg R, n):")
    print(U.groupby(pd.cut(U.prev_ret, [-99, -3, -1, 0, 1, 3, 99]), observed=True).r.agg(["count", "mean"]).round(4).T.to_string())
    print("by entry time x H1:"); print(U.groupby(["t", U.prev_ret > 1]).r.mean().unstack().round(4).to_string())
R = pd.DataFrame(out); pd.set_option("display.width", 250)
print("\n" + R.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
# Big-day check on CHECK/T2 for H1 lift: without the single best lift day
for sp in ["CHECK", "T2"]:
    U = X[X.split == sp]; m = H["H1 prev-day > +1%"].loc[U.index]
    a = U[m].groupby("date").r.mean(); b = U[~m].groupby("date").r.mean(); dd = (a - b).dropna()
    print(f"{sp} H1 daily lift: mean {dd.mean():.4f}, w/o best day {dd.drop(dd.idxmax()).mean():.4f}, share of days >0 {(dd>0).mean():.2f}, "
          f"by year: " + ", ".join(f"{y}: {v:.4f}" for y, v in dd.groupby(dd.index.str[:4]).mean().items()))
# Descriptive: stop width (bp) buckets, net / gross / cost per split (is the wide-stop lift just cost?)
print("\nstop width buckets (n, net, gross, cost):")
for sp in ["FIT", "CHECK", "T2"]:
    U = X[X.split == sp]
    t = U.groupby(pd.cut(U.stop_bp, [0, 50, 100, 200, 1e9]), observed=True).agg(n=("r", "size"), net=("r", "mean"), gross=("gross_r", "mean"), cost=("cost", "mean"))
    print(sp); print(t.round(4).to_string())
