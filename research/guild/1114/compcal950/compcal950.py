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
eps = 1e-3; X["brier"] = (X.P - X.y) ** 2; Pc = X.P.clip(eps, 1 - eps); X["ll"] = -(X.y * np.log(Pc) + (1 - X.y) * np.log(1 - Pc))
print(f"scored days {X.date.nunique()} ({X.date.min()}..{X.date.max()}); marks per day {len(MARKS)}")
for per in ("pre", "VALID", "FWD"):
    x = X[X.per == per]
    if x.empty: continue
    s = x.groupby("ref").agg(brier=("brier", "mean"), ll=("ll", "mean"), hit=("y", "mean"), n=("y", "size"), days=("date", "nunique"))
    dd = (x[x.ref == "950"].groupby("date").brier.mean() - x[x.ref == "open"].groupby("date").brier.mean()).dropna()
    print(f"\n{per}: (target hit = share of marks whose close is on the same side of the reference)")
    print(s.round(4).to_string())
    print(f"  per-day Brier (950 - open): {dd.mean():+.4f} (day-t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):+.2f}) [targets differ: descriptive]")
print("\nBrier by time of day (VALID + FWD):")
y = X[X.per != "pre"].assign(tod=lambda z: np.select([z["T"] < 1200, z["T"] < 1400], ["10:00-11:50", "12:00-13:50"], "14:00-15:50"))
print(y.groupby(["tod", "ref"]).brier.mean().unstack().round(4).to_string())
print("\ncalibration (VALID + FWD), 10 bins of P: mean P vs hit rate (n)")
for ref in ("950", "open"):
    z = y[y.ref == ref]; z = z.assign(b=pd.cut(z.P, np.linspace(0, 1, 11), include_lowest=True))
    c = z.groupby("b", observed=True).agg(P=("P", "mean"), hit=("y", "mean"), n=("y", "size"))
    print(f"  M1-{ref}: " + "  ".join(f"{r.P:.2f}->{r.hit:.2f}({int(r.n)})" for r in c.itertuples()))
print("Educational only - not financial advice.")
