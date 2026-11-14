"""OBS-STOPSLIP (Observer 2026-11-12 ~03:45 ET): live stop-exit slippage, what drives it. Live journals, run 1,
2026-10-20..11-11, all accounts. Stop exits only (exit_reason='stop'). slip_R = side*(stop - exit)/|entry - stop|
(positive = filled worse than the stop). Entry spread from trades.meta JSON prefix (meta.split(';')[0], checklist #33;
rows that fail to parse are KEPT with spread NaN). Day-clustered t. 0 configs. Educational only - not financial advice.
usage: python stopslip.py <dir of journals>"""
import sqlite3, sys, json, pandas as pd, numpy as np
D = sys.argv[1]; F = []
for nm, b in [('Primary','mcf-data'),('On Deck','mcf-data-testing'),('Testing A','mcf-data-testing2'),('Testing B','mcf-data-explore1'),
              ('Testing C','mcf-data-livelab'),('Graveyard','mcf-data-graveyard'),('Gen','mcf-data-gen')]:
    t = pd.read_sql("select date, side, entry, stop, exit, exit_time, shares, meta from trades where run_id=1 and date between "
                    "'2026-10-20' and '2026-11-11' and exit_reason='stop'", sqlite3.connect(f"{D}/{b}.db"))
    t["acct"] = nm; F.append(t)
t = pd.concat(F, ignore_index=True)
n0 = len(t); t = t[(t.entry - t.stop).abs() > 0].copy()
t["slip"] = t.side * (t.stop - t.exit) / (t.entry - t.stop).abs()
def sp(m):
    try: return json.loads(str(m).split(";")[0]).get("spread_bps")
    except Exception: return np.nan
t["spread_bps"] = t.meta.map(sp).astype(float)
t["risk_bps"] = (t.entry - t.stop).abs() / t.entry * 1e4
t["spread_over_risk"] = t.spread_bps / t.risk_bps
t["hour"] = pd.to_datetime(t.exit_time, utc=True).dt.tz_convert("America/New_York").dt.hour
t = t[t.slip.abs() < 3]; assert len(t) > 0.97 * n0, (len(t), n0)
def dt(x):
    g = x.groupby("date").slip.mean(); return g.mean() / (g.std(ddof=1) / np.sqrt(len(g))) if len(g) > 2 else np.nan
print(f"stop exits {len(t)} (of {n0}); spread parsed {t.spread_bps.notna().mean():.0%}")
print(f"ALL mean slip {t.slip.mean():+.4f}R median {t.slip.median():+.4f} share>0 {(t.slip>0).mean():.0%} day-t {dt(t):+.2f}")
for k, g in t.groupby("acct"): print(f"  {k:10s} n {len(g):5d} mean {g.slip.mean():+.4f} med {g.slip.median():+.4f} day-t {dt(g):+.2f}")
print("by spread / risk (spread as share of stop distance):")
for k, g in t.groupby(pd.qcut(t.spread_over_risk, 5), observed=True): print(f"  {str(k):22s} n {len(g):5d} mean {g.slip.mean():+.4f} med {g.slip.median():+.4f}")
print("by risk_bps (stop distance, bps of price):")
for k, g in t.groupby(pd.qcut(t.risk_bps, 5), observed=True): print(f"  {str(k):22s} n {len(g):5d} mean {g.slip.mean():+.4f} med {g.slip.median():+.4f}")
print("by exit hour:")
for k, g in t.groupby("hour"): print(f"  {k:2d} n {len(g):5d} mean {g.slip.mean():+.4f}")
print("by side:", {int(k): round(g.slip.mean(), 4) for k, g in t.groupby("side")})
d = t.groupby("date").slip.mean(); print("by date (top 5 worst):", d.sort_values(ascending=False).head(5).round(3).to_dict())
tot = t.slip.sum(); best = t.groupby("date").slip.sum().max(); print(f"one-big-day: worst day's share of total slip {best/tot:.0%}")
print("slip distribution by account (quantiles 5/25/50/75/95) and share |slip|>0.3 (likely moved stop, not slippage):")
for k, g in t.groupby("acct"):
    q = g.slip.quantile([.05, .25, .5, .75, .95]).round(3).tolist(); print(f"  {k:10s} {q}  |slip|>0.3: {(g.slip.abs()>0.3).mean():.1%}")
c = t[t.slip.abs() <= 0.3]
print(f"core (|slip|<=0.3, n {len(c)}): mean {c.slip.mean():+.4f} med {c.slip.median():+.4f} day-t {dt(c):+.2f}; by acct",
      {k: round(g.slip.mean(), 4) for k, g in c.groupby('acct')})
print("core by spread/risk quintile:", [round(g.slip.mean(), 4) for _, g in c.groupby(pd.qcut(c.spread_over_risk, 5), observed=True)])
print("core by hour:", {k: round(g.slip.mean(), 4) for k, g in c.groupby('hour')})
X = np.c_[np.ones(len(c)), c.spread_over_risk.clip(upper=0.5)]; b = np.linalg.lstsq(X, c.slip, rcond=None)[0]
print(f"replay model (core): slip_R = {b[0]:+.4f} + {b[1]:.3f} x spread/stop-distance (clipped 0.5)")
print("share of stop exits with spread/stop > 0.15:", f"{(t.spread_over_risk>0.15).mean():.0%}", " > 0.25:", f"{(t.spread_over_risk>0.25).mean():.0%}")
