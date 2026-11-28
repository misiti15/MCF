"""Pre-declared long filters (written after cells.py, before scoring): stack the two features that beat a within-day
random control in BOTH universes (prior-day/5-day strength, wide stop in spreads). 6 filters + exit-style split.
For each: A (no Graveyard) and B (Graveyard) lots/avg R, halves (10-23..11-11 / 11-12..11-27), w/o 11-25, day t,
best-day share, within-day control percentile (A), and per-setup effect (setups >= 20 lots: how many improve when
restricted, how many worsen, median change). Usage: python combos.py <scratch>. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
S = sys.argv[1]; rng = np.random.default_rng(11)
L = pd.read_parquet(f"{S}/longs2.parquet")
L["exit_style"] = np.select([L.strategy.str.contains("-holdtr-"), L.strategy.str.contains("-hold-"),
                             L.strategy.str.contains(r"-t\d", regex=True)], ["holdtr", "hold", "target"], "other")
F = {"F1 prev>+1% & stop>=12 spreads": (L.prev_ret > 1) & (L.stop_spreads >= 12),
     "F2 5d>+3% & stop>=12 spreads": (L.ret5 > 3) & (L.stop_spreads >= 12),
     "F3 prev>+1% & stop>=200bp": (L.prev_ret > 1) & (L.stop_bp >= 200),
     "F4 (prev>+1% or 5d>+3%) & stop>=12 spr": ((L.prev_ret > 1) | (L.ret5 > 3)) & (L.stop_spreads >= 12),
     "F5 stop>=12 spreads only": (L.stop_spreads >= 12),
     "F6 prev>+1% only": (L.prev_ret > 1)}
def dayt(s): return s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 and s.std(ddof=1) > 0 else np.nan
def ctrl(U, cell, n=1000):
    cnt = cell.groupby("date").size(); pools = {d: U.loc[U.date == d, "r"].values for d in cnt.index}; sims = np.empty(n)
    for i in range(n):
        sims[i] = sum(rng.choice(pools[d], c, replace=len(pools[d]) < c).sum() for d, c in cnt.items()) / cnt.sum()
    return (sims < cell.r.mean()).mean() * 100, np.percentile(sims, 95)
def row(U, m, do_ctrl=True):
    g = U[m]; d = g.groupby("date").r.sum(); tot = g.r.sum()
    o = {"lots": len(g), "share_of_lots": len(g) / len(U), "avgR": g.r.mean(), "base_avg": U.r.mean(), "gross": g.gross_r.mean(),
         "R_per_day": d.sum() / U.date.nunique(), "day_t": dayt(d), "best_share": d.max() / tot if tot > 0 else np.nan,
         "avg_h1": g[g.date < "2026-11-12"].r.mean(), "avg_h2": g[g.date >= "2026-11-12"].r.mean(),
         "avg_wo_1125": g[g.date != "2026-11-25"].r.mean(), "green_days": f"{(d > 0).sum()}/{len(d)}"}
    if do_ctrl:
        p, p95 = ctrl(U, g); o["ctrl_pct"] = p; o["ctrl_p95"] = p95
    # per-setup effect
    ch = []
    for st, gs in U.groupby("strategy"):
        if len(gs) < 20: continue
        ms = m[gs.index]
        if ms.sum() < 5: continue
        ch.append(gs[ms].r.mean() - gs.r.mean())
    ch = np.array(ch); o["setups_up/down"] = f"{(ch > 0).sum()}/{(ch < 0).sum()}"; o["median_d_avgR"] = np.median(ch)
    return o
pd.set_option("display.width", 260)
for name, U in [("A Primary+arena", L[L.book != "graveyard"]), ("B Graveyard", L[L.book == "graveyard"])]:
    rows = {k: row(U, m.loc[U.index], name.startswith("A")) for k, m in F.items()}
    print(f"\n##### {name}  base lots {len(U)} avg {U.r.mean():.3f}")
    print(pd.DataFrame(rows).T.to_string(float_format=lambda x: f"{x:.3f}"))
    print("\nexit style (descriptive):")
    print(U.groupby("exit_style").apply(lambda g: pd.Series({"lots": len(g), "avgR": g.r.mean(), "gross": g.gross_r.mean(),
          "avg_wo_1125": g[g.date != "2026-11-25"].r.mean(), "setups": g.strategy.nunique()})).round(3).to_string())
    print("\nGEN only, exit style x F4:")
    G = U[U.strategy.str.startswith("GEN")]
    print(G.groupby(["exit_style", F["F4 (prev>+1% or 5d>+3%) & stop>=12 spr"].loc[G.index].rename("F4")]).r.agg(["count", "mean"]).round(3).to_string())
