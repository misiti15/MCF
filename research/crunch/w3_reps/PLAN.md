# W3-reps — Quality Reps Plan (crunch 11-18..11-20) — pre-registered plan

_Educational only — not financial advice. Research and proposals only: no config, runtime, assignment or ledger change; nothing merged that affects trading. Every move below needs an owner reply code._

Written 2026-11-18 21:45 UTC (16:45 ET), before any per-setup rate, skip share or shadow-vs-live number was computed. Only the journal schema and row counts were looked at.

## Questions

1. **Inventory.** For every setup enabled on 11-18 (`docs/live/assignments.json`, 10 accounts): live sessions present, signals per live session, submitted, fills (closed run-1 trades), skips by reason, traded sessions (≥ 1 closed trade), trades, avg R after costs, avg R w/o best day and best-day share.
2. **Resources.** Per account and session: peak concurrent open live lots vs `slots`, and share of signals skipped for account-resource reasons (slots, buying power, max positions, per-setup cap, halt, lot cap) vs setup-side reasons (spread, cost filter, ETB/borrow, through stop/target, timing).
3. **Never-trade / starved setups and why.** Zero-fill setups since their first live session; classify as DORMANT (≤ 1 signal per 10 sessions), BLOCKED (signals but ≥ 60% skipped; name the top reason), or NEW (< 3 live sessions).
4. **Shadow as a rep source.** Shadow run (kind `shadow`, from 11-17) vs live run 1 on the same setup/symbol/day: match of live fills by a shadow lot, extra shadow lots not blocked by resources, mean paired R difference (shadow − live) and its t. This is descriptive only; the weight shadow earns is set by the existing trust check (`mcf/research/shadow_calib.py`, research/shadow/SUMMARY.md targets: match ≥ 98%, extra ≤ 2%, |bias| ≤ 0.01R, never optimistic). Two sessions only, so no weight is claimed.
5. **Time to a verdict.** Per setup: expected live trades / session and traded-session rate from its recent record (last ≤ 10 live sessions in its current account), then sessions to 30 trades AND 15 active days (C3-ROT / C3-BAR2 minimums), with and without shadow reps (shadow counted only as a separate column, never toward the live minimum unless the owner says so).
6. **Allocation design.** Rule-based (no fitting to R): priority = high-potential AND low-rep. "High potential" is pre-defined as any of: on the consultant P2/P3 contender or low-rep-high-potential lists, avg R w/o best day > 0 with ≥ 10 trades, or a C3-WB5 queue tune. Moves are whole-session rotation only (owner playing-time rule): no in-session throttle in Primary/Testing.

## What is not done

- No scoring of setups for promotion (W2 owns that); R columns are context only (one-big-day rule).
- No new setup, filter, exit or tune; no 2-year data; locked block 2024-11-01..2025-02-28 not read in any form.
- L3-gap-slope-fromopen-FD untouched; nothing proposed for Primary's lineup (promotion hold is on).

## Configurations

Descriptive inventory: 0 tuned configurations. Shadow-vs-live comparison: 1 pre-registered comparison (fill profile B as recorded). Allocation: 1 rule (above), 1 variant (with / without the CWT14 + GEN rotation caps already approved as C3-ROT if the owner says yes). Bar for any t claimed: t ≥ max(1.5, sqrt(2 ln N)); with N = 3, bar = 1.50.

## Rule changes inside the window (ledger)

Sizing 10-28; Primary -2R latch 10-29; CF 0.15R cost filter in testing 10-29; ROLL1 11-05; TEAM-6 11-11; account restructure + LR3/LR8 11-12; ROT1 block 1 11-16..11-19; TSZ1 testing half-size + promotion hold + shadow mode 11-17; GY-BENCH + guests + quotes 11-18. Records span these regimes; rates are taken from each setup's current account where possible.
