"""RISK-BUDGET replay (live, walk-forward, downsize only): each setup's lots in week w are scaled by
w = min(1, K / past daily-R sd of that setup) using only data before week w (>= 5 past sessions; no history -> 1).
Control: uniform size cut matched to the same total exposure per account-week (sum of weights), and 500 random
per-setup weight shuffles within account-week (same weights, random setups). Book = each account's daily R.
Configs: K in {2, 3, 5} = 3. Read-only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
SCR = sys.argv[1]
t = pd.read_parquet(f"{SCR}/live.parquet")
t = t[t.date >= "2026-10-23"].copy() if len(sys.argv) < 3 else t
t["wk"] = pd.to_datetime(t.date).dt.to_period("W-FRI").astype(str)
full = pd.read_parquet(f"{SCR}/live.parquet"); full["wk"] = pd.to_datetime(full.date).dt.to_period("W-FRI").astype(str)
sd = {}
for w in sorted(t.wk.unique()):
    past = full[full.wk < w]
    d = past.groupby(["strategy", "date"]).r.sum().groupby("strategy").agg(["std", "count"])
    sd[w] = d[d["count"] >= 5]["std"]
def stats_(day):
    tot = day.sum(); wk = day.groupby(pd.to_datetime(day.index.get_level_values("date")).to_period("W-FRI").astype(str)).sum()
    return tot, day.std(ddof=1), day.min(), day.nsmallest(5).mean(), int((day <= 0).sum())
rng = np.random.default_rng(11)
for K in [2, 3, 5]:
    t["w"] = [min(1.0, K / sd[w].get(s, np.nan)) if pd.notna(sd[w].get(s, np.nan)) and sd[w].get(s) > 0 else 1.0 for w, s in zip(t.wk, t.strategy)]
    cw = t.groupby(["account", "wk"]).w.transform("mean")
    t["rb"] = t.r * t.w; t["rc"] = t.r * cw
    base = t.groupby(["account", "date"]).r.sum(); rb = t.groupby(["account", "date"]).rb.sum(); rc = t.groupby(["account", "date"]).rc.sum()
    # random control: shuffle weights across setups within account-week (setup-level permutation)
    rnd_tot, rnd_worst5, rnd_red = [], [], []
    sw = t[["account", "wk", "strategy"]].drop_duplicates()
    sw = sw.merge(t.groupby(["account", "wk", "strategy"]).w.first().rename("w0").reset_index())
    for i in range(200):
        sw["wr"] = sw.groupby(["account", "wk"]).w0.transform(lambda x: rng.permutation(x.values))
        tr = t.merge(sw[["account", "wk", "strategy", "wr"]], on=["account", "wk", "strategy"])
        dd = (tr.r * tr.wr).groupby([tr.account, tr.date]).sum()
        rnd_tot.append(dd.sum()); rnd_worst5.append(dd.groupby(level=0).apply(lambda x: x.nsmallest(5).mean()).sum()); rnd_red.append(int((dd <= 0).sum()))
    print(f"\nK = {K}: mean weight {t.w.mean():.2f} (share of lots cut at all {(t.w<1).mean():.2f})")
    print("  account     base R   RB R   cut R | base sd  RB sd  cut sd | base worst  RB worst  cut worst | red base/RB")
    agg = []
    for a in sorted(t.account.unique()):
        b, r_, c = base[a], rb[a], rc[a]
        agg.append((b.sum(), r_.sum(), c.sum(), b.nsmallest(5).mean(), r_.nsmallest(5).mean(), c.nsmallest(5).mean(), int((b<=0).sum()), int((r_<=0).sum())))
        print(f"  {a:10s} {b.sum():7.1f} {r_.sum():7.1f} {c.sum():7.1f} | {b.std():6.1f} {r_.std():6.1f} {c.std():6.1f} | {b.min():8.1f} {r_.min():8.1f} {c.min():8.1f} | {int((b<=0).sum())}/{int((r_<=0).sum())}")
    A = np.array(agg)
    print(f"  ALL: R base {A[:,0].sum():.0f}  RB {A[:,1].sum():.0f}  uniform cut {A[:,2].sum():.0f}  | worst-5 avg summed: base {A[:,3].sum():.0f} RB {A[:,4].sum():.0f} cut {A[:,5].sum():.0f} | red days base {int(A[:,6].sum())} RB {int(A[:,7].sum())}")
    print(f"  random weight-shuffle control (200): R {np.mean(rnd_tot):.0f} [{np.percentile(rnd_tot,2.5):.0f},{np.percentile(rnd_tot,97.5):.0f}]  RB pct {np.mean(np.array(rnd_tot) < A[:,1].sum())*100:.0f}; worst-5 {np.mean(rnd_worst5):.0f} [{np.percentile(rnd_worst5,2.5):.0f},{np.percentile(rnd_worst5,97.5):.0f}] RB pct {np.mean(np.array(rnd_worst5) < A[:,4].sum())*100:.0f}; red days {np.mean(rnd_red):.0f}")
    # per-setup effect (remedy rule): how many setups improve / worsen vs uniform cut (R contributed)
    ps = t.groupby("strategy")[["rb", "rc"]].sum(); dlt = ps.rb - ps.rc
    print(f"  per-setup vs uniform cut: better {int((dlt>0.5).sum())}, worse {int((dlt<-0.5).sum())}, ~same {int((dlt.abs()<=0.5).sum())}; worst 3 deltas {dlt.nsmallest(3).round(1).to_dict()}")
