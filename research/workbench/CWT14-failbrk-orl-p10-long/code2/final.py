"""Final side-by-side: parent, WB4, the layer ladder, WB5 (recommended) and the tried alternates. Educational only - not financial advice."""
from bps import *
L = {
 "parent": None,
 "WB4 (first run)": (dict(exitc="A"), 1.0),
 "WB4 + C1 cost/R<=0.10": (dict(gate=c1, exitc="A"), 1.0),
 "WB4 + C1 + G3 SPY>=-0.20% since 09:50": (dict(gate=both(c1, g3), exitc="A"), 1.0),
 "WB5 = WB4 + C1 + G3 + stop 1.5R": (dict(gate=both(c1, g3), exitc="S15"), 1.5),
 "alt: WB5 with stop 2.0R": (dict(gate=both(c1, g3), exitc="S20"), 2.0),
 "alt: WB5 + max 30 trades/day": (dict(gate=both(c1, g3), exitc="S15", maxday=30), 1.5),
 "alt: WB5 + start 10:15": (dict(gate=both(c1, g3), exitc="S15", window=(1015, 1200)), 1.5),
}
rows = []; W4 = None
for nm, spec in L.items():
    if spec is None: t = P2.copy()
    else:
        kw, sk = spec; t = trades(c3, **kw); t = t.assign(bp=bps(t, sk))
    if nm.startswith("WB4 (first"): W4 = t
    for tn, rng in TESTS.items():
        a = period(t, rng); st = stats(a, "R"); pp = paired(a, period(P2, rng), "R", "R")
        pw = paired(a, period(W4, rng), "R", "R") if W4 is not None else dict(diff=np.nan, t=np.nan)
        tt = a.copy(); tt["reg"] = tt.date.map(reg.regime); dt = tt.groupby("reg").R.mean()
        rows.append(dict(copy=nm, test=tn, **st, avg_win=a.R[a.R > 0].mean(), avg_loss=a.R[a.R <= 0].mean(), bps=a.bp.mean(),
                         d_parent=pp["diff"], t_parent=pp["t"], d_wb4=pw["diff"], t_wb4=pw["t"], up=dt.get("up"), flat=dt.get("flat"), down=dt.get("down")))
D = pd.DataFrame(rows); D.to_csv(O2 + "final.csv", index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
for tn in TESTS:
    print("=====", tn)
    print(D[D.test == tn][["copy", "n", "days", "win", "avg", "wo_best", "best_share", "wo_worst", "total", "worst_day", "avg_win", "avg_loss", "bps", "d_parent", "t_parent", "d_wb4", "t_wb4", "up", "flat", "down"]].round(3).to_string())
