# BLKOUT — result and reading (Observer, 2026-11-17 ~19:50 ET). CLOSED. Educational only — not financial advice.

One run, exactly as signed (Amendment 1 + 1b), by Builder in his container; output research/blkout/blkout_out.txt. 0 configs, descriptive;
informs the owner's blackout policy only. Source: 2-year backtest (GLOSSARY), full-day lists, 1,172,116 trades; half days dropped 4,843;
976 of 1,226 names (80%) have >= 6 reports and are kept (81% of trades); 42,154 trades within 10 sessions of a block edge dropped.
Groups: inside (|k| <= 4) 151,302, outside (|k| >= 10) 623,148, buffer 138,084; 96% of inside events have a trusted BMO/AMC time.

## Primary (within setup x ISO-week, day-clustered; gross first)
| period | gross | ex-market | net | MDE80 (ex-market) |
|---|---|---|---|---|
| TRAIN (149 days) | -0.0170R, t -1.79 | -0.0139, t -1.55 | -0.0232, t -2.21 | 0.025 |
| VALID (252 days) | -0.0034R, t -0.46 | -0.0009, t -0.14 | -0.0062, t -0.81 | 0.018 |
| FWD (23 days)    | -0.0341R, t -1.84 | -0.0288, t -2.09 | -0.0380, t -1.94 | 0.039 |

## Reading (pre-registered table, row 2): |t| < 2 in VALID
Nothing above ~0.02R per trade either way: the blackout neither costs nor saves existing setups measurably in VALID. The sign is negative
(inside worse) in all three periods and every measure, so if anything the policy leans PROTECTIVE; and the 2-year backtest charges inside
trades too little (x3 costs only at |gap| >= 20%), so true inside net is lower still. Phase 2 (spread re-charge) is not needed: it is only
triggered by inside > outside. Policy stands (Lead lead-20261117-1900-2).

## Secondary (descriptive, 21 cells counted)
- Per setup (>= 30 inside, VALID, ex-market): 49 better / 41 worse; side: shorts +0.003 (t 0.21), longs -0.004 (t -0.50).
- Offset x report time (18 cells): the reaction day k = 0 is the weakest in both: BMO -0.064 (t -3.57, the only |t| > 2 cell), AMC -0.022
  (t -1.45). Post hoc, 1 of 18; consistent with the report day being where existing setups get hurt.
## For the Move Hunt thread
~62% of big moves (~31/day) sit in blackout names, but existing setups do not earn there (inside <= outside, report day worst). So that
pool is not a gap the current setups would fill by lifting the blackout; it would need event-specific setups, which only FAMC's Shadow
(next-session after-close reporters) currently tests.
