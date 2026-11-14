"""sat1114 week scorecard 11-09..11-13: Primary, On Deck, Testing A-F (paper, R after costs = pnl_adj / risk, journal run 1),
Alpaca $ from each state branch's reports/pl_reconcile/<date>.json (alpaca_day_pl). Best / worst setups with display name,
week avg R without the setup's best session and that session's share (one-big-day rule).
Usage: python week.py <scratch with <acct>/journal.db>     Educational only - not financial advice."""
import json, sqlite3, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; ROOT = "/home/user/MCF"
DAYS = [f"2026-11-{d:02d}" for d in range(9, 14)]
AC = {"p": ("Primary", "mcf-data"), "od": ("On Deck", "mcf-data-testing"), "ta": ("Testing A", "mcf-data-testing2"),
      "tb": ("Testing B", "mcf-data-explore1"), "tc": ("Testing C", "mcf-data-livelab"), "td": ("Testing D", "mcf-data-testingd"),
      "te": ("Testing E", "mcf-data-testinge"), "tf": ("Testing F", "mcf-data-testingf")}
NM = json.load(open(Path(__file__).resolve().parents[3] / "docs/live/setup_names.json"))
name = lambda s: (NM.get(s) or {}).get("name", "") if isinstance(NM.get(s), dict) else ""
out = []; P = lambda *x: (out.append(" ".join(map(str, x))), print(*x))
rows, allt = [], []
for a, (nm, br) in AC.items():
    t = pd.read_sql("select date, strategy, side, entry, stop, shares, pnl_adj from trades where run_id=1 and exit is not null", sqlite3.connect(S / a / "journal.db"))
    t = t[t.date.isin(DAYS)].copy(); t["R"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares); t = t.dropna(subset=["R"]); t["acct"] = nm
    alp = {}
    for d in DAYS:
        raw = subprocess.run(["git", "-C", ROOT, "show", f"origin/{br}:reports/pl_reconcile/{d}.json"], capture_output=True).stdout
        try: alp[d] = json.loads(raw)["rows"][0]["alpaca_day_pl"]
        except Exception: pass
    d = t.groupby("date").R.sum()
    rows.append(dict(acct=nm, trades=len(t), R=t.R.sum(), avgR=t.R.mean(), win=(t.pnl_adj > 0).mean(), alpaca=sum(alp.values()),
                     green=f"{int((d > 0).sum())}/{len(d)}", byday=" ".join(f"{k[8:]}:{v:+.1f}" for k, v in d.items()),
                     alp_byday=" ".join(f"{k[8:]}:{v:+.0f}" for k, v in alp.items()), wobd=(d.sum() - d.max()) if len(d) > 1 else np.nan))
    allt.append(t)
T = pd.concat(allt)
R = pd.DataFrame(rows)
grp = {"Primary": ["Primary"], "On Deck": ["On Deck"], "Testing (all A-F)": [f"Testing {x}" for x in "ABCDEF"]}
P("# Week 2026-11-09..11-13 (paper, R after costs; $ = Alpaca day P/L from pl_reconcile)")
for g, accts in grp.items():
    x = T[T.acct.isin(accts)]; r = R[R.acct.isin(accts)]
    P(f"\n## {g}: {x.R.sum():+.1f}R | {len(x)} trades | avg {x.R.mean():+.3f}R | win {(x.pnl_adj > 0).mean():.0%} | Alpaca ${r.alpaca.sum():+,.2f}")
    for _, q in r.iterrows():
        P(f"   {q.acct}: {q.R:+.1f}R / {q.trades} tr (avg {q.avgR:+.3f}) Alpaca ${q.alpaca:+,.2f} | green {q.green} | R by day {q.byday} | $ by day {q.alp_byday}")
    s = x.groupby("strategy").agg(n=("R", "size"), R=("R", "sum"), avg=("R", "mean"), acct=("acct", "first"))
    for k in s.index:
        dd = x[x.strategy == k].groupby("date").R.sum()
        if len(dd) > 1:
            b = dd.idxmax(); s.loc[k, "wobd"] = x[(x.strategy == k) & (x.date != b)].R.mean()
            s.loc[k, "share"] = dd.max() / dd.sum() if dd.sum() > 0 else np.nan
    s = s.sort_values("R")
    fm = lambda k, q: (f"{name(k) or '?'} ({k}, {q.acct}) {q.R:+.1f}R / {int(q.n)} (avg {q.avg:+.3f}" +
                       (f", w/o best day {q.wobd:+.3f}" if pd.notna(q.get('wobd')) else "") +
                       (f", `1 day` {q.share:.0%}" if pd.notna(q.get('share')) and q.share >= 0.5 else "") + ")")
    P("   best: " + "; ".join(fm(k, q) for k, q in s.tail(3)[::-1].iterrows()))
    P("   worst: " + "; ".join(fm(k, q) for k, q in s.head(3).iterrows()))
    s.round(3).assign(group=g).to_csv(OUT / f"week_setups_{g.split()[0].lower()}.csv")
R.round(3).to_csv(OUT / "week_scorecard.csv", index=False)
open(OUT / "week_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
