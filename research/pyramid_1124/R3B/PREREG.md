# PYRAMID round 3 — Team B "the team, not the soldier" — pre-registration (written before any book is scored)
Educational only — not financial advice. Research only; no config/ledger/account change.

## Question
Does a 5-setup BOOK (≈3 longs + 2 shorts) clearly beat the current top-10 book out of sample?

## Candidate pool
LAB (bench10 trade paths, unchanged pipelines; entries >= 09:50, flat 15:55, 1-min exits):
 Shorts: L3-gap-slope-fromopen-FD, L3-gap-slope-lowdist-FD, L3-gap-slope-rsi5hi-FD, RW3-gapdn-rsi5pop-flowsell-short-FD,
   RW5-heat30-flowsell-rsi5pop-gapdn-short-FD, CWT09-gapdn-vwaploss-g10-short, RW6-ns2-up3-short-FD,
   NM-RWN4-ns2-spyup05-notfri-short, GEN-261029-06 (Late Quiet-Day Short), GEN-261023-06 (Late-AM Pop Fade).
 Longs (each MUST carry one market gate, chosen on FIT from {TT1 (Team G def.), SPYOPEN = SPY last 1-min close before the
   decision bar >= SPY 09:30 open}): NM-ETF-late-dip-di-long, CWT14-failbrk-orl-p10-long-WB5, B3 TREND-CLOSE-DRIFT (L3 B3a),
   GEN-261019-02 (L3 A3 parent), GEN-261027-01 (L3 A1 parent).
 Sources: L2/work (L3-fromopen, RW3, RW5), hsscale/work (lowdist, rsi5hi, RW6), S/work (GEN-261029-06, GEN-261023-06),
   L3/work ctrl 0 (B3a, A3, A1), R3B/work = bench10 stages re-run unchanged (CWT09, CWT14, NM-RWN4, NM-ETF).
 Families (<= 2 per family in a book): GAPDOWN-SHORT {L3 x3, RW3, RW5, CWT09}; NS2-SHORT {RW6, NM-RWN4};
   GEN-LATE-SHORT {GEN-261029-06}; GEN-POP-SHORT {GEN-261023-06}; ETF-DIP {NM-ETF}; FAILBRK {CWT14}; TREND {B3};
   PM-DIP-LONG {GEN-261019-02, GEN-261027-01}.
LIVE: all setups with >= 20 deduped live trades (10 journals 10-06..11-24, LR8, X/live_dedup.parquet), used for the live
 walk-forward; families by name (gapdn/gap-slope/gapdown -> GAPDOWN-SHORT; WB copies = parent; else own stem).

## Book mechanics
 Each candidate booked alone under TESTING rules (bench10.TESTING_RULES: cap 100, <= 3 lots/symbol, price >= $5,
 stop-cost filter 0.15R, shorts ETB >= 90%). Gates are filters on saved trades before the book.
 Weights W2 (main, "equal risk"): every trade of setup s carries w_s = 1/max(1, FIT trades-per-session of s) R
 (live WF: tps from records before the week). Book daily R = sum_s w_s x R. A 10-setup book is compared at the SAME
 budget (x 5/10); W1 (1R per trade, live-like) reported beside it.
 Costs: research LR8 basis (bench10.add_r: tod multiplier, x3 extended tier, borrow) = main; "LR8-lab" sensitivity
 (entry 1 bp; stop exit max(2c, 4 bp); market exit max(1c, 1 bp); target 0; + borrow) reported beside it (sub-$20 bias).
 Splits: FIT 2024-10 + 2025-03..09 (170); CHECK 2025-10..2026-11-04 (276); T2 2023-01-03..2024-09-13 (427). Locked
 block never read. CHECK is NOT clean for most of the pool (TIER B list was chosen partly on it); T2 and live after
 11-04 are the cleaner tests.

## Book configs (selection on FIT only; 9 lab + 1 live = 10 configs)
 Constraints for all unless stated: 5 setups, 2 or 3 longs (each gated), <= 2 per family.
 B1 (PRIMARY) maximize FIT  mean_daily - 0.05 x |avg worst-5 days|   (W2)
 B2 lambda 0 (max FIT mean daily R)
 B3 lambda 0.15
 B4 maximize FIT day t (mean/sd x sqrt n)
 B5 B1 with exactly 3 longs + 2 shorts
 B6 B1, longs gated TT1 only
 B7 B1, longs gated SPYOPEN only
 B8 B1 in W1 weighting
 B9 team-blind: the 5 best by FIT avg R/trade (>= 20 FIT trades), same constraints
 WF live walk-forward: weekly, rule B1 on live daily records before the week (pool >= 20 trades before the week), score
   the next week; comparators chosen the same way: top-10 by live total R before the week, and the actual Primary account.

## Reference books
 TOP10 = bench10 TOP10 list (home-account rules, home cost basis), PRIMARY = current Primary roster {L3-fromopen, RW3, RW5,
 NM-ETF} under Primary rules (cap 30, -2R latch). Live: same lists' pooled live trades; Primary account's actual record.

## Metrics (every book, every window)
 avg daily R, green-day %, worst day, avg of worst 5 days, total R w/o best day + best-day share, day t, per-setup
 contribution; correlation with the Primary book; R on Primary's 10 worst days.

## "Clearly beats the top-10" (all must hold for B1; others reported)
 On BOTH CHECK and T2 at the same budget: avg daily R higher, avg worst-5 better, day t higher, paired daily difference
 > 0 in both with paired t >= 2.0 in at least one; AND live: WF book total R >= WF top-10 and worst-5 better; AND the frozen
 book's live record 11-05..11-24 not worse than the top-10's. Else verdict = does not clearly beat.
 If yes -> propose as a Testing account book (owner decision). Never Primary.
