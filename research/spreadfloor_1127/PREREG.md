Educational only — not financial advice

# SPREADFLOOR-1127 — pre-registration (build: log-only shadow logger; no scoring tonight)

Committed before any score. Tonight nothing is scored: this task builds a recorder. This file fixes now how the
evidence it collects will be judged later, so the later test cannot be tuned to the data.

## Why
stopfloor_1127 lead 1: live trades whose stop distance is under 6 / 8 quoted spreads lose more (−0.31 / −0.29 R vs
−0.18 / −0.17 kept) and a 6/8-spread skip beat 500 same-share random skips live (31 sessions, 10-14..11-25). It cannot
be backtested (no spread history). Only forward evidence can settle it.

## What is built (housekeeping, log only)
- `mcf/execution/spreadfloor.py` (pure) + `PaperRunner._spreadfloor_tag` in `mcf/execution/runner.py`.
- At each real entry (after every gate and after sizing, next to the B8 netbeta tag) the journaled signal info and the
  order meta get `spreadfloor_shadow` = {quote, spread_c, spread_bps, stop_c, stop_bps, stop_spreads, would_skip_6,
  would_skip_8}, from the decision-time quote `_realism` already fetched (no extra API call).
- Never changes orders, sizing, entries, exits or skips; nothing reads the fields; any exception is swallowed and
  printed. Kill switch `live.spreadfloor_log: false` (default on; config/ untouched).
- Report: `python -m mcf.report.spreadfloor <journal.db ...> [--json out]`.

## Future evaluation (fixed now; run once ≥ 20 sessions are logged, and again at 40)
- Unit: live lots tagged with a quote, all accounts except Graveyard; R after realized costs (pnl_adj basis; LIVE-L
  and LR8 alongside in the research run).
- Configs: exactly 2 (F6, F8: skip when stop_spreads < 6 / < 8). Cumulative N ≈ 9,176 before this wave → +2.
- Pass bars (both needed for "lead → candidate"; a candidate then goes to the backlog, not live):
  1. skipped lots' mean R < kept lots' mean R, day-clustered t ≤ −2.5 on the skipped-minus-kept difference
     (2 configs; the lineage bar t ≥ ~4.3 is shown for reference);
  2. the skip beats ≥ 95% of 500 same-share random skips within setup (book R/day without the skipped lots);
  3. ≥ 60% of setup families with ≥ 5 skipped lots improve; per-setup table reported (better / worse and by how much);
  4. best-day share of the gain < 35%, and gain still positive without the best day;
  5. playing-time cost reported (share of lots skipped per setup) — the owner's playing-time rule weighs against
     any skip; a widen-and-resize variant is the fallback to test if the skip passes but starves setups.
- Rule changes inside the window (research/ledger.jsonl) listed alongside the numbers.
- Locked block 2024-11-01..2025-02-28 is not involved (live data only, from 2026-11-30 on).
