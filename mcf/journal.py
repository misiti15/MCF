"""SQLite journal holding every backtest run and every paper/live trade.

The dashboard reads exclusively from here, so backtests and paper results are
compared on the same footing day over day.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,            -- backtest | paper | live
    label TEXT,
    created_at TEXT NOT NULL,
    config TEXT,
    summary TEXT
);
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    symbol TEXT, strategy TEXT, side INTEGER, date TEXT,
    signal_time TEXT, entry_time TEXT, entry REAL, stop REAL, target REAL,
    exit_time TEXT, exit REAL, exit_reason TEXT,
    r_multiple REAL, mae_r REAL, mfe_r REAL, success INTEGER, shares INTEGER, pnl REAL, meta TEXT,
    broker_order_id TEXT
);
CREATE INDEX IF NOT EXISTS trades_run ON trades(run_id);
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, day TEXT, ts TEXT, symbol TEXT, strategy TEXT, side INTEGER,
    ref_price REAL, stop REAL, target REAL, entry_type TEXT, entry_price REAL, bar_index INTEGER,
    status TEXT,                   -- submitted | skipped | shadow | rejected | dry_run
    reason TEXT, qty INTEGER, broker_order_id TEXT, info TEXT
);
CREATE INDEX IF NOT EXISTS signals_day ON signals(run_id, day);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, created_at TEXT, symbol TEXT, strategy TEXT, side INTEGER,
    qty INTEGER, entry_ref REAL, stop REAL, target REAL,
    broker_order_id TEXT UNIQUE, status TEXT, meta TEXT
);
"""

TRADE_COLS = [
    "symbol", "strategy", "side", "date", "signal_time", "entry_time", "entry", "stop", "target",
    "exit_time", "exit", "exit_reason", "r_multiple", "mae_r", "mfe_r", "success", "shares", "pnl", "meta",
]


class Journal:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(SCHEMA)
        cols = {r[1] for r in self.db.execute("PRAGMA table_info(trades)")}
        for col, typ in (("success", "INTEGER"), ("slip_bps", "REAL"), ("pnl_adj", "REAL")):
            if col not in cols:  # additive migrations for older journals
                self.db.execute(f"ALTER TABLE trades ADD COLUMN {col} {typ}")
        self.db.commit()

    def new_run(self, kind: str, label: str = "", config: dict | None = None) -> int:
        cur = self.db.execute(
            "INSERT INTO runs(kind,label,created_at,config) VALUES(?,?,?,?)",
            (kind, label, datetime.now(timezone.utc).isoformat(), json.dumps(config or {}, default=str)),
        )
        self.db.commit()
        return int(cur.lastrowid)

    def get_or_create_run(self, kind: str, label: str) -> int:
        row = self.db.execute("SELECT id FROM runs WHERE kind=? AND label=?", (kind, label)).fetchone()
        return int(row[0]) if row else self.new_run(kind, label)

    def add_trades(self, run_id: int, trades: pd.DataFrame) -> None:
        if trades is None or trades.empty:
            return
        df = trades.copy()
        for c in TRADE_COLS:
            if c not in df:
                df[c] = None
        df = df[TRADE_COLS + [c for c in ("broker_order_id", "slip_bps", "pnl_adj") if c in df]]
        for c in ("date", "signal_time", "entry_time", "exit_time"):
            df[c] = df[c].astype(str)
        df.insert(0, "run_id", run_id)
        df.to_sql("trades", self.db, if_exists="append", index=False)
        self.db.commit()

    def set_summary(self, run_id: int, summary: dict) -> None:
        self.db.execute("UPDATE runs SET summary=? WHERE id=?", (json.dumps(summary, default=str), run_id))
        self.db.commit()

    def runs(self) -> pd.DataFrame:
        return pd.read_sql("SELECT * FROM runs ORDER BY id", self.db)

    def trades(self, run_id: int | None = None, kind: str | None = None) -> pd.DataFrame:
        q, args = "SELECT t.* FROM trades t JOIN runs r ON r.id=t.run_id WHERE 1=1", []
        if run_id is not None:
            q += " AND t.run_id=?"
            args.append(run_id)
        if kind is not None:
            q += " AND r.kind=?"
            args.append(kind)
        df = pd.read_sql(q + " ORDER BY t.entry_time", self.db, params=args)
        for c in ("entry_time", "exit_time", "signal_time"):
            df[c] = pd.to_datetime(df[c], utc=True, errors="coerce", format="ISO8601").dt.tz_convert("America/New_York")
        return df

    def latest_run(self, kind: str) -> int | None:
        row = self.db.execute("SELECT max(id) FROM runs WHERE kind=?", (kind,)).fetchone()
        return row[0]

    def record_order(self, run_id, symbol, strategy, side, qty, entry_ref, stop, target, order_id, status, meta=""):
        self.db.execute(
            "INSERT OR IGNORE INTO orders(run_id,created_at,symbol,strategy,side,qty,entry_ref,stop,target,"
            "broker_order_id,status,meta) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, datetime.now(timezone.utc).isoformat(), symbol, strategy, side, qty, entry_ref, stop,
             target, order_id, status, meta),
        )
        self.db.commit()

    def record_signal(self, run_id, day, ts, symbol, strategy, side, ref_price, stop, target, entry_type,
                      entry_price, bar_index, status, reason, qty=0, order_id=None, info=""):
        self.db.execute(
            "INSERT INTO signals(run_id,day,ts,symbol,strategy,side,ref_price,stop,target,entry_type,entry_price,"
            "bar_index,status,reason,qty,broker_order_id,info) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, day, ts, symbol, strategy, side, ref_price, stop, target, entry_type, entry_price,
             bar_index, status, reason, qty, order_id, info),
        )
        self.db.commit()

    def signals(self, run_id: int, day: str | None = None) -> pd.DataFrame:
        q, args = "SELECT * FROM signals WHERE run_id=?", [run_id]
        if day:
            q += " AND day=?"
            args.append(day)
        return pd.read_sql(q + " ORDER BY id", self.db, params=args)

    def open_orders(self, run_id: int) -> pd.DataFrame:
        return pd.read_sql("SELECT * FROM orders WHERE run_id=? AND status NOT IN ('closed','rejected','expired')",
                           self.db, params=[run_id])

    def update_order_status(self, order_id: str, status: str) -> None:
        self.db.execute("UPDATE orders SET status=? WHERE broker_order_id=?", (status, order_id))
        self.db.commit()
