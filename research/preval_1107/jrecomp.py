"""PREVAL 1107 step C (method 2, journal-based recomputation). For each session and book: the candidate stream is
  - setups in Primary that day (mcf-data setups/<date>.json): Primary's live trades (run 1, R = pnl_adj / risk) plus its
    journaled what-ifs (run 2) for signals blocked only by the account halt ('halted' / 'daily loss limit'), the per-setup
    latch ('setup daily loss limit') or 'twin held' (only when the twin is not in the book). What-ifs have no fills: R =
    r_multiple - modelled costs (2 x (1 bp + $0.01) per share + $0.02 on stop exits) / |entry - stop|;
  - setups not in Primary that day: their home-account live trades that day (Testing 1 / Testing 2 / Live Lab / Explore 1,
    R after costs; no Graveyard / Gen rows).
Then Primary's rules are re-applied in time order: one open position per symbol for added rows (what-ifs / home trades;
Primary's live fills passed that check live; setup order = Primary's), the -2R
per-setup latch (net realized R in exit order, from 10-29 as live; applied to all sessions here = today's rules), the
-20R account halt (realized; both counted on journal r_multiple as live, scored on R after costs). Slots (77) / buying power are not binding on these books (max concurrent checked).
Usage: python jrecomp.py <scratch> <first-date>   Educational only - not financial advice."""
import sys, json, sqlite3, subprocess
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
S = Path(sys.argv[1]); FIRST = sys.argv[2]; OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT)); sys.argv = sys.argv[:1]
BOOKS = {}
exec(open(OUT / "replay.py").read().split("CACHE =")[0].split("from mcf.report import team as T")[1])  # BOOKS / ASIS
BOOKS = {k: [s["id"] for s in v] for k, v in BOOKS.items()}
ORDER = ["RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "MF2-open-rsimidhi-flowsell-FD",
         "MF4-h40-open-flowsell-FD", "ST7-rsi50dn-long-pm-t1s1-FD", "L3-gap-slope-rsi5hi-FD", "L3-gap-slope-fromopen-FD",
         "NS1-rsidip-rsi5pop-long", "NS5-sma50-flush-oversold-long", "MF4-h40-open-flowsell",
         "CWT09-gapdn-vwaploss-g10-short", "NM-ETF-late-dip-di-long"]
TWIN = {"MF4-h40-open-flowsell": "MF4-h40-open-flowsell-FD", "MF4-h40-open-flowsell-FD": "MF4-h40-open-flowsell"}
def git(*a): return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout
cols = "date, strategy, symbol, side, entry_time, exit_time, entry, stop, shares, pnl, pnl_adj, r_multiple, exit_reason, meta, run_id"
P = pd.read_sql(f"select {cols} from trades where run_id in (1,2) and date>=? and exit is not null", sqlite3.connect(S / "p" / "journal.db"), params=(FIRST,))
H = []
for a in ("t1", "t2", "ll", "ex1"):
    x = pd.read_sql(f"select {cols} from trades where run_id=1 and date>=? and exit is not null", sqlite3.connect(S / a / "journal.db"), params=(FIRST,))
    x["acct"] = a; H.append(x)
H = pd.concat(H)
dates = sorted(P.date.unique())
inprim = {d: {k for k, v in (json.loads(git("show", f"origin/mcf-data:setups/{d}.json") or "{}").get("strategies") or {}).items() if v.get("enabled", True)} for d in dates}
def why(m): return (m or "").split("why=")[-1]
def rr(df):
    risk = (df.entry - df.stop).abs()
    live = df.pnl_adj.fillna(df.pnl) / (risk * df.shares.replace(0, np.nan))
    cost = (2 * (0.0001 * df.entry + 0.01) + np.where(df.exit_reason == "stop", 0.02, 0)) / risk
    return np.where(df.run_id == 1, live, df.r_multiple - cost)
def stream(book, d):
    rows = []
    for s in book:
        if s in inprim[d]:
            x = P[(P.date == d) & (P.strategy == s)].copy()
            w = x.meta.map(why)
            ok = (x.run_id == 1) | w.isin(["halted", "daily loss limit", "setup daily loss limit"]) | \
                 ((w == "twin held") & (TWIN.get(s) not in book))
            x = x[ok]; x["src"] = np.where(x.run_id == 1, "P live", "P what-if")
        else:
            x = H[(H.date == d) & (H.strategy == s)].copy(); x["src"] = x.acct.map(lambda a: f"{a} live")
        rows.append(x)
    x = pd.concat(rows)
    x = x[(x.entry - x.stop).abs() > 0].copy()
    x["R"] = rr(x)
    x["rm"] = x.r_multiple.fillna(x.R)   # the live latch / halt count journal r_multiple (realized)
    x["et"] = pd.to_datetime(x.entry_time, utc=True, format="mixed"); x["xt"] = pd.to_datetime(x.exit_time, utc=True, format="mixed")
    x["pri"] = x.strategy.map(lambda s: ORDER.index(s) if s in ORDER else 99)
    return x.sort_values(["et", "pri"]).dropna(subset=["R"])
def apply_rules(x):
    acc, open_, closed = [], [], []    # closed: (xt, strategy, R)
    halted, latched, maxc = False, set(), 0
    for t in x.itertuples():
        # realize exits before this entry
        for o in [o for o in open_ if o.xt < t.et]:
            open_.remove(o); closed.append(o)
        closed.sort(key=lambda o: o.xt)
        tot, by = 0.0, {}
        for o in closed:
            tot += o.rm; by[o.strategy] = by.get(o.strategy, 0) + o.rm
            if tot <= -20: halted = True
            if by[o.strategy] <= -2: latched.add(o.strategy)
        # Primary's own live fills already passed the symbol / slot checks live (scale-out legs are separate rows)
        clash = t.src != "P live" and any(o.symbol == t.symbol for o in open_)
        # a setup's own live fills are identical in every book, so its latch is as live: live rows are never latched here
        latch = t.src != "P live" and t.strategy in latched
        if halted or latch or clash:
            continue
        open_.append(t); acc.append(t); maxc = max(maxc, len(open_))
    return pd.DataFrame(acc), maxc
import os
if os.environ.get("DBG"):
    b, d = os.environ["DBG"].split(",")
    x = stream(BOOKS[b], d); a, mc = apply_rules(x)
    print(x.groupby(["strategy", "src"]).R.agg(["size", "sum"]).round(2)); print(a.groupby(["strategy", "src"]).R.agg(["size", "sum"]).round(2))
    sys.exit()
res, per = [], []
for b, book in BOOKS.items():
    for d in dates:
        a, mc = apply_rules(stream(book, d))
        res.append(dict(book=b, date=d, trades=len(a), R=a.R.sum() if len(a) else 0.0, maxconc=mc,
                        whatif=int((a.src == "P what-if").sum()) if len(a) else 0, home=int(a.src.str.contains("t1|t2|ll|ex1").sum()) if len(a) else 0))
        if len(a):
            for s, g in a.groupby("strategy"): per.append(dict(book=b, date=d, setup=s, trades=len(g), R=g.R.sum()))
R = pd.DataFrame(res); R.to_csv(OUT / "jrecomp_days.csv", index=False, float_format="%.3f")
pd.DataFrame(per).to_csv(OUT / "jrecomp_setups.csv", index=False, float_format="%.3f")
act = pd.read_sql("select date, sum(pnl_adj / (abs(entry-stop)*shares)) R, count(*) n from trades where run_id=1 and exit is not null and date>=? group by date",
                  sqlite3.connect(S / "p" / "journal.db"), params=(FIRST,)).set_index("date")
pv = R.pivot(index="date", columns="book", values="R"); pv["actual"] = act.R
print(pv.round(2).to_string()); print(R.groupby("book")[["trades", "whatif", "home", "maxconc"]].agg(["sum", "max"]))
def summ(c):
    v = pv[c]; return dict(total=v.sum(), avg=v.mean(), green=f"{int((v > 0).sum())}/{len(v)}", worst=v.min(), worst_day=v.idxmin(), d1105=v.get("2026-11-05"), d1106=v.get("2026-11-06"))
for win, sub in (("all", pv.index), ("last10", pv.index[-10:])):
    print(win, len(sub)); pv0 = pv; pv = pv0.loc[sub]
    print(pd.DataFrame({c: summ(c) for c in ["actual", "asis", "opt1", "opt1b", "opt2", "opt2b"]}).T.to_string()); pv = pv0
