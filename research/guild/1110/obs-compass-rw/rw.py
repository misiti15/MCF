"""Observer: is the compass's rest-of-day read more than random-walk arithmetic? (owner COMPASS task, 2026-11-10; 'try to break').
Benchmark: P(SPY closes on the same side of its open as now) = Phi(|fo| / sigma_rest(T)), sigma_rest(T) = std of SPY's move from T to the
close at the same time of day over the PRIOR 60 sessions (point-in-time, no same-day info, no pooled future).
Compares empirical hold rate with that prediction (calibration by predicted-p bin), then asks whether the live compass state
(W60 confirmed / leaning / checkpoint) adds anything AT THE SAME predicted p. Inputs: compass_5m conditional_obs.csv.gz (main-session study,
branch claude/charming-mccarthy-i3rhhr) + guild research/compassbf/compass_2y.csv.gz. Descriptive; counted as 3 looks (normal benchmark, empirical-distribution benchmark, compass-adds).
usage: python rw.py <conditional_obs.csv.gz> <compass_2y.csv.gz>. Educational only - not financial advice."""
import sys, math, numpy as np, pandas as pd
pd.set_option("display.width", 200)
O = pd.read_csv(sys.argv[1]); C = pd.read_csv(sys.argv[2])
O = O[O.fo != 0].copy(); O["hold"] = (np.sign(O.fo) == O.eod_open).astype(int); O["Tm"] = O["T"].str[:2].astype(int) * 60 + O["T"].str[3:].astype(int)
O = O.sort_values(["T", "date"])
O["sig"] = O.groupby("T").to_close.transform(lambda s: s.shift(1).rolling(60, min_periods=40).std())
Phi = np.vectorize(lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2))))
O = O[O.sig.notna()].copy(); O["p_rw"] = Phi(O.fo.abs() / O.sig)
# (1b) non-parametric benchmark: P(no crossing) = (1 + F_|X|(|fo|)) / 2, F from the PRIOR 60 sessions' to_close at the same T
#      (symmetric, fat tails kept; still no same-day info). This is the fair 'arithmetic' benchmark.
def emp(g):
    x = g.to_close.to_numpy(); f = g.fo.abs().to_numpy(); out = np.full(len(g), np.nan)
    for i in range(len(g)):
        h = np.abs(x[max(0, i - 60):i])
        if len(h) >= 40: out[i] = 0.5 * (1 + (h < f[i]).mean())
    return pd.Series(out, index=g.index)
O["p_emp"] = O.groupby("T", group_keys=False).apply(emp)
O = O[O.p_emp.notna()].copy()
print(f"rows {len(O)}, days {O.date.nunique()} ({O.date.min()}..{O.date.max()}), times {O['T'].nunique()}")
print(f"\n(1) overall: empirical hold {O.hold.mean():.3f} vs random-walk (normal) {O.p_rw.mean():.3f} vs empirical-distribution benchmark {O.p_emp.mean():.3f}")
de = (O.hold - O.p_emp).groupby(O.date).mean(); print(f"(1b) hold minus empirical-distribution benchmark, day-clustered: {de.mean():+.4f}, t {de.mean() / (de.std() / np.sqrt(len(de))):.2f}")
O["pe"] = pd.cut(O.p_emp, [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0])
print(O.groupby("pe", observed=True).agg(n=("hold", "size"), bench=("p_emp", "mean"), empirical=("hold", "mean")).assign(diff=lambda x: x.empirical - x.bench).round(3).to_string())
O["pb"] = pd.cut(O.p_rw, [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0])
cal = O.groupby("pb", observed=True).agg(n=("hold", "size"), days=("date", "nunique"), predicted=("p_rw", "mean"), empirical=("hold", "mean"))
cal["diff"] = cal.empirical - cal.predicted
print("calibration by predicted-p bin:\n", cal.round(3).to_string())
O["blk"] = pd.cut(O.Tm, [0, 660, 780, 960], labels=["10:00-10:59", "11:00-12:59", "13:00-15:50"])
print("\nby time block:\n", O.groupby("blk", observed=True).agg(n=("hold", "size"), predicted=("p_rw", "mean"), empirical=("hold", "mean")).round(3).to_string())
# day-clustered t of (hold - p_rw)
d = (O.hold - O.p_rw).groupby(O.date).mean(); print(f"day-clustered empirical - predicted: {d.mean():+.4f}, t {d.mean() / (d.std() / np.sqrt(len(d))):.2f}, days {len(d)}")
for half, g in (("first half", O[O.date < O.date.quantile(0.5) if False else O.date < sorted(O.date.unique())[len(O.date.unique()) // 2]]), ("second half", O[O.date >= sorted(O.date.unique())[len(O.date.unique()) // 2]])):
    dd = (g.hold - g.p_rw).groupby(g.date).mean(); print(f"   {half}: {dd.mean():+.4f} (t {dd.mean() / (dd.std() / np.sqrt(len(dd))):.2f})")
# (2) does the compass state add at the same p_rw?  join on 15-min marks
J = O.merge(C[["date", "T", "w60", "checkpoint"]], on=["date", "T"], how="inner")
J["w60s"] = np.where(J.w60.str.contains("confirmed", na=False), np.where((J.w60.str.startswith("UP")) == (J.fo > 0), "confirmed-agree", "confirmed-against"),
                     np.where(J.w60.str.contains("leaning", na=False), "leaning", "mixed/none"))
print(f"\n(2) compass state at 15-min marks ({len(J)} rows): empirical minus random-walk prediction, by W60 state")
g = J.groupby("w60s").agg(n=("hold", "size"), days=("date", "nunique"), predicted=("p_rw", "mean"), empirical=("hold", "mean"))
g["excess"] = g.empirical - g.predicted
for s in g.index:
    x = J[J.w60s == s]; dd = (x.hold - x.p_rw).groupby(x.date).mean(); g.loc[s, "t_day"] = dd.mean() / (dd.std() / np.sqrt(len(dd))) if len(dd) > 2 else np.nan
print(g.round(3).to_string())
print("\nwithin empirical-benchmark bins, confirmed-agree vs the rest (empirical hold):")
J["pe"] = pd.cut(J.p_emp, [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0])
print(J.assign(conf=J.w60s == "confirmed-agree").groupby(["pe", "conf"], observed=True).hold.agg(["size", "mean"]).unstack().round(3).to_string())
J["res"] = J.hold - J.p_emp
for s_ in ("confirmed-agree", "leaning", "mixed/none"):
    x = J[J.w60s == s_]; dd = x.res.groupby(x.date).mean()
    print(f"   {s_:16s} hold minus benchmark {x.res.mean():+.4f} (day-t {dd.mean() / (dd.std() / np.sqrt(len(dd))):.2f}, n {len(x)}, days {len(dd)})")
print("Educational only - not financial advice.")
# (3) owner's 'coupled with the previous day's close': does being on the same side of yesterday's close add to the benchmark? (4th look)
K = O[O.vs_prev.notna()].copy(); K["same_prev"] = np.sign(K.vs_prev) == np.sign(K.fo); K["res"] = K.hold - K.p_emp
print("\n(3) hold minus empirical benchmark, by whether SPY is also on the same side of yesterday's close:")
for k, x in K.groupby("same_prev"):
    print(f"   same side as prev close = {k}: n {len(x)}, days {x.date.nunique()}, bench {x.p_emp.mean():.3f}, hold {x.hold.mean():.3f}, diff {x.res.mean():+.4f}")
print("Educational only - not financial advice.")
