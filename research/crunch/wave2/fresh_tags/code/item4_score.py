"""Item 4 scoring (3 pre-registered configs, weight 0). Usage: python item4_score.py <lab_trades.parquet>
Educational only - not financial advice."""
import sys, math, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
from lib import daily
x = pd.read_parquet(sys.argv[1]); x["date"] = x.date.astype(str)
assert not x.date.between("2024-11-01", "2025-02-28").any() and x.date.max() <= "2026-10-05"
H1 = x.date <= "2025-09-30"
FIVE = ["L3-gap-slope-fromopen-FD", "NM-ETF-late-dip-di-long", "RW3-gapdn-rsi5pop-flowsell-short-FD",
        "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD"]
MF = [s for s in x.setup.unique() if s.startswith("MF")]
def tday(s):
    s = s.astype(float); return float(s.mean() / (s.std(ddof=1) / math.sqrt(len(s)))) if len(s) > 1 and s.std(ddof=1) > 0 else float("nan")
def skip_rule(base, hit, label, seed=1119, draws=2000):
    h = base[hit]; gain = -h.r.sum()
    rng = np.random.default_rng(seed); pool = base.r.to_numpy(); sims = []
    # same count, same setups' pool: draw per setup the same number of trades as hit in that setup
    per_n = h.setup.value_counts()
    groups = {s: base.r[base.setup == s].to_numpy() for s in per_n.index}
    for _ in range(draws):
        sims.append(-sum(rng.choice(groups[s], n, replace=False).sum() for s, n in per_n.items()))
    pct = float((np.array(sims) < gain).mean() * 100)
    days = sorted(base.date.unique())
    dg = (-h.groupby("date").r.sum()).reindex(days, fill_value=0.0)
    best = dg.idxmax()
    out = {"rule": label, "base_n": len(base), "base_avg": base.r.mean(), "skip_n": len(h), "skip_avg": h.r.mean(),
           "keep_avg": base[~hit].r.mean(), "skip_gain_R": gain, "rand_pct": pct, "t_day": tday(dg), "sessions": len(days),
           "gain_wo_best_day": gain - dg.max(), "best_day_share": dg.max() / gain if gain > 0 else float("nan"), "best_day": best,
           "H1_gain": -h[H1[h.index]].r.sum(), "H2_gain": -h[~H1[h.index]].r.sum()}
    per = h.groupby("setup").r.agg(["size", "sum"]); keep = base[~hit].groupby("setup").r.mean()
    out["per_setup"] = "; ".join(f"{s.split('-')[0]} n{int(r['size'])} skipR {r['sum']:+.1f} (gain {-r['sum']:+.1f}; keep avg {keep.get(s, float('nan')):+.3f} vs all {base[base.setup==s].r.mean():+.3f})" for s, r in per.iterrows())
    out["better"] = int((per["sum"] < 0).sum()); out["worse"] = int((per["sum"] > 0).sum())
    out["better_R"] = float(-per["sum"][per["sum"] < 0].sum()); out["worse_R"] = float(-per["sum"][per["sum"] > 0].sum())
    return out
res = []
b5 = x[x.setup.isin(FIVE)].copy()
res.append(skip_rule(b5, b5.spy_fo.abs() < 0.25, "FLAT25 (current Primary five)"))
bm = x[x.setup.isin(MF)].copy()
res.append(skip_rule(bm, bm.gap >= 2.0, "MFGAP (MF1-5 FD)"))
for r in res:
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
# per-setup base records (for context)
print(x.groupby("setup").r.agg(["size", "mean"]).round(3).to_string())
# 3. RW3/RW5 SPY-up-day profile
spy = daily(); spy = spy[spy.symbol == "SPY"].copy(); spy["date"] = spy.date.astype(str)
up = (spy.set_index("date").close > spy.set_index("date").open)
rw = x[x.setup.str.startswith(("RW3", "RW5"))].copy(); rw["up"] = rw.date.map(up)
rw = rw[rw.up.notna()]
dd = rw.groupby("date").agg(R=("r", "sum"), avg=("r", "mean"), up=("up", "first"))
def welch(a, b):
    return float((a.mean() - b.mean()) / math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)))
for lab, m in [("all", slice(None)), ("H1", dd.index <= "2025-09-30"), ("H2", dd.index > "2025-09-30")]:
    d = dd[m]; u, dn = d[d.up == True], d[d.up == False]
    tr = rw[rw.date.isin(d.index)]
    print(f"RW3/RW5 {lab}: up sessions {len(u)} trades {int((tr.up==True).sum())} avgR {tr[tr.up==True].r.mean():+.3f} totR {tr[tr.up==True].r.sum():+.1f} | "
          f"down sessions {len(dn)} trades {int((tr.up==False).sum())} avgR {tr[tr.up==False].r.mean():+.3f} totR {tr[tr.up==False].r.sum():+.1f} | "
          f"Welch t (down - up, per-session avg R) {-welch(u.avg, dn.avg):+.2f}")
for s in ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]:
    g = rw[rw.setup == s]; print(s[:3], "up", round(g[g.up == True].r.mean(), 3), len(g[g.up == True]), "down", round(g[g.up == False].r.mean(), 3), len(g[g.up == False]))
# context only (not a config): the same day split for the other three of the five
oth = x[x.setup.isin(FIVE) & ~x.setup.str.startswith(("RW3", "RW5"))].copy(); oth["up"] = oth.date.map(up)
print("context other three:", oth.groupby(["setup", "up"]).r.agg(["size", "mean"]).round(3).to_string())
# FLAT25 by halves and split per side within the five for context
print("FLAT25 hit share", round((b5.spy_fo.abs() < 0.25).mean(), 3), "MFGAP hit share", round((bm.gap >= 2).mean(), 3))
