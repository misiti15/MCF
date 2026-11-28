"""shorts_autopsy live breakdown: non-Graveyard live trades 10-23..11-27 (LR8 R after costs, deduped), shorts vs longs by
condition. Descriptive (in-sample, 25 sessions); no selection is claimed from this table alone.
Usage: python live_autopsy.py SCRATCH > live_autopsy_out.txt. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]
t = pd.read_parquet(f"{D}/live.parquet")
t = t[(t.account != "graveyard") & (t.date >= "2026-10-23") & (t.date <= "2026-11-27")].copy()
TZ = "America/New_York"
t["et"] = pd.to_datetime(t.entry_time.astype(str), utc=True, format="mixed").dt.tz_convert(TZ)
t["xt"] = pd.to_datetime(t.exit_time.astype(str), utc=True, format="mixed").dt.tz_convert(TZ)
t["risk"] = (t.entry - t.stop).abs()
t["r_gross"] = t.side * (t.exit - t.entry) / t.risk
t["cost_r"] = t.r_gross - t.r
t["stop_bp"] = t.risk / t.entry * 1e4
t["stop_spr"] = t.stop_bp / t.spread_bps.where(t.spread_bps > 0)
t["tod"] = t.et.dt.hour * 100 + t.et.dt.minute
# daily context
d = pd.read_parquet(f"{D}/daily.parquet")
d["date"] = pd.to_datetime(d.timestamp, utc=True).dt.date.astype(str)  # daily bars stamp 04:00/05:00 UTC = session date
d = d.sort_values(["symbol", "date"])
d["pc"] = d.groupby("symbol").close.shift(1)
d["gap"] = (d.open / d.pc - 1) * 100
d["oc"] = (d.close / d.open - 1) * 100
d["atrp"] = ((d.high - d.low) / d.close * 100).groupby(d.symbol).transform(lambda s: s.rolling(14, min_periods=5).mean().shift(1))
t = t.merge(d[["symbol", "date", "gap", "oc", "atrp"]], on=["symbol", "date"], how="left")
spy = d[d.symbol == "SPY"].set_index("date")
t["spy_gap"] = t.date.map(spy.gap); t["spy_oc"] = t.date.map(spy.oc)
# SPY move during the hold
m = pd.read_parquet(f"{D}/idx1m.parquet")
m = m[m.symbol == "SPY"].copy()
m["ts"] = pd.to_datetime(m.timestamp, utc=True).dt.tz_convert(TZ)
s = m.set_index("ts").close.sort_index()
def px(ts):
    i = s.index.searchsorted(ts.floor("min"), side="right") - 1
    return s.iloc[i] if i >= 0 else np.nan
t["spy_e"] = [px(x) for x in t.et]; t["spy_x"] = [px(x) for x in t.xt]
t["spy_hold"] = (t.spy_x / t.spy_e - 1) * 100
# SPY intraday shape: 11:00 vs open, close vs 11:00 (squeeze = down into 11:00, rallies after)
m["date"] = m.ts.dt.date.astype(str); m["hm"] = m.ts.dt.hour * 100 + m.ts.dt.minute
sh = {}
for dd, g in m.groupby("date"):
    g = g[(g.hm >= 930) & (g.hm < 1600)]
    if not len(g): continue
    o = g.open.iloc[0]; c11 = g[g.hm <= 1100].close.iloc[-1]; c = g.close.iloc[-1]; lo = g.low.min()
    sh[dd] = dict(am=(c11 / o - 1) * 100, pm=(c / c11 - 1) * 100, rebound=(c / lo - 1) * 100, oc_m=(c / o - 1) * 100)
sh = pd.DataFrame(sh).T
t = t.join(sh, on="date")
t["side_l"] = np.where(t.side > 0, "long", "short")
gapdn = t.strategy.str.contains("gapdn|gap-slope|GAPDN|gap_dn", regex=True)
t["fam"] = np.where(t.side > 0, "long", np.where(gapdn, "short-gapdn-family", "short-other"))
PRIM = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]
op = m[(m.hm >= 930)].groupby("date").open.first()
t["spy_oe"] = (t.spy_e / t.date.map(op) - 1) * 100
t.to_parquet(f"{D}/live_feat.parquet")

def st(g):
    dsum = g.groupby("date").r.sum()
    n = len(dsum)
    se = dsum.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    best = dsum.max() if n else np.nan
    tot = g.r.sum()
    return pd.Series({"n": len(g), "sess": n, "avgR": g.r.mean(), "gross": g.r_gross.mean(), "cost": g.cost_r.mean(),
                      "R": tot, "day_t": dsum.mean() / se if se and se > 0 else np.nan,
                      "avg_wo_best": (tot - best) / max(1, len(g) - (g.date == dsum.idxmax()).sum()) if n else np.nan,
                      "best_share": best / tot if tot > 0 else np.nan})
pd.set_option("display.width", 250)
def tab(name, col, bins=None, labels=None, sub=None):
    x = t if sub is None else sub
    if bins is not None:
        x = x.assign(b=pd.cut(x[col], bins, labels=labels))
    else:
        x = x.assign(b=x[col])
    o = x.groupby(["side_l", "b"], observed=True).apply(st)
    print(f"\n## {name}\n" + o.round(3).to_string())

print("Non-Graveyard live 10-23..11-27, LR8 R after costs. Rule changes in window: 10-28 size, 10-29 latch, 10-30 testing CF,"
      " 11-12 LR8, 11-17 TSZ1, 11-19 Epoch1, 11-20 stop rounding, 11-21 cost basis, 11-23 ST7 out/brake.")
print(t.groupby("side_l").apply(st).round(3).to_string())
print(t.groupby("fam").apply(st).round(3).to_string())
tab("Stock gap at the open (%)", "gap", [-100, -5, -2.66, -1, 0, 1, 2.66, 5, 100])
tab("Entry price band ($)", "entry", [0, 10, 20, 50, 100, 200, 1e6])
tab("Stop width (bp)", "stop_bp", [0, 30, 50, 75, 100, 150, 250, 1e5])
tab("Stop width in spreads", "stop_spr", [0, 4, 6, 8, 12, 20, 40, 1e5])
tab("Entry time ET", "tod", [900, 1000, 1030, 1100, 1200, 1300, 1400, 1500, 1600])
tab("SPY move during hold (%)", "spy_hold", [-10, -0.3, -0.1, 0, 0.1, 0.3, 10])
tab("SPY gap (%)", "spy_gap", [-10, -0.5, -0.15, 0.15, 0.5, 10])
tab("SPY open->close (%)", "oc_m", [-10, -0.75, -0.25, 0.25, 0.75, 10])
t["squeeze"] = np.where((t.am < -0.2) & (t.pm > 0.4), "down-AM, rally-PM", np.where((t.am > 0.2) & (t.pm < -0.4), "up-AM, fade-PM", "other"))
tab("SPY day shape", "squeeze")
tab("Exit kind", "exit_reason")
tab("SPY open->entry (%)", "spy_oe", [-9, -1, -0.5, -0.2, 0, 0.2, 0.5, 1, 9])
tab("Stock 14d range % (vol)", "atrp", [0, 2, 3, 4, 6, 10, 100])
# MAE / squeeze inside the trade
sh_ = t[t.side < 0]
print("\n## Short trades: share reaching -1R MAE (stopped/squeezed) %.3f, longs %.3f" % ((sh_.mae_r <= -1).mean(), (t[t.side > 0].mae_r <= -1).mean()))
print("mae_r coverage", t.mae_r.notna().mean().round(3))
# gross decomposition per Primary short
print("\n## Primary shorts, all accounts live (gross, cost)")
print(t[t.strategy.isin(PRIM)].groupby("strategy").apply(st).round(3).to_string())
for s in PRIM:
    x = t[t.strategy == s]
    print(f"\n### {s}: by SPY hold move"); print(x.assign(b=pd.cut(x.spy_hold, [-10, -0.2, 0, 0.2, 10])).groupby("b", observed=True).apply(st).round(3).to_string())
    print(f"### {s}: by entry time"); print(x.assign(b=pd.cut(x.tod, [900, 1030, 1200, 1400, 1600])).groupby("b", observed=True).apply(st).round(3).to_string())
    print(f"### {s}: by stop in spreads"); print(x.assign(b=pd.cut(x.stop_spr, [0, 8, 15, 30, 1e5])).groupby("b", observed=True).apply(st).round(3).to_string())
# beta decomposition: regress short r_gross on SPY hold move
for side in ("short", "long"):
    x = t[(t.side_l == side) & t.spy_hold.notna()]
    b = np.polyfit(x.spy_hold, x.r_gross, 1)
    print(f"\n{side}: r_gross = {b[1]:.3f} + {b[0]:.3f} * SPY_hold%  (n {len(x)}); mean SPY hold {x.spy_hold.mean():.3f}%;"
          f" market-neutral gross {x.r_gross.mean() - b[0] * x.spy_hold.mean():.3f}R, cost {x.cost_r.mean():.3f}R")
