"""QA-1121 M2: trade jobs start watchdog.yml every ~10 min in market hours. Educational only - not financial advice."""
import pandas as pd

from mcf.execution import handover as ho
from tests.test_live_ready_lr import ROOT


def _t(s):
    return pd.Timestamp(s, tz="America/New_York")


def test_dispatch_when_no_recent_watchdog_run():
    assert ho.decide_watchdog(_t("2026-11-23 10:00"), True, [], 0)["action"] == "dispatch"


def test_no_dispatch_when_active_recent_closed_or_capped():
    now = _t("2026-11-23 10:00")
    assert ho.decide_watchdog(now, True, [{"status": "queued", "created_at": "2026-11-23T14:59:00Z"}], 0)["action"] == "none"
    recent = [{"status": "completed", "created_at": "2026-11-23T14:55:00Z"}]          # 09:55 ET, 5 min ago
    assert ho.decide_watchdog(now, True, recent, 0)["action"] == "none"
    old = [{"status": "completed", "created_at": "2026-11-23T14:45:00Z"}]             # 15 min ago
    assert ho.decide_watchdog(now, True, old, 0)["action"] == "dispatch"
    assert ho.decide_watchdog(now, True, old, ho.WATCHDOG_MAX_DISPATCHES)["action"] == "capped"
    assert ho.decide_watchdog(now, False, [], 0)["action"] == "none"                     # holiday
    assert ho.decide_watchdog(_t("2026-11-23 09:20"), True, [], 0)["action"] == "none"
    assert ho.decide_watchdog(_t("2026-11-23 16:10"), True, [], 0)["action"] == "none"
    assert ho.decide_watchdog(_t("2026-11-21 10:00"), True, [], 0)["action"] == "none"   # Saturday


def test_trade_job_launches_the_watchdog_helper():
    wf = (ROOT / ".github/workflows/trade.yml").read_text()
    assert "mcf.execution.handover watchdog" in wf
