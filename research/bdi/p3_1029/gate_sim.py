"""p3_1029 step 2b: what daily avg R / variance passes the funding gate "7 of 10 sessions green, no day > 50% of the
10-session net" (in R after costs). Inputs: trades10.csv (autopsy.py; Primary live paper 10-15..10-28).
(1) Parametric: daily R ~ Normal(mu, sd), grid of mu x sd, P(pass) by Monte Carlo (20,000 ten-day windows).
(2) Trade bootstrap from the live per-trade R of the CURRENT 8 Primary setups (and of all Primary trades), shifted by
    delta R per trade, trades/day resampled from the observed daily counts of that pool, a day = sum of its trades
    (iid trades: understates same-day correlation, so it is optimistic on variance - stated).
(3) Day bootstrap: the 10 observed daily totals (current-8 pool), shifted by delta per day.
Usage: python gate_sim.py      Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
CUR8 = ["ST7-rsi50dn-long-pm-t1s1-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
        "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "MF4-h40-open-flowsell", "NS1-rsidip-rsi5pop-long",
        "NS5-sma50-flush-oversold-long"]
rng = np.random.default_rng(20261029)
T = pd.read_csv(OUT / "trades10.csv")
DAYS = sorted(T.date.unique())
out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))


def passes(D):
    """D: (sims, 10) daily R. pass = >= 7 green and net > 0 and max day <= 50% of net."""
    net = D.sum(1)
    return ((D > 0).sum(1) >= 7) & (net > 0) & (D.max(1) <= 0.5 * net)


def pg(D):
    net = D.sum(1)
    return dict(p_pass=passes(D).mean(), p_7green=((D > 0).sum(1) >= 7).mean(),
                p_cons=((net > 0) & (D.max(1) <= 0.5 * net)).mean())


C = T[T.strategy.isin(CUR8)]
for name, pool in (("current 8 setups", C), ("all Primary trades", T)):
    d = pool.groupby("date").R.agg(["sum", "size"]).reindex(DAYS, fill_value=0)
    P(f"== {name}: {len(pool)} trades over 10 sessions; per trade mean {pool.R.mean():+.4f} sd {pool.R.std():.3f}; "
      f"per day mean {d['sum'].mean():+.3f} sd {d['sum'].std():.3f}; green {int((d['sum'] > 0).sum())}/10; trades/day {d['size'].mean():.1f}")
    P("   daily R:", d["sum"].round(2).to_dict())
    best = d["sum"].max(); net = d["sum"].sum()
    P(f"   best day {best:+.2f} = " + (f"{best / net:.0%} of net {net:+.2f}" if net > 0 else f"net {net:+.2f} <= 0"))

# (1) parametric
P("\n== (1) Normal daily R: P(pass 7/10 green & best day <= 50% of net)   rows mu (R/day), cols sd (R/day)")
sds = [1, 2, 3, 4, 6, 8, 12]
mus = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]
tab = pd.DataFrame(index=mus, columns=sds, dtype=float)
for mu in mus:
    for sd in sds:
        tab.loc[mu, sd] = passes(rng.normal(mu, sd, (20000, 10))).mean()
P(tab.round(2).to_string())
P("   rule of thumb: P(day green) = Phi(mu/sd) must be about 0.80 (mu/sd ~ 0.85) for P(>=7 of 10) ~ 0.88;")
P("   at mu/sd 0.5 (P green 0.69) P(>=7/10) is only ~0.5. The 50% rule binds only when sd is large vs mu.")

# (2) trade bootstrap with a per-trade shift
C2 = C[C.date != "2026-10-22"]
P(f"\n   current 8 w/o 10-22: {len(C2)} trades, mean R {C2.R.mean():+.4f}, $ {C2.pnl_adj.sum():+.2f} (with 10-22 $ {C.pnl_adj.sum():+.2f}); "
  f"current-8 daily $: {C.groupby('date').pnl_adj.sum().reindex(DAYS, fill_value=0).round(2).to_dict()}")
for name, pool in (("current 8", C), ("current 8 w/o 10-22", C2), ("all Primary", T)):
    r = pool.R.to_numpy(float)
    cnt = pool.groupby("date").size().reindex(DAYS, fill_value=0).to_numpy()
    P(f"\n== (2) trade bootstrap, {name}: per-trade R + delta, trades/day drawn from {sorted(cnt.tolist())}")
    rows = []
    for delta in [0, 0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30]:
        n = rng.choice(cnt, (20000, 10))
        D = np.zeros((20000, 10))
        tot = n.sum()
        draws = rng.choice(r, tot) + delta
        idx = np.repeat(np.arange(20000 * 10), n.ravel())
        D.ravel()[:] = np.bincount(idx, weights=draws, minlength=20000 * 10)
        rows.append(dict(delta=delta, avgR_trade=round(r.mean() + delta, 3), day_mu=round(D.mean(), 2), day_sd=round(D.std(), 2), **{k: round(v, 3) for k, v in pg(D).items()}))
    P(pd.DataFrame(rows).to_string(index=False))

# (3) day bootstrap of current-8 daily totals
dC = C.groupby("date").R.sum().reindex(DAYS, fill_value=0).to_numpy()
P(f"\n== (3) day bootstrap, current 8 daily totals {np.round(dC, 2).tolist()} + delta per day")
rows = []
for delta in [0, 0.5, 1, 1.5, 2, 3, 4, 6]:
    D = rng.choice(dC, (20000, 10)) + delta
    rows.append(dict(delta_day=delta, day_mu=round(D.mean(), 2), day_sd=round(D.std(), 2), **{k: round(v, 3) for k, v in pg(D).items()}))
P(pd.DataFrame(rows).to_string(index=False))
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(OUT / "gate_sim_out.txt", "w").write(txt); print(txt)
