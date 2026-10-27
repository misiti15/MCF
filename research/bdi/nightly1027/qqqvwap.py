"""D) Sellers-into-strength shorts (MF3 / MF5 / MF1 families, all versions) and all other shorts: live R by QQQ above vs
below its session VWAP at entry (no lookahead: VWAP and close of the last complete 1-min bar before the entry). Same
inputs as patterns.py. Usage: python qqqvwap.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, symbol, strategy, side, entry, stop, shares, pnl_adj, entry_time from trades "
                    "where run_id=1 and date >= '2026-10-06' and exit is not null and side=-1", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
Q = pd.read_parquet(S / "QQQ_hist.parquet"); Q.index = pd.to_datetime(Q.index, utc=True).tz_convert(TZ)
Q = Q.between_time("09:30", "15:59").copy(); Q["d"] = Q.index.strftime("%Y-%m-%d")
tp = (Q.high + Q.low + Q.close) / 3
Q["vwap"] = (tp * Q.volume).groupby(Q.d).cumsum() / Q.volume.groupby(Q.d).cumsum()
def above(ts):
    g = Q[Q.index < ts.floor("1min") - pd.Timedelta(minutes=0)]
    g = g[g.d == ts.strftime("%Y-%m-%d")]
    return None if g.empty else bool(g.close.iloc[-1] > g.vwap.iloc[-1])
T["q_above"] = [above(x) for x in T.nt]
T["fam"] = T.strategy.str.extract(r"^(MF[135])")[0].fillna("other")
out = []
def s(d): return f"n {len(d)}, win {100 * (d.pnl_adj > 0).mean():.0f}%, avgR {d.R.mean():+.3f}, sumR {d.R.sum():+.1f}, days {d.date.nunique()}"
for f in ("MF1", "MF3", "MF5", "other"):
    d = T[T.fam == f]
    out.append(f"{f}: QQQ above VWAP {s(d[d.q_above == True])} | below {s(d[d.q_above == False])}")
d = T[T.fam != "other"]
out.append(f"MF1+3+5: above {s(d[d.q_above == True])} | below {s(d[d.q_above == False])}")
x = d[d.q_above == True].groupby("date").R.agg(["size", "sum"]).round(1)
out.append("MF1+3+5 above-VWAP by date: " + str(x.to_dict("index")))
x = d[d.q_above == False].groupby("date").R.agg(["size", "sum"]).round(1)
out.append("MF1+3+5 below-VWAP by date: " + str(x.to_dict("index")))
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(OUT / "qqqvwap_out.txt", "w").write(txt); print(txt)
