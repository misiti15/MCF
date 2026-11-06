"""Step 6 candidate cards 2026-11-06: combined.csv + ex-market (BETA1 sums merged across all 7 account scorecards) +
playing time (Primary scorecard) + 3-busiest avg R and per-account split from journals. Costs in (R = pnl_adj / $ risk).
Usage: python cands.py <scratch>   Educational only - not financial advice."""
import sys, json, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.analytics import market_beta
from mcf import setup_names
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
AC = ["p", "t1", "t2", "gy", "gen", "ex1", "ll"]
C = pd.read_csv(OUT / "combined.csv").set_index("setup")
parts = {}
for a in AC:
    for r in json.load(open(S / a / "reports" / "scorecard.json"))["leaderboard"]:
        if r.get("mkt_n"):
            parts.setdefault(r["setup"], []).append({k: r[k] for k in market_beta.KEYS})
ex = {k: market_beta.fit(market_beta.merge(v)) for k, v in parts.items()}
pt = json.load(open(S / "p" / "reports" / "scorecard.json")).get("playing_time") or {}
rows = []
for a in AC:
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, entry, stop, shares, pnl_adj from trades where run_id=1 and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows); T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0]; T["R"] = T.pnl_adj / T.risk
L = ["MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "NS1-rsidip-rsi5pop-long", "MF4-h40-open-flowsell",
     "L3-gap-slope-rsi5hi-FD", "NS5-sma50-flush-oversold-long", "ST7-rsi50dn-long-pm-t1s1-FD", "L3-gap-slope-fromopen-FD",
     "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD"]
L += sys.argv[2].split(",") if len(sys.argv) > 2 else []
out = []
for k in L:
    d = T[T.strategy == k]; by = d.groupby("date").R.agg(["sum", "size"])
    busy = by.sort_values("size", ascending=False).head(3).index
    c = C.loc[k] if k in C.index else None
    e = ex.get(k) or {}
    pp = pt.get(k) if isinstance(pt, dict) else None
    out.append(dict(setup=k, name=setup_names.name(k), now=None if c is None else c.now, trades=len(d), sessions=len(by),
                    win=round((d.pnl_adj > 0).mean(), 3), be_win=None if c is None else c.be_win, avgR=round(d.R.mean(), 3),
                    exmkt=None if not e else round(e.get("exmkt_r") or np.nan, 3), exbest=None if c is None else c.exbest,
                    best_share=None if c is None else c.best_share, t_day=None if c is None else c.t_day,
                    last4=None if c is None else c.last4_R, bt=None if c is None else c.bt, busy3=round(d[d.date.isin(busy)].R.mean(), 3),
                    pnl=round(d.pnl_adj.sum(), 2), by_acct={a: (int((d.acct == a).sum()), round(d[d.acct == a].R.mean(), 3)) for a in d.acct.unique()},
                    playing=pp if pp is None or len(str(pp)) < 200 else str(pp)[:200]))
txt = pd.DataFrame(out).to_string(); print(txt)
open(OUT / "cands_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
