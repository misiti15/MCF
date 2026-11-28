"""Day-type / time levers + 11-25 mechanism + weekly view of the basket cap. Usage: python daytype_levers.py <scratch>.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import dayt, spy_days
S = sys.argv[1]; rng = np.random.default_rng(5)
f = pd.read_parquet(f"{S}/feat2.parquet"); spy = spy_days(S).astype(float)
f = f.join(spy[["spy_gap", "spy_oc"]], on="date")
def ev(x, keep, name):
    base = x.groupby("date").r.sum(); new = x.r.where(keep, 0.0).groupby(x.date).sum(); d = new - base; n = int((~keep).sum())
    u = []
    for _ in range(300):
        m = np.ones(len(x), bool); m[rng.choice(len(x), n, replace=False)] = False; u.append(x.r[m].sum() - x.r.sum())
    print(f"{name}: skip {n} ({100*n/len(x):.0f}%) saved {d.sum():+.1f}R ({d.sum()/(len(base)/5):+.1f}/wk) U {np.mean(u):+.1f} pct {100*np.mean(np.array(u)<d.sum()):.0f} "
          f"dt {dayt(d):.2f} green-day cost {d[base>0].sum():+.1f} red {int((base<=0).sum())}->{int((new<=0).sum())} worst5 {base.nsmallest(5).sum():.1f}->{new.nsmallest(5).sum():.1f} "
          f"ex-best-day {d.sum()-d.max():+.1f} days affected {(d!=0).sum()}")
for book in ["primary", "arena"]:
    x = f[f.book == book].reset_index(drop=True); print("=====", book)
    ev(x, ~((x.sidel == "short") & (x.spy_gap > 0.3)).values, "no shorts on SPY gap-up >0.3% days")
    ev(x, ~((x.sidel == "short") & (x.spy_gap > 0.5)).values, "no shorts on SPY gap-up >0.5% days")
    ev(x, ~((x.sidel == "long") & (x.spy_gap < -0.5)).values, "no longs on SPY gap-down <-0.5% days")
    ev(x, ~(x.emin >= 13 * 60).values, "no entries from 13:00")
    ev(x, ~(x.emin >= 12 * 60 + 30).values, "no entries from 12:30")
p = f[(f.book == "primary") & (f.date == "2026-11-25") & f.strategy.str.startswith("L3")].sort_values("entry_et")
print("\n11-25 Primary L3: entries by 30 min:", (p.entry_et.dt.floor("30min").dt.strftime("%H:%M")).value_counts().sort_index().to_dict())
print("  stops by 30 min:", (p[p.exit_reason == "stop"].exit_et.dt.floor("30min").dt.strftime("%H:%M")).value_counts().sort_index().to_dict())
first_stop = p[p.exit_reason == "stop"].exit_et.min(); print("  first stop", first_stop.strftime("%H:%M"), "lots entered before first stop", int((p.entry_et < first_stop).sum()), "of", len(p),
      " max open at once", int(p.sd_open.max() + 1), " median stop bp", round(p.stop_bp.median(), 0))
# weekly with the K5 cap (skip and half)
for book in ["primary"]:
    x = f[f.book == book]
    wk = pd.to_datetime(x.date).dt.to_period("W-FRI")
    tab = pd.DataFrame({"base": x.r.groupby(wk).sum(), "K5skip": x.r.where(x.sd_lot <= 5, 0).groupby(wk).sum(),
                        "K5half": (x.r * np.where(x.sd_lot <= 5, 1, .5)).groupby(wk).sum(),
                        "K5skip+noGapUpShorts": x.r.where((x.sd_lot <= 5) & ~((x.sidel == "short") & (x.spy_gap > 0.3)), 0).groupby(wk).sum()})
    print("\nPrimary weekly R:"); print(tab.round(1).to_string())
