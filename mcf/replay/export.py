"""Dashboard data from replays (another page renders it): docs/live/replay.json and docs/live/pipeline.json.

replay.json   {"generated", "note", "system_agreement": {account: replay vs live on shared sessions}, "setups": {setup: {date, from, sessions, trades, win_rate, avg_r, t, total_r,
               account, fills, run}}} - the latest replay run of each setup (costs in, trade-through limits unless the
               run says otherwise). `t` is the day-clustered t of R (sessions are the clusters).
pipeline.json {setup: {stage: backtest|replay|live, backtest: {...}, replay: {...}, live: {...}, agreement: {...}}}
               stage: live when the setup is enabled in an account's config today, replay when it has replay results,
               else backtest. live = the paper journals (trades run 1) of the data branches; agreement = replay vs live
               on the sessions both cover (drift flagged when |avg R difference| > 0.25 R with >= 10 trades each).
Educational only - not financial advice."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ACCOUNTS = ("primary", "testing", "testing2", "graveyard", "gen")
DRIFT_R = 0.25
DRIFT_MIN_TRADES = 10


def setup_stats(t: pd.DataFrame, r_col: str = "r_multiple") -> dict:
    """trades, sessions, win rate, avg / total R and the day-clustered t (per-session R sums)."""
    if t is None or not len(t):
        return {"trades": 0, "sessions": 0, "win_rate": None, "avg_r": None, "t": None, "total_r": 0.0}
    r = t[r_col].astype(float)
    day = t["session"] if "session" in t else t["date"]
    per = r.groupby(day.astype(str)).sum()
    n = len(per)
    t_stat = None
    if n >= 2 and per.std(ddof=1) > 0:
        t_stat = float(per.mean() / (per.std(ddof=1) / math.sqrt(n)))
    return {"trades": int(len(r)), "sessions": int(day.nunique()), "win_rate": round(float((r > 0).mean()), 3),
            "avg_r": round(float(r.mean()), 3), "t": None if t_stat is None else round(t_stat, 2),
            "total_r": round(float(r.sum()), 2)}


def _runs(runs: Path) -> list[tuple[dict, Path]]:
    out = []
    for p in sorted(runs.glob("*/*-run.json")):
        meta = json.loads(p.read_text())
        acct = p.name[: -len("-run.json")]
        out.append((meta, p.parent / acct))
    return out


def replay_setups(runs: Path) -> dict:
    """setup -> stats of the newest run that traded it."""
    from .__main__ import load_run

    best: dict[str, dict] = {}
    for meta, acct_dir in _runs(runs):
        tr, _ = load_run(acct_dir)
        if not len(tr):
            continue
        mtime = (acct_dir.parent / f"{acct_dir.name}-run.json").stat().st_mtime
        for n, g in tr.groupby("strategy"):
            st = setup_stats(g)
            st.update(date=str(g.session.max()), **{"from": str(g.session.min())}, account=meta.get("account"),
                      fills=meta.get("fills"), limit_fill=meta.get("limit_fill"), run=meta.get("label"),
                      as_live=meta.get("as_live"), _mtime=mtime)
            if n not in best or (mtime, st["sessions"]) > (best[n]["_mtime"], best[n]["sessions"]):
                best[n] = st
    for v in best.values():
        v.pop("_mtime", None)
    return best


def live_trades() -> pd.DataFrame:
    """Paper trades (run 1) of every account's data branch, with the account."""
    import sqlite3
    import subprocess
    import tempfile

    from . import harness, store

    parts = []
    for acct in ACCOUNTS:
        br = harness.data_branch(acct)
        r = subprocess.run(["git", "-C", str(store.ROOT), "show", f"{br}:journal.db"], capture_output=True)
        if r.returncode or not r.stdout:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            f.write(r.stdout)
            f.flush()
            con = sqlite3.connect(f.name)
            t = pd.read_sql("SELECT symbol, strategy, side, date, entry_time, entry, exit, exit_reason, r_multiple "
                            "FROM trades WHERE run_id=1", con)
            con.close()
        parts.append(t.assign(account=acct))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def enabled_setups() -> dict[str, list[str]]:
    from . import harness

    out: dict[str, list[str]] = {}
    for acct in ACCOUNTS:
        try:
            cfg = harness.account_config(acct)
        except Exception:
            continue
        for n, v in (cfg.get("strategies") or {}).items():
            if (v or {}).get("enabled"):
                out.setdefault(n, []).append(acct)
    return out


def backtest_expectations() -> dict[str, float]:
    try:
        from ..report.scorecard import _expected

        return _expected()
    except Exception:
        return {}


def agreement(replay_tr: pd.DataFrame, live: pd.DataFrame) -> dict:
    """Replay vs live on the sessions both have: per setup and system-wide avg R, and a drift flag."""
    out = {}
    if not len(replay_tr) or not len(live):
        return out
    days = set(replay_tr.session.astype(str)) & set(live.date.astype(str))
    a = replay_tr[replay_tr.session.astype(str).isin(days)]
    b = live[live.date.astype(str).isin(days)]
    for n in sorted(set(a.strategy) | set(b.strategy)):
        x, y = a[a.strategy == n], b[b.strategy == n]
        out[n] = _agree(x, y, len(days))
    out["_system"] = _agree(a, b, len(days))
    return out


def _agree(x, y, days) -> dict:
    ra, rb = x.r_multiple.astype(float), y.r_multiple.astype(float)
    d = {"sessions": days, "replay_trades": int(len(ra)), "live_trades": int(len(rb)),
         "replay_avg_r": None if not len(ra) else round(float(ra.mean()), 3),
         "live_avg_r": None if not len(rb) else round(float(rb.mean()), 3)}
    d["drift"] = bool(len(ra) >= DRIFT_MIN_TRADES and len(rb) >= DRIFT_MIN_TRADES and
                      abs(d["replay_avg_r"] - d["live_avg_r"]) > DRIFT_R)
    return d


def export(runs: Path, out_dir: Path, live: pd.DataFrame | None = None, enabled: dict | None = None,
           expected: dict | None = None) -> list[Path]:
    from .__main__ import load_run

    gen = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rep = replay_setups(runs)
    live = live_trades() if live is None else live
    enabled = enabled_setups() if enabled is None else enabled
    expected = backtest_expectations() if expected is None else expected
    rtr = []
    for meta, acct_dir in _runs(runs):
        if meta.get("as_live") and not meta.get("setup"):
            tr, _ = load_run(acct_dir)
            if len(tr):
                rtr.append(tr.assign(account=meta.get("account")))
    rtr = pd.concat(rtr, ignore_index=True) if rtr else pd.DataFrame()
    agree: dict = {}
    if len(rtr) and len(live):
        for acct, g in rtr.groupby("account"):
            agree[acct] = agreement(g, live[live.account == acct])
    names = sorted(set(rep) | set(enabled) | (set(live.strategy) if len(live) else set()) | set(expected))
    pipe = {}
    for n in names:
        lv = live[live.strategy == n] if len(live) else live
        st_live = setup_stats(lv) if len(lv) else None
        if st_live:
            st_live["accounts"] = sorted(set(lv.account))
            st_live["from"], st_live["date"] = str(lv.date.min()), str(lv.date.max())
        stage = "live" if n in enabled else ("replay" if n in rep else "backtest")
        ag = {a: v[n] for a, v in agree.items() if n in v}
        pipe[n] = {"stage": stage, "accounts": enabled.get(n, []),
                   "backtest": None if n not in expected else {"expected_r": round(float(expected[n]), 3)},
                   "replay": rep.get(n), "live": st_live, "agreement": ag or None,
                   "drift": any(v.get("drift") for v in ag.values())}
    out_dir.mkdir(parents=True, exist_ok=True)
    p1, p2 = out_dir / "replay.json", out_dir / "pipeline.json"
    note = ("Replays of recorded sessions through the live runner (mcf/replay): production costs, trade-through limit "
            "fills, the lab universe. Replay results are not live results. Educational only - not financial advice.")
    sysag = {a: v.get("_system") for a, v in agree.items()}
    p1.write_text(json.dumps({"generated": gen, "note": note, "system_agreement": sysag, "setups": rep}, indent=1,
                             default=str))
    p2.write_text(json.dumps(pipe, indent=1, default=str))
    return [p1, p2]
