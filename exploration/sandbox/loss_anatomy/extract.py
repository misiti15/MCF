"""Loss anatomy step 1: pull run-1 closed trades since 10-23 from all 10 journals (git show, read-only), compute
LR8 net R, gross R (pnl/risk), cost R, stop width, spread, ET entry minute; plus SPY minute bars for day types.
Usage: python extract.py <scratch_dir>   -> <scratch>/trades.parquet, <scratch>/spy.parquet
Educational only - not financial advice."""
import sqlite3, subprocess, sys, json, os
from datetime import datetime
import numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES, family_of

S = sys.argv[1]; cfg = load_config(); parts = []
for acct, br in BRANCHES.items():
    subprocess.run(["git", "-C", "/home/user/MCF", "fetch", "-q", "origin", br])
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    fn = f"{S}/j_{acct}.db"; open(fn, "wb").write(raw)
    con = sqlite3.connect(fn)
    x = pd.read_sql("SELECT id, strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, meta, "
                    "shares, pnl, pnl_adj, r_multiple, mae_r, mfe_r FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
    con.close(); os.remove(fn)
    x["date"] = x["date"].astype(str).str[:10]; x = x[x.date >= "2026-10-23"].reset_index(drop=True)
    x["r"] = cost_r_lr8(x, cfg).astype(float)
    x["account"] = acct; parts.append(x); print(acct, len(x), flush=True)
t = pd.concat(parts, ignore_index=True); t = t[t.r.notna()].copy()
risk = (t.entry - t.stop).abs() * t.shares.abs()
t["gross_r"] = np.where(risk > 0, t.pnl / risk, np.nan)
t["cost_r"] = t.gross_r - t.r
t["stop_bp"] = (t.entry - t.stop).abs() / t.entry * 1e4
def spr(m):
    try:
        return float(json.loads(str(m).split(";")[0]).get("spread_bps"))
    except Exception:
        return np.nan
t["spread_bp"] = t.meta.map(spr)
t["stop_spreads"] = t.stop_bp / t.spread_bp
et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
xt = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["entry_et"] = et; t["exit_et"] = xt
t["emin"] = et.dt.hour * 60 + et.dt.minute
t["hold_min"] = (xt - et).dt.total_seconds() / 60
t["family"] = t.strategy.map(family_of)
t["sidel"] = np.where(t.side > 0, "long", "short")
t = t.drop(columns=["meta"])
t.to_parquet(f"{S}/trades.parquet"); print("trades", len(t))
# SPY minute bars (Alpaca market data GET only)
try:
    from mcf.data.alpaca_data import fetch_bars
    b = fetch_bars(["SPY"], datetime(2026, 10, 20), datetime(2026, 11, 28), feed="iex")["SPY"]
    b.to_parquet(f"{S}/spy.parquet"); print("spy bars", len(b), b.index.min(), b.index.max())
except Exception as e:
    print("SPY fetch failed:", type(e).__name__, e)
