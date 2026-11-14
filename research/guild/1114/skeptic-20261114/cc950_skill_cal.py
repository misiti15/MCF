"""COMPCAL950 scorer (PLAN.md frozen 2026-11-14 15:20 ET). One look. Display research only.
    python -I compcal950.py <lead20 m5.csv.gz>        Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
m = pd.read_csv(sys.argv[1]); m = m[m.symbol == "SPY"].copy()
m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
assert not ((m.date >= "2024-11-01") & (m.date <= "2025-02-28")).any()
MARKS = [h * 100 + mi for h in range(10, 16) for mi in range(0, 60, 10) if h * 100 + mi <= 1550]
def bar_end(T):          # 5-min bar that ENDS at T starts at T-5
    h, mi = divmod(T, 100); mi -= 5
    if mi < 0: h, mi = h - 1, mi + 60
    return h * 100 + mi
rows = {}
for d, g in m.groupby("date"):
    g = g.set_index("hm")
    if not {930, 950, 1555}.issubset(g.index): continue
    r = dict(A=g.loc[950, "o"], O=g.loc[930, "o"], C=g.loc[1555, "c"])
    for T in MARKS:
        b = bar_end(T); r[T] = g.loc[b, "c"] if b in g.index else np.nan
    rows[d] = r
D = pd.DataFrame(rows).T.sort_index(); days = list(D.index)
gapi = [i for i in range(1, len(days)) if (pd.Timestamp(days[i]) - pd.Timestamp(days[i - 1])).days > 5]
start_ok = set(days[(gapi[-1] if gapi else 0) + 60:])
recs = []
for i, d in enumerate(days):
    if d not in start_ok: continue
    prior = D.iloc[i - 60:i]
    for ref, key in (("950", "A"), ("open", "O")):
        R0 = D.loc[d, key]
        for T in MARKS:
            p = D.loc[d, T]
            if not np.isfinite(p): continue
            f = (p / R0 - 1) * 100
            if f == 0: continue
            mm = ((prior["C"] - prior[T]) / prior[key] * 100).dropna()
            if len(mm) < 40: continue
            P = float((np.sign(f) * (f + mm) > 0).mean())
            y = int(np.sign(D.loc[d, "C"] / R0 - 1) == np.sign(f))
            recs.append(dict(date=d, ref=ref, T=T, f=f, P=P, y=y))
X = pd.DataFrame(recs)
X["per"] = np.where(X.date < "2025-10-01", "pre", np.where(X.date <= "2026-10-07", "VALID", "FWD"))
X["brier"] = (X.P - X.y) ** 2
# climatology: prior-60-day hit rate at the same mark and reference (no f), strictly prior days
X = X.sort_values(["ref", "T", "date"])
X["clim"] = X.groupby(["ref", "T"]).y.transform(lambda s: s.shift(1).rolling(60, min_periods=40).mean())
X = X.dropna(subset=["clim"]); X["bc"] = (X.clim - X.y) ** 2
for per in ("VALID", "FWD"):
    for ref in ("950", "open"):
        x = X[(X.per == per) & (X.ref == ref)]
        dd = x.groupby("date").apply(lambda g: (g.bc - g.brier).mean())
        print(f"{per} M1-{ref}: Brier {x.brier.mean():.4f} vs clim {x.bc.mean():.4f}; skill {1 - x.brier.mean() / x.bc.mean():+.3f}; day-t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):+.2f}; days {x.date.nunique()}")
def ratio(x, col):
    s = x.groupby("date")[col].agg(["sum", "size"]); mu = s["sum"].sum() / s["size"].sum()
    u = s["sum"] - mu * s["size"]; return mu, mu / (np.sqrt((u ** 2).sum()) / s["size"].sum()), len(x), len(s)
for ref in ("950", "open"):
    z = X[(X.per != "pre") & (X.ref == ref)].assign(e=lambda q: q.y - q.P)
    print(f"M1-{ref} calibration gap mean(y - P), pooled day-clustered:")
    for lo, hi in ((0.5, 0.8), (0.8, 1.01), (0, 0.5)):
        print(f"   P {lo}-{hi}: " + "%+.3f t %+.2f marks %d days %d" % ratio(z[(z.P >= lo) & (z.P < hi)], "e"))
