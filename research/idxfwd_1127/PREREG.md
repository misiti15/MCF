# IDXFWD-1127 — forward shadow of the two index open-dip leads, pre-registration

*Educational only — not financial advice.* Research only (journal-only script, not runner code): no change to config/,
setups, exits, assignments.json, decisions.json or the ledger.

Committed before any forward day is scored. The frozen rules, costs, pass bar, harm stop and time cap are in
`research/forward/idx_dip/RULE.md` (this commit) — that file is the pre-registration.

- Rules: IDX6 (QQQ >= 1.5% by 09:55 -> TQQQ, B 0.20, 1R trail) and IWM45 (IWM >= 0.75% by 09:45 -> TNA, B 0.20, 1R
  trail), copied exactly from research/idxdip_1127 (`shadow.py --verify` reproduces the study's FIT and CHECK trades).
- Forward window: 2026-11-05 (first session after the CHECK end) onward; 2026-11-05..11-27 backfilled at freeze.
  The locked block 2024-11-01..2025-02-28 is never read (asserted in `shadow.py`).
- Configurations: **2** (frozen copies, no new search). Cumulative program N ~9,300 -> ~9,302.
- Pass bar (one test, one book): >= 15 signal days; LIVE-L avg R > 0 with day-clustered t >= 2.0; best-day share
  < 50% and avg R w/o best day > 0; S12 (+1 min, +2 bp) avg R > 0. LR8 reported alongside. Harm stop from 8 signal
  days: cumulative <= -6R or avg <= -0.40R. Time cap 2028-06-30 (then INCONCLUSIVE).
- Control: at scoring, a size-matched random-day control (same rule clock, same stop %, other forward sessions, 500 draws)
