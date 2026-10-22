"""First day of the twin-exposure cap ('twin held') and the per-setup 2R daily loss limit ('setup daily loss limit'),
2026-10-22. Counts the skips per account/setup and prices what they blocked with the journal's what-if run (run 2:
the runner's own simulation of skipped signals, next-bar entry, same stop/target, flatten at close), minus the production
cost model (config/default.yaml costs: $0.01/sh + 1 bps per side, no slippage on target exits, +$0.02/sh on stops), so costs are in.
For the loss limit it also reports, per setup, the realized R at the moment it tripped and what the setup's live
trades did afterwards (none: it was stopped). Writes caps_out.txt.
Usage: python caps.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3, json
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-10-22"
T = pd.read_csv(OUT / "trades.csv")
T["costR"] = (T.pnl - T.pnl_adj) / T.risk
out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
REASONS = ("twin held", "setup daily loss limit")
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    sg = pd.read_sql("select id, ts, symbol, strategy, side, reason, info from signals where day=? and run_id=1 and status='skipped'", c, params=(D,))
    w = pd.read_sql("select symbol, strategy, side, signal_time, entry, stop, exit, exit_reason, r_multiple, meta from trades where date=? and run_id=2", c, params=(D,))
    w["why"] = w.meta.fillna("").str.extract(r"why=(.*)$")[0]
    w["sig_min"] = pd.to_datetime(w.signal_time, utc=True).dt.tz_convert("America/New_York").dt.strftime("%H:%M")
    sg["sig_min"] = (pd.to_datetime(sg.ts, utc=True).dt.tz_convert("America/New_York").dt.floor("5min")).dt.strftime("%H:%M")
    R = (w.entry - w.stop).abs()
    cps = (0.01 + w.entry * 1e-4) + np.where(w.exit_reason == "target", 0.0, 0.01 + w.exit * 1e-4) + np.where(w.exit_reason == "stop", 0.02, 0.0)
    w["costR"] = np.where(R > 0, cps / R, 0.0)
    cost = float(w.costR.mean()) if len(w) else 0.0
    P(f"\n===== {a}: skipped {len(sg)}; what-if rows {len(w)}; mean cost {cost:.3f}R/trade (production model)")
    for rsn in REASONS:
        s = sg[sg.reason == rsn]
        x = w[w.why == rsn].copy()
        x["netR"] = x.r_multiple - x.costR
        P(f"-- '{rsn}': {len(s)} skipped signals; {len(x)} priced in the what-if run")
        if len(s) == 0:
            continue
        if len(x):
            rk = float(T[T.acct == a].risk.median())
            P(f"   (~${x.netR.sum() * rk:+.0f} at the account's median $risk {rk:.2f})")
            P(f"   what-if: n {len(x)}, win {100*(x.netR>0).mean():.0f}%, sum gross {x.r_multiple.sum():+.2f}R, sum net {x.netR.sum():+.2f}R, avg net {x.netR.mean():+.3f}R")
            g = x.groupby("strategy").agg(n=("netR", "size"), win=("netR", lambda v: round(100 * (v > 0).mean())), sumR=("netR", "sum"),
                                          avgR=("netR", "mean")).round(3).sort_values("sumR")
            P(g.to_string())
        else:
            P("   by setup (unpriced):", s.strategy.value_counts().to_dict())
        if rsn == "twin held":
            hb = s["info"].map(lambda v: tuple(json.loads(v or "{}").get("held_by", [])))
            P("   held_by:", pd.Series([" / ".join(h) for h in hb]).value_counts().head(8).to_dict())
        if rsn == "setup daily loss limit":
            first = s.groupby("strategy").ts.min().sort_values()
            live = T[T.acct == a]
            for st, t0 in first.items():
                lt = live[live.strategy == st]
                t0 = pd.Timestamp(t0); et = pd.to_datetime(lt.et, utc=True); nt = pd.to_datetime(lt.nt, utc=True)
                pre = lt[et <= t0]; ovr = lt[(nt < t0) & (et > t0)]; aft = lt[nt >= t0]
                P(f"   {st}: realized at trip {pre.r_multiple.sum():+.2f}R(j) over {len(pre)}; open at trip {len(ovr)} lots -> {ovr.radj.sum():+.2f}R; "
                  f"entered after {len(aft)}; max same-poll cluster {int(lt.cluster.max())}")
                P(f"   {st}: tripped first {pd.Timestamp(t0).strftime('%H:%M')}, live {len(lt)} trades {lt.radj.sum():+.2f}R "
                  f"(${lt.pnl_adj.sum():+.2f}); blocked {int((s.strategy == st).sum())} signals; what-if {x[x.strategy == st].netR.sum():+.2f}R net "
                  f"over {int((x.strategy == st).sum())}")
open(OUT / "caps_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
