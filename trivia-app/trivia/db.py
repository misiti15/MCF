"""SQLite storage. Small on purpose: swap for Postgres when there are real users."""
from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  token TEXT UNIQUE NOT NULL,
  name TEXT,
  phone TEXT,
  email TEXT,
  channel TEXT NOT NULL DEFAULT 'push',
  drop_size INTEGER NOT NULL DEFAULT 3,
  mix TEXT NOT NULL DEFAULT 'ramp',
  send_days TEXT NOT NULL DEFAULT '["Mon","Tue","Wed","Thu","Fri"]',
  send_time TEXT NOT NULL DEFAULT '12:15',
  tz TEXT NOT NULL DEFAULT 'America/New_York',
  level_theme TEXT NOT NULL DEFAULT 'fan',
  sms_opt_in INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_topics (
  user_id TEXT NOT NULL, topic_id TEXT NOT NULL, PRIMARY KEY (user_id, topic_id)
);
CREATE TABLE IF NOT EXISTS drops (
  user_id TEXT NOT NULL, day TEXT NOT NULL, question_ids TEXT NOT NULL, sent_at TEXT,
  PRIMARY KEY (user_id, day)
);
CREATE TABLE IF NOT EXISTS bonus (
  user_id TEXT NOT NULL, day TEXT NOT NULL, question_id TEXT NOT NULL,
  PRIMARY KEY (user_id, day, question_id)
);
CREATE TABLE IF NOT EXISTS answers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL, question_id TEXT NOT NULL, day TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('drop','bonus')),
  level INTEGER NOT NULL, choice INTEGER NOT NULL, correct INTEGER NOT NULL,
  points INTEGER NOT NULL, answered_at TEXT NOT NULL,
  UNIQUE (user_id, question_id, day)
);
CREATE TABLE IF NOT EXISTS topic_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'researching', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS flags (
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, question_id TEXT NOT NULL,
  note TEXT, created_at TEXT NOT NULL
);
"""

USER_FIELDS = ("name", "phone", "email", "channel", "drop_size", "mix", "send_days", "send_time", "tz", "level_theme", "sms_opt_in")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(path or config.DB_PATH)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def create_user(con, topics: list[str], **fields) -> dict:
    uid, token = secrets.token_hex(8), secrets.token_urlsafe(24)
    data = {k: v for k, v in fields.items() if k in USER_FIELDS and v is not None}
    if "send_days" in data:
        data["send_days"] = json.dumps(data["send_days"])
    cols = ["id", "token", "created_at", *data]
    con.execute(f"INSERT INTO users ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                [uid, token, now(), *data.values()])
    set_topics(con, uid, topics)
    con.commit()
    return get_user(con, uid)


def update_user(con, uid: str, **fields) -> dict:
    data = {k: v for k, v in fields.items() if k in USER_FIELDS and v is not None}
    if "send_days" in data:
        data["send_days"] = json.dumps(data["send_days"])
    if data:
        con.execute(f"UPDATE users SET {', '.join(f'{k}=?' for k in data)} WHERE id=?", [*data.values(), uid])
        con.commit()
    return get_user(con, uid)


def _user(row) -> dict | None:
    if not row:
        return None
    u = dict(row)
    u["send_days"] = json.loads(u["send_days"])
    return u


def get_user(con, uid: str) -> dict | None:
    u = _user(con.execute("SELECT * FROM users WHERE id=?", [uid]).fetchone())
    if u:
        u["topics"] = [r[0] for r in con.execute("SELECT topic_id FROM user_topics WHERE user_id=? ORDER BY rowid", [uid])]
    return u


def user_by_token(con, token: str) -> dict | None:
    row = con.execute("SELECT id FROM users WHERE token=?", [token]).fetchone()
    return get_user(con, row[0]) if row else None


def all_users(con) -> list[dict]:
    return [get_user(con, r[0]) for r in con.execute("SELECT id FROM users")]


def set_topics(con, uid: str, topics: list[str]) -> None:
    con.execute("DELETE FROM user_topics WHERE user_id=?", [uid])
    con.executemany("INSERT OR IGNORE INTO user_topics VALUES (?,?)", [(uid, t) for t in topics])
    con.commit()
