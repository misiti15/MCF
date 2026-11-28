"""Reviewer re-check of long_edge headline numbers from the journals (LR8 via mcf.costs.cost_r_lr8, same dedup as
footrace.live_trades, side kept). SPY day type from Alpaca daily bars (GET only). Usage: python recheck.py
Educational only - not financial advice."""
import sqlite3, subprocess, tempfile
from datetime import datetime
import numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush(); con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, entry, stop, target, exit, exit_reason, meta, shares, pnl,"
                        " pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con); con.close()
    x["account"] = acct; parts.append(x)
t = pd.concat(parts, ignore_index=True); t["date"] = t.date.astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float); t = t[t.r.notna()]
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
t = t.drop_duplicates("k"); t = t[(t.date >= "2026-10-23") & (t.date <= "2026-11-27")]
print("side values:", t.side.value_counts().to_dict())
L = t[t.side.astype(str).isin(["1", "long", "buy"]) | (pd.to_numeric(t.side, errors="coerce") > 0)]
A = L[L.account != "graveyard"]; B = L[L.account == "graveyard"]
for n, U in [("A", A), ("B", B)]:
    print(n, "lots", len(U), "days", U.date.nunique(), "R %.1f" % U.r.sum(), "avg %.3f" % U.r.mean())
from alpaca.data.enums import DataFeed
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from mcf.data.alpaca_data import _client
d = _client().get_stock_bars(StockBarsRequest(symbol_or_symbols="SPY", timeframe=TimeFrame.Day, start=datetime(2026, 10, 20),
                             end=datetime(2026, 11, 28), feed=DataFeed("sip"))).df.reset_index()
d["date"] = pd.to_datetime(d.timestamp).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
oc = (d.set_index("date").close / d.set_index("date").open - 1) * 100
A = A.assign(spy=A.date.map(oc)); A["typ"] = pd.cut(A.spy, [-99, -0.3, 0.3, 99], labels=["down", "flat", "up"])
g = A.groupby("typ", observed=True).r.agg(["count", "sum", "mean", lambda s: 0])
g["days"] = A.groupby("typ", observed=True).date.nunique(); print(g.iloc[:, [0, 1, 2]].assign(days=g.days).round(3))
print("down share of loss %.3f" % (A[A.typ == "down"].r.sum() / A.r.sum()))
up = A[A.typ == "up"]; print("up w/o 11-25 avg %.3f" % up[up.date != "2026-11-25"].r.mean())
def dayt(s): return s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
for st in ["GEN-261020-09", "CWT14-failbrk-orl-p10-long-WB5", "GEN-261023-07", "GEN-261027-10", "ULT-05-withgap-cont-long"]:
    g = A[A.strategy.str.startswith(st)]
    if not len(g): print(st, "none"); continue
    dd = g.groupby("date").r.sum(); tot = dd.sum()
    print(f"{st}: setups {g.strategy.nunique()} lots {len(g)} days {len(dd)} R {tot:.1f} w/o best {tot-dd.max():.1f} "
          f"best {dd.idxmax()} share {dd.max()/tot if tot>0 else float('nan'):.2f} day_t {dayt(dd):.2f}")
st = A.groupby("strategy").r.agg(["count", "sum"]); st = st[st["count"] >= 50]
wob = A[A.strategy.isin(st.index)].groupby(["strategy", "date"]).r.sum().groupby(level=0).apply(lambda s: s.sum() - s.max())
print("setups>=50:", len(st), "pos", int((st["sum"] > 0).sum()), "pos w/o best day", int((wob > 0).sum()))
# random-draw check for the two survivors as a set (same days, same counts), per-lot R w/o best day
