"""What 'green every day' requires: daily R = sum of N lots, lot mean mu, lot sd s, within-day lot correlation rho.
P(red day) ~ Phi(-mu_d / sd_d), mu_d = N mu, sd_d = s sqrt(N (1 + (N-1) rho)). Estimated on Primary (10-23..11-27)
and on each account. Also weekly-review metric set on Primary. Read-only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
from scipy.stats import norm

SCR = sys.argv[1]
t = pd.read_parquet(f"{SCR}/live.parquet"); t = t[t.date >= "2026-10-23"]

def decomp(g):
    d = g.groupby("date").r.agg(["count", "sum"])
    mu, s = g.r.mean(), g.r.std(ddof=1)
    N = d["count"].mean()
    # moment estimate of average within-day correlation
    num = ((d["sum"] - d["count"] * mu) ** 2).sum(); den = (d["count"] * s ** 2).sum()
    npair = (d["count"] * (d["count"] - 1)).sum() * s ** 2
    rho = (num - den) / npair if npair > 0 else np.nan
    return mu, s, N, rho, d["sum"]

print("Account     sess  lots/day  mu/lot   sd/lot  rho_in_day  day_mean  day_sd  P(red) normal  P(red) actual")
out = {}
for acct, g in t.groupby("account"):
    mu, s, N, rho, ds = decomp(g)
    out[acct] = (mu, s, N, rho)
    print(f"{acct:10s} {len(ds):4d} {N:8.1f} {mu:8.3f} {s:7.3f} {rho:10.3f} {ds.mean():9.2f} {ds.std(ddof=1):7.2f} {norm.cdf(-ds.mean()/ds.std(ddof=1)):12.2f} {(ds<=0).mean():13.2f}")

mu, s, N, rho = out["primary"]
print(f"\nPrimary: N {N:.1f} lots/day, lot sd {s:.3f}, in-day rho {rho:.3f}")
sdd = lambda n, r: s * np.sqrt(n * (1 + (n - 1) * r))
print("Required lot edge mu for target P(red day), by lots/day and in-day correlation (lot sd as Primary):")
print("  lots/day  rho   P(red)=30%  20%     10%     5%      1%   | P(green week) at mu=+0.05 / +0.10")
for n in [10, 20, 38, 60]:
    for r in [0.0, max(rho, 0.0), 0.15]:
        req = [norm.ppf(1 - p) * sdd(n, r) / n for p in [.30, .20, .10, .05, .01]]
        pw = [norm.cdf(5 * n * m / (np.sqrt(5) * sdd(n, r))) for m in (0.05, 0.10)]
        print(f"  {n:8d} {r:5.2f}  " + "  ".join(f"{x:6.3f}" for x in req) + f"  |  {pw[0]:.2f} / {pw[1]:.2f}")
print("\nP(red day) / P(red week) / expected red days per 21-session month at Primary's N and rho, by lot edge:")
for m in [-0.16, -0.05, 0.0, 0.03, 0.05, 0.10, 0.20, 0.50]:
    pd_ = norm.cdf(-N * m / sdd(N, rho)); pw = norm.cdf(-5 * N * m / (np.sqrt(5) * sdd(N, rho)))
    print(f"  mu {m:+.2f}: red day {pd_:.2f}  red week {pw:.2f}  red days/month {21*pd_:4.1f}  20-session 5th-pct floor {20*N*m - 1.645*np.sqrt(20)*sdd(N, rho):7.1f}R")

# weekly-review metric set on Primary's actual days
p = t[t.account == "primary"].groupby("date").r.sum().sort_index()
wk = pd.to_datetime(p.index).to_period("W-FRI").astype(str)
w = p.groupby(wk).agg(sess="count", total="sum", median_day="median", worst="min", red=lambda x: int((x <= 0).sum()))
roll = p.rolling(20).sum()
print("\nPrimary weekly review metrics (R after costs):"); print(w.round(1).to_string())
print(f"20-session rolling R: min {roll.min():.1f}, last {roll.iloc[-1]:.1f}; median day overall {p.median():.2f}; worst {p.min():.1f}; days <= -20R: {(p<=-20).sum()}")
# heavy tails: empirical vs normal for the sum-of-lots model
z = (p - p.mean()) / p.std(ddof=1)
print(f"Primary daily R skew {p.skew():.2f}, excess kurtosis {p.kurt():.2f}; share of total loss from worst 5 days {p.nsmallest(5).sum()/p[p<0].sum():.2f}")
