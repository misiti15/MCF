Educational only — not financial advice

# ex30 / accounts — plan (written before any change, 2026-11-03)

Housekeeping only: wiring for three new paper accounts. No setup, exit or risk rule of an existing account changes,
and no setup is enabled in the new accounts (each setup added later is a setup move: assignments regenerated, ledger
entry, merged outside 09:30-16:00 ET). No bar history is read, so the locked block 2024-11-01..2025-02-28 is not touched.

Accounts (keys optional; every job skips the account until the owner adds both secrets):

| key | label | orders | state branch | secrets |
|---|---|---|---|---|
| livelab | Live Lab | mll- | mcf-data-livelab | ALPACA_LIVELAB_API_KEY / ALPACA_LIVELAB_SECRET_KEY |
| explore1 | Explore 1 | mx1- | mcf-data-explore1 | ALPACA_EXPLORE1_API_KEY / ALPACA_EXPLORE1_SECRET_KEY |
| explore2 | Explore 2 | mx2- | mcf-data-explore2 | ALPACA_EXPLORE2_API_KEY / ALPACA_EXPLORE2_SECRET_KEY |

Overlay (from research/bdi/night1102/livelab NOTES "Exact pieces needed", item 1): strategies_exclusive; 200 slots,
buying_power_multiple 2.0 (~$1,000 lot at $100k), max_positions_per_strategy 10, per-setup daily stop off, account
daily stop 120R as Testing, max_stop_cost_r 0.15 as Testing, no twin block, no live scale-out, no setups.

Pieces: trade / watchdog / eod matrix rows and env mappings, session-guard, longhold key separation, outage prefixes,
assignments, daily post, playing time, replay export / harness / spreads, generator overlap check, dashboard
(index.html, report.html). Tests: tests/test_new_accounts_1103.py. Then the full pytest and a capacity check.
