# Friday 11-27 switches (pre-built, all OFF) — Educational only — not financial advice
Code: `mcf/execution/safety.py`, `risk.py`, `runner.py`; config block `risk:` in `config/default.yaml`. None of them
flattens: each blocks NEW entries only (B8 only logs). Each applies only in its `accounts:` list (default `[primary]`).
Flip only after the 13:00 ET close, on the owner's yes; skeptic review; `docs/live/assignments.json` is untouched.
State after the flip: status.json `health.risk_state.safety`. LATCH-OPEN / HS-SCALE / SHOCK-V add realized + open R, so they
run only in `account.loss_stops_cost_r_accounts` (Primary); elsewhere they stay off with a warning (`safety.refused`).
Skip reasons: `setup daily loss limit (open)`, `scaled loss limit`, `shock-v failsafe` (restored after a restart).

| Decision | Exact config change (`config/default.yaml`, `risk:`) |
|---|---|
| LATCH-OPEN friday | `latch_counts_open: true` (threshold = `account.max_setup_daily_loss_r`, 2R). ('now' was withdrawn: no mid-week Primary latch change) |
| LATCH-OPEN -3R | also `latch_open_r: 3` (closed latch stays 2R; for strict G1-3 also `account.max_setup_daily_loss_r: 3`) |
| HS-SCALE shock-only | `shock_v.enabled: true` + `shock_v.v1_floor_r: 16` + `shock_v.v2_floor_r: 24`. `scaled_halt` stays OFF (do NOT use the old 'yes' row: it would also turn the scaled halt on). Without the floor change SHOCK-V runs on its unscored bare 8R / 12R floors (X is passed only when the scaled halt is on) |
| HS-SCALE build-flatten | no config change: build the K4 flatten + MISMATCH-$ + LR10 order-size guards with tests for a later epoch; nothing switched on |
| HS-SCALE no | no change |
| (retired) HS-SCALE yes | was `scaled_halt.enabled` + `shock_v.enabled`; no longer a card option (inspector 1127 #1) |
| L3-OUT out | not a `risk:` key: `strategies.L3-gap-slope-fromopen-FD.enabled` false in Primary, enabled in On Deck (the `testing` account, as for ST7-MOVE; a move, never a copy), `live.setup_order` both accounts, `python -m mcf.report.assignments`, ledger `kind: move` naming the owner's override of PRIME-RULES probation |
| L3-OUT probation | no config change: stays in Primary on probation; ledger note only (re-decided at 20 Primary sessions or at -10R) |
| L3-OUT no | no change |
| B8 shadow | `netbeta_shadow.enabled: true` (+ `betas_path:` a JSON of shrunk betas; none = beta 1.0) |
| B8 enforce | NOT built (shadow only); needs its own change |

Ledger entry template (`research/ledger.jsonl`, one line; then `python -m mcf.research.ledger check`):
```
{"id": "2026-11-27-<code>", "date": "2026-11-27", "effective": "2026-11-30", "kind": "risk", "code": "<LATCH-OPEN|HS-SCALE|B8-SHADOW>",
 "title": "<one line>", "approved_by": "owner 2026-11-2x (<where>)", "owner_approval": "<same>",
 "patch": {"risk.latch_counts_open": [false, true]}, "evidence": ["research/neveragain_1125/REPORT.md"],
 "metrics_at_approval": {"...": "..."}, "note": "blocks entries only, never flattens", "rule_change_context": "<ledger dates in window>"}
```
Patch keys per decision: `risk.latch_counts_open` (+ `risk.latch_open_r`); HS-SCALE shock-only: `risk.shock_v.enabled`,
`risk.shock_v.v1_floor_r` [8, 16], `risk.shock_v.v2_floor_r` [12, 24] (`risk.scaled_halt.*` unchanged); `risk.netbeta_shadow.enabled`. Evidence: neveragain_1125,
hsscale_1125 (+ s8cap_1125), squeeze_1125.

Tests to run after the flip: `pytest -q tests/test_friday_switches.py tests/test_twin_and_setup_loss.py
tests/test_restart_restore.py tests/test_burst_brake.py`, then the full `pytest -q`. The default-off test
(`test_every_switch_defaults_off_in_every_account`) is meant to fail once a switch is on: change its expectation for the
flipped account in the same commit.

Assumptions (read before flipping): HS-SCALE here blocks entries only (the report's K4 also flattens at -X; not built);
with X >= 20R it never fires before the fixed -20R halt, which stays. sigma comes from research (std of simulated daily
closed R, trailing 250 sessions, min 120, refreshed Fridays); N = setups trading live. SHOCK-V uses X when HS-SCALE is
on, else its floors (8R / 12R as shipped; 16R / 24R under 'shock-only' = the scored thresholds at N = 4, X = 32R, not
re-scored as a fixed value: Primary's 13 snapshot days pass it once, 11-06); stale polls / failed marks skip a sample. LATCH-OPEN: a setup with an unmarked lot, or a
failed marking pass, counts closed R only (logged). A latch / halt that fires with no later signal is not journaled, so
a restart re-derives it from the marks.
