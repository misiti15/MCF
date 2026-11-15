"""IMOM scorer (PLAN.md frozen 2026-11-15 03:30 ET). One look.  python -I imom.py <lead20 m5.csv.gz>
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
m = pd.read_csv(sys.argv[1]); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
assert not ((m.date >= "2024-11-01") & (m.date <= "2025-02-28")).any()
tt = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
for inst in ("SPY", "SPXL"):
    s = m[m.symbol == inst]; P = lambda hm, c: s[s.hm == hm].set_index("date")[c]
    D = pd.DataFrame({"c955": P(955, "c"), "o1530": P(1530, "o"), "c1555": P(1555, "c")}).dropna().sort_index()
    spy = m[m.symbol == "SPY"]; sc = spy[spy.hm == 1555].set_index("date").c.sort_index(); sc955 = spy[spy.hm == 955].set_index("date").c
    days = list(sc.index); prev = {days[i]: sc.iloc[i - 1] for i in range(1, len(days))
                                   if (pd.Timestamp(days[i]) - pd.Timestamp(days[i - 1])).days <= 5}
    D = D[D.index.isin(prev)]
    r1 = pd.Series({d: sc955[d] / prev[d] - 1 for d in D.index})                   # predictor always from SPY
    D["r1"] = r1; D["rl"] = (D.c1555 / D.o1530 - 1) * 1e4
    cost = ((0.01 + D.o1530 * 2e-4) / D.o1530 + (0.01 + D.c1555 * 1e-4) / D.c1555) * 1e4
    C1 = np.sign(D.r1) * D.rl; C2 = D.rl[D.r1 > 0]
    b = np.polyfit(D.r1 * 1e4, D.rl, 1); e = D.rl - np.polyval(b, D.r1 * 1e4)
    se_b = np.sqrt((e @ e) / (len(D) - 2) / ((D.r1 * 1e4 - (D.r1 * 1e4).mean()) ** 2).sum())
    print(f"\n{inst}: {len(D)} sessions ({D.index[0]}..{D.index[-1]}); r1 > 0 on {int((D.r1 > 0).sum())}; all-days last half-hour {D.rl.mean():+.2f}bps")
    print(f"  slope of r_last on r1: {b[0]:+.4f} bps per bp (t {b[0] / se_b:+.2f})")
    for nm, x, cx in (("C1 sign", C1, cost), ("C2 long-only", C2, cost[D.r1 > 0])):
        se = x.std(ddof=1) / np.sqrt(len(x)); tr, va = x[x.index <= "2025-09-30"], x[x.index > "2025-09-30"]
        print(f"  {nm:12s} n {len(x):3d} gross {x.mean():+6.2f}bps (t {tt(x):+.2f}) net {(x - cx).mean():+6.2f} | TRAIN {tr.mean():+.2f} (t {tt(tr):+.2f}) "
              f"VALID {va.mean():+.2f} (t {tt(va):+.2f}) | w/o best {x.drop(x.idxmax()).mean():+.2f} | MDE80 {2.8 * se:.1f}bps, at bar {4.41 * se:.1f}bps")
print("\nfamily 2,613, BAR90 3.57. Educational only - not financial advice.")
