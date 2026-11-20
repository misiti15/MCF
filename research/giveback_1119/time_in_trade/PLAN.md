# Time-in-trade exits per family (giveback_1119/time_in_trade) — pre-registered plan

*Educational only — not financial advice.* Written 2026-11-20 before any rule was scored. Nothing here changes a live
setting; a passing class would go to `research/backlog.jsonl` and ship only outside 09:30-16:00 ET.

## Data and protocol (WB2)
- Paired on the parent's own signals: the map's lab paths (`gb_tmp/lab_paths.parquet`, first signal per
  (setup, symbol, day) of bt_lab1104, BEREPLAY walk, bt_all costs, locked block 2024-11-01..2025-02-28 absent and
  re-asserted here). Unit = stop distance. For each trade still open at checkpoint T, the map stores the mark, MFE so
  far and `rem_T` = final net R − net R of a market exit at the minute-T close, where the exit carries bt_all exit cost
  **plus 0.01/share extra**. A rule that fires changes the trade by `delta = −rem_T`; trades it does not fire on are
  unchanged (delta 0). Exit at the bar close is slightly optimistic in execution; the extra 0.01/share is the allowance.
- Fit = sessions ≤ 2025-09-30 (170), check = later (276). Mechanism family = setup prefix (GEN pooled), split by side:
  36 family-sides.
- Checkpoints available: T ∈ {15, 30, 45, 60, 90, 120} (5 and 10 excluded: setups must be given room to breathe).

## Exit classes (grid per family-side)
- **A "never worked"**: exit at T if MFE_T < m and mark_T < r; m ∈ {0.25, 0.5}, r ∈ {−0.25, 0, +0.25}. 36 configs.
- **B "worked, then faded"**: exit at T if MFE_T ≥ m and mark_T ≤ r; m ∈ {0.5, 0.8, 1.0}, r ∈ {0, +0.25}. 36 configs.
- 72 configs x 36 family-sides = 2,592; plus one book-wide secondary per class (same grid, one config for all
  families, chosen on fit) = 72. **N (this class) = 2,664.** Lineage: the map scored 916 descriptive cells and 0 exit
  configs; counting those too gives N = 3,580. Threshold = max(1.5, sqrt(2 ln N)) = 3.97 (N = 2,664) / 4.05 (N = 3,580);
  sibling classes of this investigation add to N, and the bar moves by < 0.3 even at 10x N. I use 4.05 and also show
  sqrt(2 ln 10N).

## Fit-half selection (per family-side, fixed before the check half is read)
Pick the single config (of 72) with the largest fit total delta. Adopt it only if: fit avg delta > 0, fit day-clustered
t ≥ 2.0, fit delta without its best day > 0, and it fires on ≥ 100 fit trades. Otherwise the family keeps no rule
(delta 0). At most one rule per family-side.

## Check half (scored once)
Book = all lab trades in the check half; delta from adopted rules only. Report: total and avg R before/after, paired
day-clustered t of the per-trade delta (book), avg R without best day before/after, best-day share of the improvement,
per family-side and per setup better/worse counts with sizes (total R and avg R change), and the secondary book-wide
rules. Live (run 1, 10-06..11-19, de-duplicated as in the map, live R units, cost = live exit cost model of the map):
the same adopted rules applied descriptively, per family; rule changes inside the window listed (see map RESULTS).

## Pass rule (pre-registered, from the task)
On the check half: total R and avg R improve after costs; avg R without best day not worse; improvement not carried by
one day (best-day share of the improvement < 50%); more families and more setups better than worse; and the paired
improvement's day-clustered t ≥ max(1.5, sqrt(2 ln N)) = 4.05. All must hold.
