"""Alternative success metrics per live setup (>= 20 trades since 10-23, all 10 accounts, LR8 R after costs, deduped).
Compares rankings vs the leaderboard score (avg R shrunk by n/(n+20)) and tests which metric, measured on the first
half of the window, best predicts the second half. Read-only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
from scipy import stats

SCR = sys.argv[1]
t = pd.read_parquet(f"{SCR}/live.parquet")
t = t[t.date >= "2026-10-23"].copy()
t["hold_h"] = t.hold_min.clip(0, 390) / 60
t["cost_r"] = t.gross_r - t.r
t["side"] = np.where(t.side > 0, "L", "S")

def metrics(g):
    d = g.groupby("date")["r"].sum().sort_index()
    n, ns = len(g), len(d)
    srt = d.sort_values(ascending=False)
    cum = d.cumsum(); dd = cum - np.maximum(cum.cummax(), 0)
    se = d.std(ddof=1) / np.sqrt(ns) if ns > 1 else np.nan
    wo1 = (g.r.sum() - srt.iloc[0]) / max(n - g[g.date == srt.index[0]].shape[0], 1)
    top2 = list(srt.index[:2]); wo2 = g[~g.date.isin(top2)].r.mean() if (~g.date.isin(top2)).any() else np.nan
    avg = g.r.mean()
    return pd.Series({
        "acct": g.account.mode().iloc[0], "side": g.side.iloc[0], "n": n, "sess": ns,
        "avgR": avg, "score": avg * n / (n + 20), "totR": g.r.sum(), "R_sess": d.mean(),
        "med_day": d.median(), "worst_day": d.min(), "green_sh": (d > 0).mean(),
        "day_t": d.mean() / se if se and se > 0 else np.nan,
        "maxDD": dd.min(), "ulcer": float(np.sqrt((dd ** 2).mean())),
        "wo1": wo1, "wo2": wo2, "best_sh": srt.iloc[0] / g.r.sum() if g.r.sum() > 0 else np.nan,
        "R_per_slot_h": g.r.sum() / max(g.hold_h.sum(), 1e-9),
        "R_per_10k_h": g.r.sum() / max((g.notional * g.hold_h).sum() / 1e4, 1e-9),
        "gross": g.gross_r.mean(), "cost": g.cost_r.mean(),
        "cost_share": g.cost_r.mean() / g.gross_r.abs().mean(),
    })

m = t.groupby("strategy").apply(metrics)
m = m[m.n >= 20].copy()
m["short"] = m.index.str.slice(0, 48)
pd.set_option("display.width", 250)
print(f"Setups with >= 20 trades since 10-23: {len(m)} ({(m.side=='L').sum()} long, {(m.side=='S').sum()} short); trades {int(m.n.sum())}")
print("\nDistribution of metrics across setups (median [p10, p90]):")
for c in ["avgR", "R_sess", "med_day", "worst_day", "green_sh", "day_t", "maxDD", "ulcer", "wo1", "wo2", "R_per_slot_h", "gross", "cost", "cost_share"]:
    print(f"  {c:12s} {m[c].median():8.3f}  [{m[c].quantile(.1):8.3f}, {m[c].quantile(.9):8.3f}]")
print(f"\nPositive: avgR {int((m.avgR>0).sum())}, wo1 {int((m.wo1>0).sum())}, wo2 {int((m.wo2>0).sum())}, day_t>2 {int((m.day_t>2).sum())}, gross>0 {int((m.gross>0).sum())}, green_sh>=0.5 {int((m.green_sh>=.5).sum())}")

alt = ["avgR", "R_sess", "med_day", "worst_day", "green_sh", "day_t", "ulcer_neg", "wo1", "wo2", "R_per_slot_h", "R_per_10k_h", "gross"]
m["ulcer_neg"] = -m.ulcer
print("\nSpearman rank correlation with leaderboard score, and top-15 overlap:")
top = set(m.score.nlargest(15).index)
for c in alt:
    rho = stats.spearmanr(m.score, m[c], nan_policy="omit").correlation
    print(f"  {c:12s} rho {rho:5.2f}   top15 overlap {len(top & set(m[c].nlargest(15).index)):2d}/15")

cols = ["acct", "side", "n", "sess", "avgR", "score", "R_sess", "med_day", "worst_day", "green_sh", "day_t", "ulcer", "wo1", "wo2", "best_sh", "R_per_slot_h", "cost"]
m["rk_score"] = m.score.rank(ascending=False, na_option="bottom").astype(int)
m["rk_wo2"] = m.wo2.rank(ascending=False, na_option="bottom").astype(int)
m["rk_dayt"] = m.day_t.rank(ascending=False, na_option="bottom").astype(int)
m["rk_ulcer"] = m.ulcer.rank(na_option="bottom").astype(int)
print("\nTop 20 by leaderboard score with alternative ranks:")
print(m.sort_values("score", ascending=False).head(20).set_index("short")[cols + ["rk_wo2", "rk_dayt", "rk_ulcer"]].round(3).to_string())
print("\nTop 15 by avg R w/o best 2 days:")
print(m.sort_values("wo2", ascending=False).head(15).set_index("short")[cols + ["rk_score"]].round(3).to_string())
print("\nTop 15 by day t:")
print(m.sort_values("day_t", ascending=False).head(15).set_index("short")[cols + ["rk_score"]].round(3).to_string())

# Pending decision setups (docs/live/decisions.json open On Deck / Primary cards)
pend = ["GEN-261027-01", "GEN-261023-06", "GEN-261022-05", "GEN-261026-07", "GEN-261020-09", "GEN-261029-06", "GEN-261021-04",
        "NM-RWR4-ns2-u", "L3-gap-slope-fromopen-FD", "RW3-gapdn", "RW5-heat30", "NM-ETF-late-dip", "GEN-261023-07", "GEN-261027-10"]
print("\nPending-decision / Primary setups (rank of", len(m), "):")
rows = []
for p in pend:
    hit = m[m.index.str.startswith(p)]
    for s, r in hit.iterrows():
        rows.append(r)
pdx = pd.DataFrame(rows)
if len(pdx):
    print(pdx.set_index("short")[cols + ["rk_score", "rk_wo2", "rk_dayt", "rk_ulcer"]].round(3).to_string())

# Predictive validity: metric on first half (10-23..11-11) vs avg R / R per session on second half (11-12..11-27)
h1, h2 = t[t.date < "2026-11-12"], t[t.date >= "2026-11-12"]
a = h1.groupby("strategy").apply(metrics); b = h2.groupby("strategy").apply(metrics)
both = a[(a.n >= 20)].join(b[b.n >= 10][["avgR", "R_sess", "totR", "worst_day", "green_sh"]], rsuffix="_2", how="inner")
both["ulcer_neg"] = -both.ulcer
print(f"\nPredictive validity: {len(both)} setups with >= 20 trades in H1 (10-23..11-11) and >= 10 in H2 (11-12..11-27)")
print("  Spearman(H1 metric, H2 outcome)   [boot 95% CI over setups for avgR_2]")
rng = np.random.default_rng(7)
res = []
for c in ["score", "avgR", "R_sess", "med_day", "worst_day", "green_sh", "day_t", "ulcer_neg", "wo1", "wo2", "R_per_slot_h", "gross"]:
    r1 = stats.spearmanr(both[c], both.avgR_2, nan_policy="omit").correlation
    r2 = stats.spearmanr(both[c], both.R_sess_2, nan_policy="omit").correlation
    r3 = stats.spearmanr(both[c], both.worst_day_2, nan_policy="omit").correlation
    bs = []
    idx = np.arange(len(both))
    for _ in range(500):
        s = both.iloc[rng.choice(idx, len(idx))]
        bs.append(stats.spearmanr(s[c], s.avgR_2, nan_policy="omit").correlation)
    q = np.nanpercentile(bs, [2.5, 97.5])
    # top-quintile selection: H2 avg R of top 20% by metric vs all
    k = max(len(both) // 5, 1)
    sel = both.nlargest(k, c)
    res.append((c, r1, q[0], q[1], r2, r3, sel.avgR_2.mean(), sel.R_sess_2.mean(), (sel.avgR_2 > 0).mean()))
    print(f"  {c:12s} ->avgR {r1:5.2f} [{q[0]:5.2f},{q[1]:5.2f}]  ->R/sess {r2:5.2f}  ->worst day {r3:5.2f}   top20% H2 avgR {sel.avgR_2.mean():6.3f} R/sess {sel.R_sess_2.mean():6.2f} pos {(sel.avgR_2>0).mean():.2f}")
# random control for top-quintile selection
k = max(len(both) // 5, 1)
rnd = [both.sample(k, random_state=i).avgR_2.mean() for i in range(2000)]
print(f"  random top-{k} control: H2 avgR mean {np.mean(rnd):.3f}, 95% band [{np.percentile(rnd,2.5):.3f}, {np.percentile(rnd,97.5):.3f}]; all setups {both.avgR_2.mean():.3f}")
m.drop(columns=["short"]).to_csv(f"{SCR}/setup_metrics.csv")
m.drop(columns=["short"]).round(4).to_csv(sys.argv[2] if len(sys.argv) > 2 else f"{SCR}/m.csv")
