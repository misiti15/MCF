"""BDI 1127 step 0 (copy of research/bdi/1125/acct.py, SPY request end moved to 11-28; half day 11-27 close 13:00 ET, SPY day type from the 13:00 close): per-account session lines (R after costs = pnl_adj / $ risk), realised-path peak vs close, best/
setup, and avg R per session by SPY day type 10-06..11-20 (up > +0.25% open->close, down < -0.25%, quiet between).
Usage: python acct.py <scratch> <day>. Journals: <scratch>/<acct>/journal.db (git show of the mcf-data* branches).
Alpaca market-data GET only (SPY daily). Educational only - not financial advice."""
import sqlite3, sys
from datetime import datetime
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.priors import _client
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

S, D = Path(sys.argv[1]), sys.argv[2]
ACC = [("p", "Primary"), ("od", "On Deck"), ("ta", "Testing A"), ("tb", "Testing B"), ("tc", "Testing C"), ("td", "Testing D"),
       ("te", "Testing E"), ("tf", "Testing F"), ("gen", "Gen"), ("gy", "Graveyard")]
dc = _client()
b = dc.get_stock_bars(StockBarsRequest(symbol_or_symbols="SPY", timeframe=TimeFrame.Day, start=datetime(2026, 10, 1),
                                       end=datetime(2026, 11, 28), feed="sip")).df.droplevel(0)
b.index = b.index.tz_convert("America/New_York").date
oc = (b.close / b.open - 1) * 100
dtype = oc.apply(lambda x: "up" if x > 0.25 else ("down" if x < -0.25 else "quiet"))
print("SPY open->close today %+.2f%% (%s)" % (oc.loc[pd.Timestamp(D).date()], dtype.loc[pd.Timestamp(D).date()]))
win = [d for d in dtype.index if pd.Timestamp("2026-10-06").date() <= d < pd.Timestamp(D).date()]
print("window sessions:", pd.Series([dtype[d] for d in win]).value_counts().to_dict())
for a, name in ACC:
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select symbol, strategy, side, date, exit_time, entry, stop, shares, pnl_adj from trades where run_id=1 "
                    "and date>='2026-10-06' and date<=?", c, params=(D,))
    t["R"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares).replace(0, np.nan)
    d = t[t.date == D].copy()
    if d.empty:
        print(f"{name}: no trades"); continue
    d["xt"] = pd.to_datetime(d.exit_time, utc=True, format="mixed"); d = d.sort_values("xt")
    path = d.R.cumsum(); pk = path.max(); pkt = d.xt.iloc[int(np.argmax(path.to_numpy()))].tz_convert("America/New_York")
    st = d.groupby("strategy").R.agg(["sum", "count"]).sort_values("sum")
    h = t[t.date < D].groupby("date").R.sum()
    h.index = pd.to_datetime(h.index).date
    by = {k: (h[[x for x in h.index if x in win and dtype[x] == k]]) for k in ("up", "quiet", "down")}
    L, Sh = d[d.side == 1].R.sum(), d[d.side == -1].R.sum()
    print(f"| {name} | {len(d)} | {d.R.mean():+.3f} | {d.R.sum():+.2f} | {L:+.2f} / {Sh:+.2f} | {pk:+.2f} ({pkt:%H:%M}) | "
          f"{st.index[-1]} {st['sum'].iloc[-1]:+.2f} ({st['count'].iloc[-1]}) | {st.index[0]} {st['sum'].iloc[0]:+.2f} ({st['count'].iloc[0]}) | "
          + " | ".join(f"{v.mean():+.2f} ({len(v)})" if len(v) else "—" for v in by.values()) + " |")
