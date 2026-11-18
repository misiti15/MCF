# W1-redteam — plan (crunch 2026-11-18 evening)

*Educational only — not financial advice.* Research only: no config, code, runtime or branch change; nothing merged.

Written after reading the 11-17/18 reports and before recomputing any figure from the journals.

**Scope.** Consultant Parts 2 and 3, usage items 4-11, LATCH review, L3 bespoke study and L3-AM, SRC-VALUE, replay
held-out calibration, Graveyard review 11-18, owner inbox 11-17/18 and docs/live/decisions.json.

**Checks (fixed in advance).**
1. Recompute a sample of headline figures from the live journals (run_id 1, all ten `mcf-data*` branches):
   the Primary journal (P9), the current six as traded and pooled (P1/P2), L3 Primary, C3-NS5 evidence, EXIT100
   persistence, GY-ARCHIVE-20 per-session numbers, L3 AM/PM, CWT14 share, GEN totals, ledger count.
2. Data mix-ups: the cost basis before vs after 11-12 (LR8), R vs dollars (the ~$4k position cap), equity changes
   (the 11-05 MTUM booking), sizing changes (10-28 Primary, 11-17 TSZ1).
3. Look-ahead and in-sample selection (books chosen on the same records they are judged on).
4. Contradictions between studies and between open decisions.
5. Conclusions that do not follow from their numbers.

**Configurations.** The audit selects nothing. The only scored grid is the EXIT100 base-rate check:
2 account sets × 3 R bases (after costs / raw / uniform LR8-style cost) × 2 active-day minimums × 2 keyings
(per account / pooled by setup) = **24**, all reported. Everything else is descriptive recomputation.

**Rules.** Costs in (R = pnl_adj / risk; raw R shown only to size the cost-basis effect). The locked block
2024-11-01..2025-02-28 is not read (the live journals start 2026-10-06). Every error gets a correction and its
effect on decisions already made and on the open C3 / U / GY codes.
