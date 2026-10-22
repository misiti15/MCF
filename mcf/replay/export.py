"""Dashboard data from replays (another page renders it): docs/live/replay.json and docs/live/pipeline.json.

replay.json   {"generated": "YYYY-MM-DD HH:MM ET", "window", "note", "setups": {setup: {trades, sessions, win_rate, avg_r, t,
               total_r, date}}, "meta": {setup: {from, account, fills, run, ...}}, "system_agreement": {...}}
               - per setup the research-rule run with the most sessions (costs in, trade-through limits unless the
               run says otherwise). `t` is the day-clustered t of R (sessions are the clusters).
pipeline.json {"generated", "setups": {setup: {stage: backtest|replay|live, backtest|replay|live: {trades, win, be_win,
               avg_r, t} | null, accounts, agreement, drift}}} - the dashboard schema (tests/test_replay_pipeline_stubs)
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
            # the research-rule run (costs, trade-through) with the most sessions, then the newest
            st["_rank"] = (meta.get("fills") == "costs" and meta.get("limit_fill") == "through", st["sessions"], mtime)
            if n not in best or st["_rank"] > best[n]["_rank"]:
                best[n] = st
    for v in best.values():
        v.pop("_mtime", None)
        v.pop("_rank", None)
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


def agreement(replay_tr: pd.DataFrame, live: pd.DataFrame, universe: set | None = None) -> dict:
    """Replay vs live on the sessions both have: per setup and system-wide avg R, and a drift flag."""
    out = {}
    if not len(replay_tr) or not len(live):
        return out
    days = set(replay_tr.session.astype(str)) & set(live.date.astype(str))
    a = replay_tr[replay_tr.session.astype(str).isin(days)]
    b = live[live.date.astype(str).isin(days)]
    if universe is not None and "symbol" in b:
        b = b[b.symbol.isin(universe)]           # only what the replay can see (its universe)
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


def _universe() -> set | None:
    try:
        from . import store

        return set(store.symbols())
    except Exception:
        return None


REPLAY_KEYS = ("trades", "sessions", "win_rate", "avg_r", "t", "total_r", "date")
STAGE_KEYS = ("trades", "win", "be_win", "avg_r", "t")


def stage_stats(t: pd.DataFrame | None, r_col: str = "r_multiple") -> dict | None:
    """The dashboard's stage block {trades, win, be_win, avg_r, t}: be_win = the win rate at which this payoff
    (average win vs average loss) breaks even, |avg loss| / (avg win + |avg loss|)."""
    if t is None or not len(t):
        return None
    st = setup_stats(t, r_col)
    r = t[r_col].astype(float)
    w, lo = r[r > 0], r[r <= 0]
    be = None
    if len(w) and len(lo) and (w.mean() - lo.mean()) > 0:
        be = round(float(-lo.mean() / (w.mean() - lo.mean())), 3)
    return {"trades": st["trades"], "win": st["win_rate"], "be_win": be, "avg_r": st["avg_r"], "t": st["t"]}


def export(runs: Path, out_dir: Path, live: pd.DataFrame | None = None, enabled: dict | None = None,
           expected: dict | None = None, universe: set | None = None) -> list[Path]:
    """Write docs/live/replay.json and docs/live/pipeline.json in the dashboard's schema
    (tests/test_replay_pipeline_stubs.py); run details sit beside it (replay.json `meta`, pipeline setup keys)."""
    from .__main__ import load_run

    now = pd.Timestamp.now(tz="America/New_York")
    gen = f"{now:%Y-%m-%d %H:%M} ET"
    rep = replay_setups(runs)
    live = live_trades() if live is None else live
    enabled = enabled_setups() if enabled is None else enabled
    expected = backtest_expectations() if expected is None else expected
    rtr = []
    live_runs = [(m, d) for m, d in _runs(runs) if m.get("as_live") and not m.get("setup")]
    for acct in sorted({m.get("account") for m, _ in live_runs}):
        mine = [(m, d) for m, d in live_runs if m.get("account") == acct]
        # replay vs live like for like: the paper-fill replay of the sessions as they were configured, if there is one
        m, d = sorted(mine, key=lambda x: (x[0].get("fills") == "paper", x[1].stat().st_mtime))[-1]
        tr, _ = load_run(d)
        if len(tr):
            rtr.append(tr.assign(account=acct))
    rtr = pd.concat(rtr, ignore_index=True) if rtr else pd.DataFrame()
    agree: dict = {}
    if len(rtr) and len(live):
        for acct, g in rtr.groupby("account"):
            agree[acct] = agreement(g, live[live.account == acct], universe if universe is not None else _universe())
    # replay trades per setup (the run rep[n] came from), for the pipeline's stage block
    by_run: dict = {}
    for meta, acct_dir in _runs(runs):
        by_run[(meta.get("label"), meta.get("account"))] = acct_dir
    names = sorted(set(rep) | set(enabled) | (set(live.strategy) if len(live) else set()) | set(expected))
    pipe = {}
    for n in names:
        lv = live[live.strategy == n] if len(live) else live
        stage = "live" if n in enabled else ("replay" if n in rep else "backtest")
        ag = {a: v[n] for a, v in agree.items() if n in v}
        rp = None
        if n in rep:
            tr, _ = load_run(by_run[(rep[n]["run"], rep[n]["account"])])
            rp = stage_stats(tr[tr.strategy == n])
        pipe[n] = {"stage": stage, "accounts": enabled.get(n, []),
                   "backtest": None if n not in expected else
                   {"trades": None, "win": None, "be_win": None, "avg_r": round(float(expected[n]), 3), "t": None},
                   "replay": rp, "live": stage_stats(lv) if len(lv) else None,
                   "agreement": ag or None, "drift": any(v.get("drift") for v in ag.values())}
    out_dir.mkdir(parents=True, exist_ok=True)
    p1, p2 = out_dir / "replay.json", out_dir / "pipeline.json"
    note = ("Replays of recorded sessions through the live runner (mcf/replay): production costs, trade-through limit "
            "fills, the lab universe. Replay results are not live results. Educational only - not financial advice.")
    sysag = {a: v.get("_system") for a, v in agree.items()}
    froms = [v["from"] for v in rep.values()]
    tos = [v["date"] for v in rep.values()]
    out = {"generated": gen, "window": f"{min(froms)} to {max(tos)}" if rep else None, "note": note,
           "setups": {n: {k: v.get(k) for k in REPLAY_KEYS} for n, v in rep.items()},
           "meta": {n: {k: v.get(k) for k in ("from", "account", "fills", "limit_fill", "run", "as_live")}
                    for n, v in rep.items()},
           "system_agreement": sysag}
    p1.write_text(json.dumps(out, indent=1, default=str))
    p2.write_text(json.dumps({"generated": gen, "note": "backtest -> replay (~50 sessions) -> testing account -> "
                              "primary; replay vs live agreement per setup and system-wide (drift when |avg R gap| > "
                              f"{DRIFT_R} R with >= {DRIFT_MIN_TRADES} trades each). Educational only - not financial "
                              "advice.", "system_agreement": sysag, "setups": pipe}, indent=1, default=str))
    return [p1, p2]
