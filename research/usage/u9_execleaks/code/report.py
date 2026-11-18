"""U9 tables from u9_whatif.csv.gz: per-setup W1, B2 fit/check verdict, per-setup improve/worsen counts."""
import sys, numpy as np, pandas as pd
S, OUT = sys.argv[1], sys.argv[2]
o = pd.read_csv(f"{S}/u9_whatif.csv.gz")
def wobd(g):
    d = g.groupby("day").R.sum(); tot = d.sum()
    if len(d) < 2: return np.nan, np.nan
    b = d.idxmax(); n_wo = (g.day != b).sum()
    return (tot - d[b]) / max(n_wo, 1), (d[b] / tot if tot > 0 else np.nan)
def tstat(x):
    x = x.dropna(); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan
# W1 per setup
w, r = o[o.cfg == "W1"].dropna(subset=["R"]), o[o.cfg == "W1-ref"].dropna(subset=["R"])
rows = []
for s, g in w.groupby("strategy"):
    a, sh = wobd(g); h = r[r.strategy == s]
    rows.append(dict(setup=s, etb_n=len(g), etb_days=g.day.nunique(), etb_avgR=g.R.mean(), etb_totR=g.R.sum(), etb_t=tstat(g.R),
                     etb_wo_best=a, etb_best_share=sh, etb_rand=g.R_rand.mean(), traded_n=len(h), traded_engineR=h.R.mean(),
                     traded_liveR=h.R_live.mean(), blocked_share=len(g) / (len(g) + len(h)) if len(h) + len(g) else np.nan))
W1 = pd.DataFrame(rows).sort_values("etb_n", ascending=False)
W1.round(4).to_csv(f"{OUT}/u9_w1_etb_by_setup.csv", index=False)
a, sh = wobd(w)
print(f"W1 all: n={len(w)} setups={w.strategy.nunique()} avg={w.R.mean():+.4f} tot={w.R.sum():+.1f} t={tstat(w.R):.2f} wo_best={a:+.4f} share={sh} rand={w.R_rand.mean():+.4f}")
print(f"W1-ref (traded, same setups): n={len(r)} engine={r.R.mean():+.4f} live={r.R_live.mean():+.4f} rand={r.R_rand.mean():+.4f}")
pos = W1[(W1.etb_n >= 20)]
print("setups with >=20 ETB skips:", len(pos), " as-if avg>0:", (pos.etb_avgR > 0).sum(), " as-if > traded engine:", (pos.etb_avgR > pos.traded_engineR).sum(),
      " as-if > 0 and t>=1.5 and wo_best>0:", ((pos.etb_avgR > 0) & (pos.etb_t >= 1.5) & (pos.etb_wo_best > 0)).sum())
print(W1.head(25).round(3).to_string(index=False))
# B2 fit / check
b = o[o.cfg == "B2"].dropna(subset=["R"]).copy(); b["half"] = np.where(b.day <= "2026-10-22", "fit", "check")
for h, g in b.groupby("half"):
    a, sh = wobd(g)
    print(f"B2 {h}: n={len(g)} days={g.day.nunique()} avg={g.R.mean():+.4f} tot={g.R.sum():+.2f} t={tstat(g.R):.2f} wo_best={a:+.4f} share={sh} rand={g.R_rand.mean():+.4f}")
bs = b.groupby("strategy").agg(n=("R", "size"), B2_avgR=("R", "mean"), B2_totR=("R", "sum"), rand=("R_rand", "mean")).sort_values("n", ascending=False)
bc = o[o.cfg == "diag-bt-credit"].dropna(subset=["R"]).groupby("strategy").agg(btcredit_totR=("R", "sum"), btcredit_avgR=("R", "mean"))
bs = bs.join(bc); bs.round(4).to_csv(f"{OUT}/u9_w2_target_by_setup.csv")
print(bs.round(3).to_string())
print("B2 vs B1 per setup: improve", (bs.B2_totR > 0).sum(), "worse", (bs.B2_totR < 0).sum(), "sum gain", bs.B2_totR[bs.B2_totR > 0].sum().round(2), "sum loss", bs.B2_totR[bs.B2_totR < 0].sum().round(2))
d = o[o.cfg == "diag-bt-credit"].dropna(subset=["R"])
print(f"diag backtest credit: n={len(d)} avg={d.R.mean():+.3f} tot={d.R.sum():+.1f}")
