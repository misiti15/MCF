Educational only — not financial advice.

# obs-costkilled — lab cost charge vs live paper cost on the cost-killed setups (Observer, 2026-11-10 ~22:00 ET)

Lead's request lead-20261110-2100-2. Descriptive, 0 configs. `costkilled.py <journals> 2026-10-06 2026-11-09` -> `costkilled_out.txt`.
17,581 live paper trades joined to signals (all 7 accounts); 95 setups with >= 30 trades; same cost model as costgap.py / obs-stopcost.
Cost-killed = gross > 0 and lab net < 0, recomputed on the window through 11-09: **17 setups, 1,719 trades** (was 14 to 11-06).

**Rule changes inside the window** (research/ledger.jsonl): Owner CF cost filter from **10-30** (Testing 1/2 skip entries whose stop round-trip
cost > 0.15R), which changes these setups' trade mix; Primary size ~$4k from 10-28; Primary per-setup -2R stop from 10-29; ST-A per-setup stop
off in Testing/GEN from 10-23.

## Failures first
- Live paper costs these setups about a third of the lab charge: **+0.065R vs +0.192R per trade** (pooled, trade-weighted). Live net is
  +0.026R pooled, and 9 of 17 are positive live. **But only 2 of 17 stay positive without their best day.** For the rest, one day carries
  more than the whole total (MF2-FD best day = 213% of its total; NS4-FD 196%; L3 variants 131-194%; GEN 422-649%).
- The 2 survivors, both Testing 'gap-down bounce' SHORTS:
  | setup | n | days | gross | live cost | lab cost | live net | w/o best day |
  |---|---|---|---|---|---|---|---|
  | RW7-gapdn-bounce-early-short-FD | 436 | 19 | +0.113 | +0.052 | +0.177 | +0.061 | +0.032 |
  | RW1-gapdn-bounce-flowsell-short-FD | 108 | 20 | +0.121 | +0.033 | +0.163 | +0.088 | +0.045 |
- **And both earn it all after 10-30**, the cost-filter era, which is also the 11-04/11-05 sell-off (shorts):
  RW7 before 10-30 live net -0.039 (302 trades, 14 days), from 10-30 +0.288 (134, 5 days); RW1 +0.029 (79, 14) -> +0.250 (29, 6).
  Rule change and regime overlap completely; this window cannot separate them. Days positive: RW7 10 of 19, RW1 12 of 20.

## Reading
Execution matters (live paper cost is ~1/3 of the lab charge on these names), but 'cost-killed but actually net positive as traded' holds
for none of the 17 on a robust basis yet. For Builder's limit-entry study: the cost gap is mostly entry slip (e_cost +0.040 avg here, negative
for MF2-FD -0.061), and the setups where it matters most are the tight-stop MF flow-sell shorts (stop 55-70bp, lab cost 0.28-0.38R).
