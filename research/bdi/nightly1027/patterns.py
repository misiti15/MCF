"""Live-record checks behind tonight's backlog ideas (all accounts, real trades run 1, 2026-10-06..10-27, costs in:
R = pnl_adj / $ risk). Needs <scratch>/<acct>/journal.db and <scratch>/QQQ_hist.parquet (SIP 1-min, 10-06..10-27).
A) longs on inverse ETFs vs other longs; B) failed-PDL-break longs (CWT14 pdl family) entered while QQQ was still
making new lows (QQQ low of day set in the 15 min before entry) vs later; C) shorts entered 09:50-09:59 by account /
up vs down QQQ days. Descriptive splits only. Usage: python patterns.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
INV = {"SQQQ", "SOXS", "SPXS", "SPXU", "SDOW", "SDS", "QID", "PSQ", "SH", "TZA", "SRTY", "LABD", "FAZ", "TECS", "YANG",
       "DRV", "ERY", "WEBS", "FNGD", "TSLQ", "TSLS", "NVDQ", "NVDS", "NVD", "MSTZ", "CONI", "SMST", "ETQ", "SARK", "DUST",
       "JDST", "KOLD", "SCO", "ZSL", "BITI", "SBIT", "REW", "SSG", "SPDN", "DOG", "RWM", "HIBS", "WANT", "AMDD", "AAPD",
       "METD", "MSFD", "GGLS", "AMZD", "PLTD", "CRWD-INV"}
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, symbol, strategy, side, entry, stop, shares, pnl_adj, entry_time from trades "
                    "where run_id=1 and date >= '2026-10-06' and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
out = []; P = lambda *x: out.append(" ".join(str(y) for y in x))
def s(d): return f"n {len(d)}, win {100 * (d.pnl_adj > 0).mean():.0f}%, avgR {d.R.mean():+.3f}, sumR {d.R.sum():+.1f}, ${d.pnl_adj.sum():+.0f}, days {d.date.nunique()}"
# A
L = T[T.side == 1]; inv = L.symbol.isin(INV)
P("== A) longs on inverse ETFs vs other longs (all accounts, 10-06..10-27)")
P("inverse ETF longs:", s(L[inv])); P("other longs:      ", s(L[~inv]))
P("inverse longs by date:", L[inv].groupby("date").R.agg(["size", "sum"]).round(2).to_dict("index"))
P("inverse longs by symbol:", L[inv].groupby("symbol").R.agg(["size", "sum"]).round(2).sort_values("size").tail(10).to_dict("index"))
P("inverse longs by setup:", L[inv].groupby("strategy").R.agg(["size", "sum"]).round(2).sort_values("size").tail(10).to_dict("index"))
# per-day sign check: inverse-ETF longs on QQQ up days vs down days
Q = pd.read_parquet(S / "QQQ_hist.parquet"); Q.index = pd.to_datetime(Q.index, utc=True).tz_convert(TZ)
Q = Q.between_time("09:30", "15:59"); Q["d"] = Q.index.strftime("%Y-%m-%d")
qday = Q.groupby("d").apply(lambda g: g.close.iloc[-1] / g.open.iloc[0] - 1)
L = L.assign(qup=L.date.map(qday) > 0)
P("inverse longs, QQQ up day:", s(L[inv & L.qup])); P("inverse longs, QQQ down day:", s(L[inv & ~L.qup]))
P("other longs, QQQ up day:", s(L[~inv & L.qup])); P("other longs, QQQ down day:", s(L[~inv & ~L.qup]))
# B
B = T[T.strategy.str.startswith("CWT14-failbrk-pdl")].copy()
def qlow_age(ts):
    g = Q[(Q.d == ts.strftime("%Y-%m-%d")) & (Q.index < ts.floor("1min"))]
    if g.empty: return np.nan
    return (ts.floor("1min") - g.low.idxmin()).total_seconds() / 60
B["qlow_age"] = [qlow_age(x) for x in B.nt]
P("\n== B) failed-PDL-break longs (CWT14 pdl family), by minutes since QQQ set its low of day (at entry)")
for lo, hi in [(0, 15), (15, 60), (60, 999)]:
    d = B[(B.qlow_age >= lo) & (B.qlow_age < hi)]; P(f"QQQ low {lo}-{hi} min ago:", s(d))
d = B[B.qlow_age < 15]
P("  <15 min by date:", d.groupby("date").R.agg(["size", "sum"]).round(2).to_dict("index"))
d = B[B.qlow_age >= 15]
P("  >=15 min by date:", d.groupby("date").R.agg(["size", "sum"]).round(2).to_dict("index"))
for st, g in B.groupby("strategy"):
    P(f"  {st}: <15 {s(g[g.qlow_age < 15])} | >=15 {s(g[g.qlow_age >= 15])}")
# C
C = T[(T.side == -1)]
C = C.assign(hm=C.nt.dt.strftime("%H:%M"), qup=C.date.map(qday) > 0)
e = C[C.hm < "10:00"]
P("\n== C) shorts entered before 10:00 vs later")
P("before 10:00:", s(e)); P("10:00 or later:", s(C[C.hm >= "10:00"]))
P("before 10:00, QQQ up day:", s(e[e.qup])); P("before 10:00, QQQ down day:", s(e[~e.qup]))
P("before 10:00 by date:", e.groupby("date").R.agg(["size", "sum"]).round(1).to_dict("index"))
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(OUT / "patterns_out.txt", "w").write(txt); print(txt)
