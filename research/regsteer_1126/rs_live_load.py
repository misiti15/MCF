"""REGSTEER-1126 live trades: mcf.report.footrace.live_trades() logic (run 1, LR8 cost-R, identical signals across accounts
counted once) plus entry_time and side, so each trade can be given its point-in-time state. Journals are copied (git show)
into a scratch dir and deleted after. Parity with live_trades() is asserted (same rows, same R).
Usage (repo root): python research/regsteer_1126/rs_live_load.py SCRATCH OUT.parquet. Educational only - not financial advice."""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SCR, OUT = Path(sys.argv[1]), Path(sys.argv[2])
os.environ["TMPDIR"] = str(SCR)            # live_trades() tempfiles also land in the scratch dir
import tempfile  # noqa: E402

tempfile.tempdir = str(SCR)
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
from mcf.report.footrace import live_trades  # noqa: E402
from mcf.research.shadow_calib import BRANCHES  # noqa: E402

cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw:
        continue
    p = SCR / f"j_{acct}.db"
    p.write_bytes(raw)
    con = sqlite3.connect(p)
    x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, entry, stop, target, exit, exit_reason, meta, shares, pnl, "
                    "pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
    con.close()
    p.unlink()
    x["account"] = acct
    parts.append(x)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()]
t["k"] = t["strategy"] + "|" + t["symbol"] + "|" + t["date"] + "|" + t["entry_time"].astype(str).str[:16]
t = t.drop_duplicates("k").reset_index(drop=True)
ref = live_trades()
assert len(ref) == len(t) and abs(ref.r.sum() - t.r.sum()) < 1e-6, (len(ref), len(t))
et = pd.to_datetime(t.entry_time.astype(str), utc=True, errors="coerce", format="mixed").dt.tz_convert("America/New_York")
t["em"] = et.dt.hour * 60 + et.dt.minute
t[["account", "strategy", "symbol", "side", "date", "em", "r"]].to_parquet(OUT)
print(len(t), "trades", t.date.min(), t.date.max(), "em median", t.em.median())
assert not any(f.name.endswith(".db") for f in SCR.iterdir())
