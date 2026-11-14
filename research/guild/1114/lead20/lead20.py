"""LEAD20 scorer (PLAN.md frozen 2026-11-14 01:30 ET). One look.
    python -I lead20.py <m5.csv.gz>        Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
LEAD = "AAPL MSFT NVDA AMZN META GOOGL GOOG BRK.B AVGO LLY TSLA JPM UNH XOM V MA PG JNJ COST HD".split()
INST = ["SPY", "QQQ", "SPXL", "TQQQ"]; SPLIT = "2025-09-30"; BAR = 3.57
m = pd.read_csv(sys.argv[1]); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
assert not ((m.date >= "2024-11-01") & (m.date <= "2025-02-28")).any()
P = lambda hm, col: m[m.hm == hm].pivot_table(index="date", columns="symbol", values=col)
o930, c1025, o1030, c1550 = P(930, "o"), P(1025, "c"), P(1030, "o"), P(1550, "c")
days = sorted(set(o930.index) & set(c1025.index) & set(o1030.index) & set(c1550.index))
o930, c1025, o1030, c1550 = (x.reindex(days) for x in (o930, c1025, o1030, c1550))
D = pd.DataFrame(index=days)
D["spy_up"] = c1025.SPY > o930.SPY
lead_ok = c1025[LEAD].notna() & o930[LEAD].notna()
D["L"] = ((c1025[LEAD] > o930[LEAD]) & lead_ok).sum(axis=1) / lead_ok.sum(axis=1)
D["day_up"] = c1550.SPY > o930.SPY
for s in INST:
    e, x = o1030[s], c1550[s]
    D[f"g_{s}"] = (x / e - 1) * 1e4
    D[f"n_{s}"] = D[f"g_{s}"] - ((0.01 + e * (1.4e-4 + 4.4e-4)) / e + (0.01 + x * 1e-4) / x) * 1e4
U = D[D.spy_up].dropna(subset=["g_SPY"]); R, C, N = U[U.L >= 0.70], U[U.L < 0.70], U[U.L < 0.50]
print(f"sessions {len(D)} ({days[0]}..{days[-1]}); spy_up at 10:30: {len(U)} ({len(U)/len(D):.0%}); rule days (L >= 0.70): {len(R)} "
      f"({len(R)/len(U):.0%} of spy_up); narrow (L < 0.50): {len(N)}")
print(f"hit (SPY closes above open): rule days {R.day_up.mean():.0%}, all spy_up {U.day_up.mean():.0%} (Observer: 76% at 10:30)")
def welch(a, b):
    return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
def tt(a): return a.mean() / (a.std(ddof=1) / np.sqrt(len(a)))
res = {}
for s in INST:
    a, b = R[f"g_{s}"].dropna(), C[f"g_{s}"].dropna()
    res[s] = dict(diff=a.mean() - b.mean(), t=welch(a, b), gross=a.mean(), t_gross=tt(a), net=R[f"n_{s}"].mean(),
                  comp=b.mean(), narrow=N[f"g_{s}"].mean())
    print(f"{s:5s} rule gross {a.mean():+6.1f}bps (t {tt(a):+.2f}) net {R[f'n_{s}'].mean():+6.1f} | complement {b.mean():+6.1f} | "
          f"diff {a.mean()-b.mean():+6.1f} (Welch t {welch(a, b):+.2f}) | narrow L<0.5 {N[f'g_{s}'].mean():+6.1f}")
for nm, sel in (("TRAIN", lambda x: x[x.index <= SPLIT]), ("VALID", lambda x: x[x.index > SPLIT])):
    a, b = sel(R).g_SPY, sel(C).g_SPY
    print(f"  {nm}: SPY rule {a.mean():+.1f}bps (n {len(a)}) vs complement {b.mean():+.1f} (n {len(b)}), diff t {welch(a, b):+.2f}")
bd = R.g_SPY.idxmax(); wob = R.drop(bd).g_SPY.mean()
tr, va = R[R.index <= SPLIT].g_SPY.mean() - C[C.index <= SPLIT].g_SPY.mean(), R[R.index > SPLIT].g_SPY.mean() - C[C.index > SPLIT].g_SPY.mean()
ok = (res["SPY"]["t"] >= BAR and res["SPY"]["gross"] > 0 and res["SPY"]["net"] > 0 and tr > 0 and va > 0
      and res["SPXL"]["net"] > 0 and wob > 0)
print(f"\nSPY w/o best day {wob:+.1f}bps. PASS {ok}{'' if ok else ' -> LEAD20 closed'} (bar 3.57; family 2,606). Educational only - not financial advice.")
