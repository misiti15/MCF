"""BD&I Saturday 1121: week scorecard 11-16..11-20, all accounts (paper, Live engine). R after costs = LR8 basis
(mcf.costs.cost_r_lr8: every row this week is on/after 2026-11-12, so it is the journal's booked pnl_adj / $ risk);
journal run 1, closed trades, per account (a signal taken in two accounts counts in both). Alpaca $ = each state
branch's reports/pl_reconcile/<date>.json alpaca_day_pl; account R = $ / (0.25% of that day's close equity).
Best / worst setups with display name, avg R w/o best session, its share, avg R w/o top-2 days and day-clustered t.
Usage: python week.py <scratch with <acct>/journal.db>     Educational only - not financial advice."""
import json, sqlite3, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
DAYS = [f"2026-11-{d:02d}" for d in range(16, 21)]
AC = {"primary": ("Primary", "mcf-data"), "testing": ("On Deck", "mcf-data-testing"), "testing2": ("Testing A", "mcf-data-testing2"),
      "explore1": ("Testing B", "mcf-data-explore1"), "livelab": ("Testing C", "mcf-data-livelab"), "testingd": ("Testing D", "mcf-data-testingd"),
      "testinge": ("Testing E", "mcf-data-testinge"), "testingf": ("Testing F", "mcf-data-testingf"), "gen": ("Gen", "mcf-data-gen"),
      "graveyard": ("Graveyard", "mcf-data-graveyard")}
NM = json.load(open(ROOT / "docs/live/setup_names.json"))
name = lambda s: (NM.get(s) or {}).get("name", "") if isinstance(NM.get(s), dict) else ""
CFG = load_config()
out = []; P = lambda *x: (out.append(" ".join(map(str, x))), print(*x))


def load(a):
    t = pd.read_sql("select * from trades where run_id=1 and exit_time is not null", sqlite3.connect(S / a / "journal.db"))
    t["date"] = t.date.astype(str).str[:10]
    t = t[t.date.isin(DAYS)].reset_index(drop=True)
    t["R"] = cost_r_lr8(t, CFG).astype(float)
    return t.dropna(subset=["R"])


def dct(x):
    d = x.groupby("date").R.mean()
    return d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 and d.std(ddof=1) > 0 else np.nan


rows, allt = [], []
for a, (nm, br) in AC.items():
    t = load(a); t["acct"] = nm
    alp, eq = {}, {}
    for d in DAYS:
        raw = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:reports/pl_reconcile/{d}.json"], capture_output=True).stdout
        try:
            r0 = json.loads(raw)["rows"][0]; alp[d] = r0["alpaca_day_pl"]; eq[d] = r0.get("equity_close")
        except Exception:
            pass
    acct_r = sum(alp[d] / (0.0025 * eq[d]) for d in alp if eq.get(d))
    d = t.groupby("date").R.sum()
    rows.append(dict(acct=nm, trades=len(t), R=round(t.R.sum(), 2), avgR=round(t.R.mean(), 4) if len(t) else np.nan,
                     win=round((t.R > 0).mean(), 3) if len(t) else np.nan, alpaca=round(sum(alp.values()), 2), acct_R=round(acct_r, 1),
                     green=f"{int((d > 0).sum())}/{len(d)}", byday=" ".join(f"{k[8:]}:{v:+.1f}" for k, v in d.items()),
                     wobd=round((t[t.date != d.idxmax()].R.mean()), 4) if len(d) > 1 else np.nan, t_day=round(dct(t), 2)))
    allt.append(t)
T = pd.concat(allt, ignore_index=True)
T[["acct", "date", "strategy", "symbol", "side", "entry_time", "exit_time", "R", "exit_reason"]].to_parquet(S / "week_trades.parquet")
Rr = pd.DataFrame(rows)
P("# Week 2026-11-16..11-20 (paper, Live engine, R after costs LR8 basis; $ = Alpaca day P/L)")
for _, q in Rr.iterrows():
    P(f"{q.acct}: {q.R:+.1f}R / {q.trades} tr (avg {q.avgR:+.3f}, w/o best day {q.wobd:+.3f}, day-t {q.t_day}) | Alpaca ${q.alpaca:+,.2f} "
      f"(account R {q.acct_R:+.1f}) | green {q.green} | by day {q.byday}")
for g in Rr.acct:
    x = T[T.acct == g]
    if not len(x):
        continue
    s = x.groupby("strategy").agg(n=("R", "size"), R=("R", "sum"), avg=("R", "mean"), days=("date", "nunique"))
    for k in s.index:
        xx = x[x.strategy == k]; dd = xx.groupby("date").R.sum()
        if len(dd) > 1:
            b = dd.idxmax(); s.loc[k, "wobd"] = xx[xx.date != b].R.mean()
            s.loc[k, "share"] = dd.max() / dd.sum() if dd.sum() > 0 else np.nan
            top2 = dd.nlargest(2).index; s.loc[k, "wo2"] = xx[~xx.date.isin(top2)].R.mean() if len(dd) > 2 else np.nan
            s.loc[k, "t_day"] = dct(xx)
    s = s.sort_values("R")
    fm = lambda k, q: (f"{name(k) or '?'} ({k}) {q.R:+.1f}R / {int(q.n)} (avg {q.avg:+.3f}" +
                       (f", w/o best day {q.wobd:+.3f}" if pd.notna(q.get('wobd')) else "") +
                       (f", `1 day` {q.share:.0%}" if pd.notna(q.get('share')) and q.share >= 0.5 else "") + ")")
    P(f"\n## {g}  best: " + "; ".join(fm(k, q) for k, q in s.tail(3)[::-1].iterrows()))
    P(f"## {g}  worst: " + "; ".join(fm(k, q) for k, q in s.head(3).iterrows()))
    if g == "Primary":
        P("Primary per setup:\n" + s.round(3).to_string())
        P("Primary by setup x day (R):\n" + x.pivot_table(index="strategy", columns="date", values="R", aggfunc="sum").round(1).fillna(0).to_string())
    s.round(3).assign(acct=g).to_csv(OUT / "scratch" / f"week_setups_{g.replace(' ', '_')}.csv")
Rr.to_csv(OUT / "week_scorecard.csv", index=False)
(OUT / "week_out.txt").write_text("\n".join(out) + "\n\nEducational only - not financial advice.\n")
