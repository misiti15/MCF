"""F) Flatten at 15:45 instead of 15:55: for every live trade still open at 15:45 that exited by the 15:55 flatten
(all accounts, 10-06..10-27), R if closed at the 15:45 1-min close (SIP) vs the actual flatten fill, costs as journaled
(the same per-trade cost is kept: pnl_adj - pnl). Fetches SIP 1-min bars 15:44-15:46 per day into <scratch>/f1545/.
Usage: python flat1545.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, symbol, strategy, side, entry, stop, shares, pnl, pnl_adj, entry_time, exit_time, exit_reason, exit "
                    "from trades where run_id=1 and date >= '2026-10-06' and exit is not null and exit_reason='flatten'", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["et"] = pd.to_datetime(T.exit_time, utc=True, format="mixed").dt.tz_convert(TZ)
T = T[(T.nt.dt.strftime("%H:%M") < "15:45") & (T.et.dt.strftime("%H:%M") >= "15:50")].copy()
D = S / "f1545"; D.mkdir(exist_ok=True); cl = _client(); px = {}
for d, g in T.groupby("date"):
    f = D / f"{d}.parquet"
    if f.exists():
        b = pd.read_parquet(f)
    else:
        y, m, dd = map(int, d.split("-"))
        a = pd.Timestamp(f"{d} 15:44", tz=TZ).tz_convert("UTC").to_pydatetime()
        z = pd.Timestamp(f"{d} 15:46", tz=TZ).tz_convert("UTC").to_pydatetime()
        syms = sorted(g.symbol.unique()); parts = []
        for i in range(0, len(syms), 100):
            for s, bb in fetch_bars(syms[i:i + 100], a, z, feed="sip", client=cl).items():
                bb = bb.copy(); bb["symbol"] = s; parts.append(bb)
        b = pd.concat(parts) if parts else pd.DataFrame(); b.to_parquet(f)
    b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
    b = b[b.index.strftime("%H:%M") == "15:44"]   # the bar that closes at 15:45
    for s, r in b.groupby("symbol"):
        px[(d, s)] = float(r.close.iloc[-1])
T["px1545"] = [px.get((d, s)) for d, s in zip(T.date, T.symbol)]
T = T[T.px1545.notna()].copy()
cost = T.pnl - T.pnl_adj
T["R1545"] = (T.side * (T.px1545 - T.entry) * T.shares - cost) / T.risk
T["d"] = T.R1545 - T.R
out = [f"trades open at 15:45 and flattened: n {len(T)}, days {T.date.nunique()}",
       f"actual (15:55 flatten) sum R {T.R.sum():+.1f}, avg {T.R.mean():+.3f}; at 15:45 sum R {T.R1545.sum():+.1f}, avg {T.R1545.mean():+.3f}; diff {T.d.sum():+.1f}R"]
g = T.groupby("date").d.sum()
out.append(f"days better at 15:45: {(g > 0).sum()} / worse {(g < 0).sum()}; t_day {g.mean() / (g.std(ddof=1) / len(g) ** .5):.2f}")
out.append("by date: " + str(g.round(2).to_dict()))
out.append("by account: " + str(T.groupby("acct").d.agg(["size", "sum"]).round(2).to_dict("index")))
out.append("by side: " + str(T.groupby("side").d.agg(["size", "sum"]).round(2).to_dict("index")))
out.append("best day share of the gain: " + (f"{g.max() / g.sum():.0%}" if g.sum() > 0 else "n/a (total <= 0)"))
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(OUT / "flat1545_out.txt", "w").write(txt); print(txt)
