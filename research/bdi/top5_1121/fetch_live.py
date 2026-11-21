"""top5_1121: live trades for Part A (top-20 conditions) and Part B (top-5 execution).
Journal rows (run_id 1, closed) from every account journal on the mcf-data* branches (same reader as
mcf.report.footrace.live_trades, but keeping entry/exit time, side, MFE/MAE), R on the LR8 cost basis
(mcf.costs.cost_r_lr8 - every row priced with the live cost model, including rows before its 11-12 effective date),
identical signals across accounts counted once. GEN account rows kept in the file but excluded downstream.
Market data: Alpaca market-data GET only (daily bars of traded symbols 2026-07-01..11-21, SPY 1-minute per live date).
Compass at entry: research-scratch live_compass.parquet (10-13..11-10, backfilled + recorded) and the recorded
mcf-data-compass rows (11-06..11-20); 10-06..10-09 have no compass row -> 'unconfirmed'.
Usage (from the repo checkout so mcf imports): python fetch_live.py <scratch>. Educational only - not financial advice."""
import io
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, ".")
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.priors import _bars, _client  # noqa: E402
from mcf.research.shadow_calib import BRANCHES  # noqa: E402

S = Path(sys.argv[1]); S.mkdir(parents=True, exist_ok=True)
OLD = Path(__file__).resolve().parents[4] / "live_compass.parquet"  # scratchpad/live_compass.parquet
OLD = OLD if OLD.exists() else Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/live_compass.parquet")

cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw:
        print("no journal", acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush()
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT id, strategy, symbol, side, date, signal_time, entry_time, exit_time, entry, stop, target, exit, "
                        "exit_reason, meta, shares, pnl, pnl_adj, r_multiple, mae_r, mfe_r FROM trades "
                        "WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
    x["acct"] = acct
    parts.append(x)
T = pd.concat(parts, ignore_index=True)
T["date"] = T["date"].astype(str).str[:10]
T["r_journal"] = T["r_multiple"]
T["r_multiple"] = cost_r_lr8(T, cfg).astype(float)
T = T[T.r_multiple.notna()]
T["k"] = T.strategy + "|" + T.symbol + "|" + T.date + "|" + T.entry_time.astype(str).str[:16]
order = {a: i for i, a in enumerate(BRANCHES)}
T = T.sort_values("acct", key=lambda s: s.map(order)).drop_duplicates("k").drop(columns=["meta"])
T.to_parquet(S / "trades.parquet")
print("trades", len(T), T.date.min(), T.date.max(), T.groupby("acct").size().to_dict())

dc = _client()
syms = sorted(set(T.symbol) | {"SPY", "QQQ"})
D = _bars(dc, syms, datetime(2026, 7, 1), datetime(2026, 11, 21), None, "sip").reset_index()
D.to_parquet(S / "daily.parquet")
print("daily", len(D), D.symbol.nunique())
fr = []
for d in sorted(T.date.unique()):
    a = datetime.combine(pd.Timestamp(d).date(), datetime.min.time()) + timedelta(hours=13)
    raw = _bars(dc, ["SPY"], a, a + timedelta(hours=8), 1, "sip")
    x = rth(normalize(raw.droplevel(0)))
    fr.append(x.reset_index().rename(columns={"index": "ts", "timestamp": "ts"}))
M = pd.concat(fr, ignore_index=True)
M.to_parquet(S / "spy_1m.parquet")
print("spy 1m", len(M), M.ts.min(), M.ts.max())

old = pd.read_parquet(OLD)
old["source"] = old["backfilled"].map(lambda b: "backfill" if b else "recorded") if "backfilled" in old else "old"
rows = [old[["date", "T", "w60", "source"]]]
for p in subprocess.check_output(["git", "ls-tree", "--name-only", "origin/mcf-data-compass", "compass/"]).decode().split():
    d = p[8:18]
    if p.endswith(".csv") and d[:4] == "2026" and d > old.date.max():
        r = pd.read_csv(io.BytesIO(subprocess.check_output(["git", "show", f"origin/mcf-data-compass:{p}"])))
        r["date"] = d; r["source"] = "recorded"
        rows.append(r[["date", "T", "w60", "source"]])
C = pd.concat(rows, ignore_index=True)
C.to_parquet(S / "compass.parquet")
print("compass sessions", C.date.nunique(), C.groupby("source").date.nunique().to_dict())
