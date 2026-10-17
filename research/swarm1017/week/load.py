"""Shared loader: all real trades (run_id=1) 2026-10-06..16, three accounts. Educational only - not financial advice."""
import sqlite3, sys, json, pandas as pd, numpy as np
from pathlib import Path
sys.path.insert(0, "/home/user/MCF")
S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swarm1017/week")
ACC = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2"}
LAST = ["2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]
THIS = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
L3 = ["2026-10-14", "2026-10-15", "2026-10-16"]; P3 = ["2026-10-09", "2026-10-12", "2026-10-13"]
# broker equity: first (pre-open) / last (closed) status.json per session (git log, see NOTES)
EQ = {"p": {"2026-10-06": (96392.28, 96246.97), "2026-10-07": (96270.79, 96049.85), "2026-10-08": (96008.13, 95924.41),
            "2026-10-09": (95922.54, 95683.70), "2026-10-12": (95681.05, 95798.98), "2026-10-13": (95798.13, 95702.74),
            "2026-10-14": (95708.17, 95771.70), "2026-10-15": (95771.26, 94909.43), "2026-10-16": (94906.62, 94913.79)},
      "t1": {"2026-10-09": (100000.0, 99975.08), "2026-10-12": (99974.20, 99993.16), "2026-10-13": (99989.44, 99335.17),
             "2026-10-14": (99328.40, 99393.61), "2026-10-15": (99387.69, 97714.67), "2026-10-16": (97710.52, 97691.12)},
      "t2": {"2026-10-12": (100000.0, 99336.73), "2026-10-13": (99330.06, 99223.39), "2026-10-14": (99211.34, 98050.88),
             "2026-10-15": (98044.38, 96768.04), "2026-10-16": (96758.29, 95775.80)}}

def trades():
    out = []
    for a in ACC:
        c = sqlite3.connect(S / a / "journal.db")
        t = pd.read_sql("select * from trades where run_id=1", c); t["acct"] = a; out.append(t)
    T = pd.concat(out, ignore_index=True)
    T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
    T["et"] = pd.to_datetime(T.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
    T["R1"] = (T.entry - T.stop).abs()
    T["risk"] = T.R1 * T.shares
    T["cost_r"] = ((T.pnl - T.pnl_adj) / T.risk).replace([np.inf, -np.inf], np.nan).fillna(0)
    T["r_adj"] = T.r_multiple - T.cost_r
    T["base"] = T.strategy.str.replace(r"-FD$", "", regex=True)
    T["win"] = T.pnl > 0
    return T

def bars(d):
    b = pd.read_parquet(S / "bars" / f"{d}.parquet")
    b["ts"] = pd.to_datetime(b.ts, utc=True).dt.tz_convert("America/New_York")
    return b

def index_day(d):
    b = bars(d); b = b[b.symbol.isin(["SPY", "QQQ", "IWM"])]
    b = b[(b.ts.dt.time >= pd.Timestamp("09:30").time()) & (b.ts.dt.time < pd.Timestamp("16:00").time())]
    r = {}
    for s, g in b.groupby("symbol"):
        o, c = g.open.iloc[0], g.close.iloc[-1]; r[s] = round(100 * (c / o - 1), 2)
    return r
