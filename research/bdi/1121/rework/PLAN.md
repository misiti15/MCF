Educational only — not financial advice.

# BD&I Saturday 2026-11-21: rule-18 rework round, pre-registration

Written 2026-11-21 ~15:56 UTC, **before any rework config was scored**. Research only: no config, setup, exit,
assignment or ledger change.

## Which failed ideas, and why these
Excluded: everything on research/final1121/REPORT.md "What failed: do not re-run" (cov-long, cap-etp, open-drive,
trio, etf-burst, promo-pipe) and the 11-19 give-back exit classes (research/giveback_1119). Among the remaining failed
backlog ideas, the two closest to the bar under the normal-way engine are the beginner batch's two NEAR misses
(research/beginner_1120/REPORT.md; backlog `beg-1120-batch-finding`, parked):

| idea | lineage tries so far | failure mode (from its RESULTS.md) | rework aimed at it |
|---|---|---|---|
| BEG-06 noise-area breakout, SPY/QQQ (best: `notrail`, NEAR, T1 combined w/o best day misses by 0.012R) | 4 | entries beat random sides before costs (69th-100th pct), but costs ~0.10R a trade at a 0.25 x ATR stop (~29 bp) eat the edge; trend-day setup that pays for chop | wider stop (cost per R falls), band and check-step neighbourhood, one-entry-a-day |
| BEG-04 quiet gap fade (best: `gap25`, NEAR, CHECK w/o best day misses by 0.018R) | 4 | the trigger is late (much of the fade already done when it fires); controls point to day selection, not the trigger | closer target (take the part of the fill that is left), wider stop, relaxed 1.2R test, filters removed one at a time |

Not chosen (and why): BEG-07 atr4 (NEAR on one reading but REALLY BAD on leg 2), BEG-09 stopx15 (CHECK −0.069),
guild-1109-cwt14skip (closed: half its skips sat in the earnings blackout), reddit-1110 grind continuation and
mh-1106 defensive rotation (both market-direction bets with w/o-best-day < 0; the first needs a structural-stop
harness not available in the normal-way engine).

## Engine (rule 31: existing engines only)
The beginner batch's own runners, which import bench10 ("normal way") unchanged: LR8 costs + 1.2 bp borrow, testing-arena
book (cap 100, <= 3 lots / symbol, price >= $5, ETB >= 0.9, 0.15R stop-cost filter), 1-minute signals and exits,
day-clustered t. Label: **E4-normal-way (bench10 book) on 1-minute bars**. Wrappers in this folder only set the
variants file and the scratch dir. BEG-04 needs its day table (rvol20 / rank) rebuilt with the BEG-02 build code
(the original scratch copy was deleted); T1 only. Windows: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..2026-11-04.
The locked block 2024-11-01..2025-02-28 is never read (bench10 filters + asserts). T2 not run tonight.

## Configs (one change or one pair each; all FIT-scored)
BEG-06 (base = the original beginner base; `notrail` = trail off):
- R6a stop_atr 0.375, notrail · R6b stop_atr 0.50, notrail · R6c stop_atr 0.375, trail on
- R6d band_mult 1.25, notrail · R6e band_mult 0.75, notrail · R6f step 60 (hourly checks), notrail
- R6g max_entries 1, notrail · R6h pair: stop_atr 0.375 + band_mult 1.25, notrail
BEG-04 (base = beginner base, gap 1.5-6%):
- R4a tgt_frac 0.5 · R4b tgt_frac 0.75 · R4c min_tgt_r 0.8 · R4d stop_mult 1.5 · R4e atr_cap 0.50
- R4f rvol/rank filter removed (rvol_max 99, rank_min 0) · R4g gap_lo 2.0 · R4h pair: tgt_frac 0.5 + stop_mult 1.5
**16 configs** (lineage N: BEG-06 4 + 8 = 12; BEG-04 4 + 8 = 12).

## Choice and scoring
- Per idea, the FIT pick = highest FIT avg R after costs among configs with >= 100 FIT trades whose one-step
  neighbour(s) in the same parameter (where one exists in the grid) are also above the idea's FIT base (plateau).
- CHECK is scored **once**, for the FIT pick only (CHECK has already been looked at twice per lineage: base + the
  beginner pick, so this is look 3 → rule 18 rising bar day-clustered t >= 2.0).
- **Pass (Testing proposal)**: CHECK avg R > 0, CHECK avg R w/o best day > 0, best-day share < 50%, CHECK day-clustered
  t >= max(2.0 rule-18 look-3 bar, 0.9 x sqrt(2 ln 12) = 2.0), FIT avg R > 0. **NEAR**: meets the top-10 standard
  (research/ultimate_1119/top10/PLAN.md Tier A on T1 legs) but not the pass. Otherwise FAIL.
- Reported for every config: FIT n, avg R, w/o best day, t; the pick's CHECK with best day, share, SPY up/flat/down.
