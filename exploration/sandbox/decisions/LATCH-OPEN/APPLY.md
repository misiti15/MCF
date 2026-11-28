# LATCH-OPEN - how it would be applied (DRAFT; nothing here is applied)
Educational only - not financial advice.

Both options make the identical code/config change; only the date differs.

| Step | Monday 11-30 (override) | 12-04 Friday epoch |
|---|---|---|
| When | Sat 11-28 / Sun 11-29, outside market hours, after the owner's reply | Fri 12-04 after the 16:00 close |
| Config | `config.diff` (risk.latch_counts_open: true) | same |
| Ledger | `ledger_monday_1130.jsonl` (effective 2026-11-30) | `ledger_epoch_1204.jsonl` (effective 2026-12-07) |
| Tests | `pytest -q tests/test_friday_switches.py tests/test_twin_and_setup_loss.py tests/test_restart_restore.py tests/test_burst_brake.py`, then full `pytest -q`; update `test_every_switch_defaults_off_in_every_account` for primary in the same commit | same |
| Checks | `python -m mcf.research.ledger check`; decisions.json card LATCH-OPEN -> answered | same |
| First-day check | status.json `health.risk_state.safety.latch_counts_open.enabled == true`; skip reason `setup daily loss limit (open)` appears only on latch days | same, 12-07 |
| Rollback | set back to false after a close (one-line revert + ledger entry) | same |

Variant '-3R': also `latch_open_r: 3` (closed latch stays 2R). Not re-scored on the full 11-25 day.
