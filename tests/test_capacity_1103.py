"""capacity1103: workflow load reducers (research/ops/capacity1103/NOTES.md). Educational only — not financial advice."""
from pathlib import Path

import yaml

WF = Path(__file__).resolve().parents[1] / ".github" / "workflows"
EOD_IF = "github.event_name != 'workflow_run' || github.event.workflow_run.conclusion != 'cancelled'"


def test_eod_skips_cancelled_trade_runs_without_a_runner():
    # a job-level `if` that is false skips the job before a runner is assigned; the closing run (success or failure),
    # workflow_dispatch and the 16:25 backup cron always pass it
    job = yaml.safe_load((WF / "eod.yml").read_text())["jobs"]["report"]
    assert job["if"] == EOD_IF


def test_research_matrices_leave_room_for_trading_jobs():
    # GitHub Free = 20 concurrent jobs per account; a research matrix must never take them all during a session
    for p in WF.glob("*.yml"):
        if p.name in ("trade.yml", "watchdog.yml", "eod.yml"):   # per-account matrices (one job per account)
            continue
        for name, job in (yaml.safe_load(p.read_text()).get("jobs") or {}).items():
            strat = job.get("strategy") or {}
            if "matrix" in strat:
                assert int(strat.get("max-parallel", 99)) <= 4, f"{p.name}:{name}"


def test_trade_job_caps_the_cache_download_timeout():
    env = yaml.safe_load((WF / "trade.yml").read_text())["jobs"]["session"]["env"]
    assert env["SEGMENT_DOWNLOAD_TIMEOUT_MINS"] == "1"
