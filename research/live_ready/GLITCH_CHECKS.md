# Extra checks for the half-hourly :51 glitch check (LIVE-READY, owner 2026-11-11)

From research/live_ready/NOTES.md ("What the half-hourly :51 glitch check should also check"), alongside the :21
monitor. Per account, from that account's state-branch `status.json` (fields named below) and the broker (GET only).
Report a check only when it fails; never place, cancel or close an order from the check.

1. **Broker positions vs open journal lots.** Quantity per symbol; any non-MCF or untraded-today symbol.
   `health.position_mismatch` (LR5: kind `unknown_symbol` / `qty_mismatch` / `corporate_action` / `side_mismatch` /
   `missing`) and `health.position_check.blocked` (symbols with new entries blocked). Closing a mismatch stays the
   owner's decision.
2. **Unprotected lots.** Any open MCF position with no working stop leg, and any `-u` (unprotected close) order today.
3. **Stuck orders.** Orders in new / accepted / pending for more than 2 minutes; entries that never filled.
4. **Health flags.** `health.flatten_failed`, `health.flatten_retry`, `health.outage_actions`, `health.data_stale`,
   `health.partial_lots`, `health.alerts` (LR5 / LR7 alerts: position_mismatch, flatten_failed, kill_switch,
   after_close_exposure).
5. **Loss stops.** Realized + open marked R vs the −20R halt, and per setup vs −2R. Is the latch state consistent with
   the journal? `health.risk_state` (`realized_r`, `open_r`, `r_basis`, `halt_counts_open`, `halted`,
   `setup_stopped`). From 2026-11-12 Primary counts R after costs and open marks (LR3).
6. **Run alive.** `status.json` age under 5 minutes, and the job / hand-over successor is queued.
7. **Rejected orders.** Count and reasons since the last check (buying power, duplicate id, asset not tradable).
8. **Equity jump vs MTM.** Equity change that the marked positions do not explain (a corporate-action / phantom tell,
   like MTUM's ~$11.6k phantom swing in the 11-06 running total).
9. **Calendar.** Early-close / holiday flag for today and the flatten time in use: `health.session_close`,
   `health.flatten_at`, `health.early_close` (LR1; 2026-11-27 and 2026-12-24 close at 13:00, flatten 12:55).
10. **Buying power.** Headroom (daytrading buying power − open notional) and the PDT flag / day-trade count (real
    money).

Also: `health.kill` set means the kill switch is on for that account (LR4); report it once, it is intentional.

Educational only — not financial advice.
