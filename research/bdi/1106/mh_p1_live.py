"""MH1106-P1 on 11-06 itself (in-sample, descriptive): class A at the 09:50 bar (beta from daily.parquet through 11-04,
i.e. two sessions stale), t1s1 walked on SIP 1-min bars from the 09:55 close, production-like costs.
Usage: python mh_p1_live.py <scratch mh1106>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); TZ = "America/New_York"; D = "2026-11-06"
F = pd.read_parquet(S / "mh" / D / "frames.parquet"); F = F[F.tod == 950]
B = pd.read_parquet(S / f"cov/days/{D}/bars.parquet"); B.index = pd.to_datetime(B.index, utc=True).tz_convert(TZ)
d = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet"); d["date"] = d.date.astype(str)
C = d.pivot_table(index="date", columns="symbol", values="close").sort_index().tail(61); R = C.pct_change(fill_method=None).iloc[1:]
beta = R.cov()["SPY"] / R["SPY"].var()
adv = d[d.date == d.date.max()].set_index("symbol").adv20
spy950 = F.spy_fo.iloc[0] if "spy_fo" in F else np.nan
F = F.assign(beta=F.symbol.map(beta), adv=F.symbol.map(adv))
F = F[(F.adv >= 95e6) & (F.close >= 5)]
def walk(s, e, Ru):
    g = B[B.symbol == s]; g = g[(g.index >= pd.Timestamp(f"{D} 09:55", tz=TZ)) & (g.index < pd.Timestamp(f"{D} 15:55", tz=TZ))]
    for h, l in zip(g.high, g.low):
        if l <= e - Ru: return -1.0 - (0.04 + 2 * e * 1e-4) / Ru
        if h >= e + Ru: return 1.0 - (0.02 + 2 * e * 1e-4) / Ru
    return (g.close.iloc[-1] - e) / Ru - (0.02 + 2 * e * 1e-4) / Ru if len(g) else np.nan
F["r"] = [walk(s, e, 0.25 * a) for s, e, a in zip(F.symbol, F.close, F.atr_d)]
F["A"] = (F.beta <= 0.5) & (F.fromOpen <= 0.10)
a, b = F[F.A], F[~F.A]
print(f"11-06 SPY at the 09:50 bar {spy950:+.2f}% (qualifies: {spy950 >= 0.4}); class A n {len(a)} win {(a.r > 0).mean():.0%} avg {a.r.mean():+.3f} | base n {len(b)} avg {b.r.mean():+.3f} | excess {a.r.mean() - b.r.mean():+.3f}")
print("class A names: " + ", ".join(f"{s} {r:+.2f}" for s, r in a.sort_values('r', ascending=False)[['symbol', 'r']].values[:25]))
print("Educational only - not financial advice.")
