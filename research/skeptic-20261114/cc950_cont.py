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
out = []
for i, d in enumerate(days):
    if d not in start_ok or d < "2025-10-01": continue
    A = D.loc[d, "A"]; C = D.loc[d, "C"]
    prior = D.iloc[i - 60:i]
    for T in MARKS:
        p = D.loc[d, T]
        if not np.isfinite(p) or p == A: continue
        f = (p / A - 1) * 100; m_ = (C / p - 1) * 100
        sd = ((prior["C"] - prior[T]) / prior["A"] * 100).std()
        # today's realised range so far vs prior typical (vol regime)
        out.append(dict(date=d, T=T, f=f, cont=np.sign(f) * m_, z=abs(f) / sd))
O = pd.DataFrame(out)
def ratio(x):
    s = x.groupby("date").cont.agg(["sum", "size"]); mu = s["sum"].sum() / s["size"].sum()
    u = s["sum"] - mu * s["size"]; se = np.sqrt((u ** 2).sum()) / s["size"].sum()
    return mu, mu / se, len(x), len(s)
print("pooled, day-clustered (ratio estimator); continuation = sign(f) x SPY move T->close, %")
print("  all: %+.4f t %+.2f marks %d days %d" % ratio(O))
for lo, hi in ((0, .5), (.5, 1), (1, 2), (2, 99)):
    print(f"  |f|/sd60 {lo}-{hi}: " + "%+.4f t %+.2f marks %d days %d" % ratio(O[(O.z >= lo) & (O.z < hi)]))
