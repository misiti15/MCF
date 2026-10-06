"""One trading session split into CI-sized slots, plus pre-market prep and state publishing.

GitHub-hosted jobs run at most 6 hours, so each job trades until the earlier of the close or
`max_job_minutes` after it started, then hands over. Jobs share one concurrency group (never overlap)
and hourly standby triggers keep one queued, so the next job picks up as soon as the previous one ends
— including after a crash or a skipped trigger. Positions keep broker-side stops across handovers;
state is rebuilt from the journal and the broker on every start.

State lives in a checkout of the `mcf-data` branch (`--state-dir`): journal.db, status.json and the
daily universe. The runner pushes status.json every few minutes so the dashboard is near-live.
"""

from __future__ import annotations

import pickle
import subprocess
from pathlib import Path

import pandas as pd

from ..strategies.base import t

NY = "America/New_York"


def job_deadline(now: pd.Timestamp, live: dict) -> pd.Timestamp | None:
    """When a job started at `now` (ET) must hand over, or None if it should not run at all."""
    if now.weekday() >= 5 or not (t(live.get("start_from", "08:00")) <= now.time() < t("15:50")):
        return None
    return now + pd.Timedelta(minutes=live.get("max_job_minutes", 340))


SETUP_KEYS = ("strategies", "exits", "shorts", "live", "universe")


def freeze_setups(cfg: dict, state_dir: str | Path, now: pd.Timestamp) -> str:
    """Owner rule (2026-10-06): setups change only outside market hours. The first job of a session
    snapshots the setup-defining config to state/setups/<date>.json; every later job that day trades
    that snapshot, so an edit merged during market hours waits for the next session."""
    import json

    d = Path(state_dir) / "setups"
    d.mkdir(parents=True, exist_ok=True)
    snap = d / f"{now.date()}.json"
    if snap.exists():
        frozen = json.loads(snap.read_text())
        changed = [k for k in SETUP_KEYS if cfg.get(k) != frozen.get(k)]
        cfg.update({k: frozen[k] for k in SETUP_KEYS if k in frozen})
        return (f"setups frozen for {now.date()} (snapshot {snap.name})"
                + (f"; ignoring intraday edits to: {', '.join(changed)}" if changed else ""))
    snap.write_text(json.dumps({k: cfg.get(k) for k in SETUP_KEYS}, indent=1, default=str))
    return f"setups snapshot written for {now.date()} ({len([s for s in cfg['strategies'].values() if s.get('enabled')])} enabled)"


def priors_path(state_dir: str | Path, day) -> Path:
    return Path(state_dir) / "cache" / f"priors-{day}.pkl"


def prep(cfg: dict, state_dir: str | Path, day, log=print) -> dict:
    """Build today's universe and priors once (the afternoon job reuses them via the CI cache)."""
    from ..data.priors import build_priors
    from ..data.universe import build_universe

    p = priors_path(state_dir, day)
    if p.exists():
        log(f"prep: reusing {p}")
        return pickle.loads(p.read_bytes())
    p.parent.mkdir(parents=True, exist_ok=True)
    uni = build_universe(cfg, str(Path(state_dir) / "universe.csv"))
    log(f"prep: universe {len(uni)} symbols {uni.tier.value_counts().to_dict()}")
    exact = sorted({s for st in cfg["strategies"].values() if st.get("enabled") for s in st.get("symbols", [])})
    pri = build_priors(uni.symbol.tolist(), day, feed=cfg["data"]["feed"], exact_symbols=exact, log=log)
    p.write_bytes(pickle.dumps(pri))
    return pri


class Publisher:
    """Commit + push files in the state checkout. Failures are logged, never fatal."""

    def __init__(self, state_dir: str | Path, enabled: bool = True):
        self.dir = Path(state_dir)
        self.enabled = enabled and (self.dir / ".git").exists()

    def _git(self, *args) -> bool:
        r = subprocess.run(["git", "-C", str(self.dir), *args], capture_output=True, text=True)
        if r.returncode:
            print(f"git {' '.join(args[:2])} failed: {r.stderr.strip()[:200]}")
        return r.returncode == 0

    def push(self, paths: list[str], message: str):
        if not self.enabled:
            return
        self._git("add", *paths)
        if subprocess.run(["git", "-C", str(self.dir), "diff", "--cached", "--quiet"]).returncode == 0:
            return
        self._git("-c", "user.name=mcf-bot", "-c", "user.email=mcf-bot@users.noreply.github.com",
                  "commit", "-q", "-m", message)
        branch = subprocess.run(["git", "-C", str(self.dir), "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True).stdout.strip() or "mcf-data"
        for _ in range(3):
            if self._git("push", "-q", "origin", f"HEAD:{branch}"):
                return
            self._git("pull", "-q", "--rebase", "origin", branch)
