"""Load MarcoFlow's clean-window paper trades into the MCF journal as a reference source,
so the dashboard can show MarcoFlow's record side by side with MCF backtests/paper runs.

R is approximated as returnPct / stopPct (v7 per-trade stop when recorded, else MarcoFlow's
1.25% default hard stop). Labelled as MarcoFlow; never mixed into MCF results.
"""

from __future__ import annotations

import sqlite3
import sys

import pandas as pd

sys.path.insert(0, ".")
from mcf.config import load_config  # noqa: E402
from mcf.journal import Journal  # noqa: E402

DEFAULT_STOP = 1.25
LABEL = "MarcoFlow paper trades (clean 8/28+, reference)"


def main(db="data/marcoflow.sqlite"):
    cfg = load_config()
    t = pd.read_sql("""SELECT * FROM PaperTrade WHERE status='CLOSED' AND entryTime >= '2026-08-28'""",
                    sqlite3.connect(db))
    et = pd.to_datetime(t.entryTime, format="ISO8601").dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    xt = pd.to_datetime(t.exitTime, format="ISO8601").dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    stop_pct = t.stopPct.where(t.stopPct > 0, DEFAULT_STOP)
    side = t.direction.map({"LONG": 1, "SHORT": -1})
    out = pd.DataFrame({
        "symbol": t.symbol, "strategy": "mf_" + t.sessionSlot.fillna("na"), "side": side,
        "date": et.dt.date.astype(str), "signal_time": et, "entry_time": et, "entry": t.entryPrice,
        "stop": t.entryPrice * (1 - side * stop_pct / 100), "target": None, "exit_time": xt,
        "exit": t.exitPrice, "exit_reason": t.exitReason, "r_multiple": t.returnPct / stop_pct,
        "mae_r": -t.troughPct / stop_pct, "mfe_r": t.peakPct / stop_pct,
        "shares": t.shares.round().astype(int), "pnl": t.pnlDollars, "meta": "era=marcoflow",
    })
    j = Journal(cfg["data"]["journal_path"])
    old = j.db.execute("SELECT id FROM runs WHERE kind='reference' AND label=?", (LABEL,)).fetchall()
    for (rid,) in old:  # idempotent reload
        j.db.execute("DELETE FROM trades WHERE run_id=?", (rid,))
        j.db.execute("DELETE FROM runs WHERE id=?", (rid,))
    run = j.new_run("reference", LABEL)
    j.add_trades(run, out)
    print(f"loaded {len(out)} MarcoFlow trades as run {run}")


if __name__ == "__main__":
    main(*sys.argv[1:])
