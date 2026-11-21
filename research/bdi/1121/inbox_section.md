Educational only — not financial advice.

## DECISION | bdi-1121 | CODE: BDI-RW1121 — park both reworked near misses (no Testing admission)
- **What:** this is the rule-18 rework round on the two closest failed ideas, the beginner batch's BEG-06
  noise-area breakout and BEG-04 quiet gap fade. There were 16 configs, pre-registered, run in the bench10 normal way
  with LR8 costs.
- **Result:**
  - BEG-06's FIT pick (hourly checks) scored CHECK −0.088R (n 331, w/o best day −0.127). FAIL.
  - BEG-04's FIT pick (gap ≥ 2.0%) scored CHECK −0.034R (n 3,375, w/o best day −0.087). FAIL on the pass; NEAR
    against the top-10 standard by 0.009R, the same place as before.
  - Every FIT figure is the April-2025 tariff week.
- **Recommend: Yes** (park both; no Testing slot). Each lineage now has 12 configs and 3 CHECK looks. The edge, if
  any, is in which days, not in the trigger, stop or target.
- Evidence: research/bdi/1121/REPORT.md §2, rework/PLAN.md.

## DECISION | bdi-1121 | CODE: BDI-GBCAP — do not adopt a correlated-group lot cap
- **What:** this is the give-back remedy tested against the 11-20 NM-ETF stack (12 correlated ETF lots in
  14:11-14:16 ET, all stopped, −12.6R). Correlated symbols (≥ 0.85) count as one symbol for the lot cap.
- **Result:**
  - On NM-ETF itself: FIT −38.6R / CHECK −6.6R at 1 lot per group, and FIT −31.6R / CHECK −0.6R at 2 per group.
  - Across 11 setups, the 2-per-group version made 9 setups worse and 2 better (CHECK −14.5R).
  - The stacked dips are NM-ETF's best two-year trades.
- **Recommend: No** (do not deploy). No give-back proposal survives this week. BRAKE-BURST (from 11-23) would not
  have bound in Primary this week (max 13 entries in 10 min).
- Evidence: REPORT.md §5, giveback/PLAN.md, giveback/groupcap_out.txt.

## DECISION | bdi-1121 | CODE: BDI-MH4 — screen two new Move Hunt ideas next week
- **What:** 4 ideas from this week's big moves are filed in the backlog as untested candidates. Long-side capture
  was 1 of 100 big moves.
- **The proposal:** pre-register and run the 2-year screen on the two strongest:
  - **crypto complex follows bitcoin:** 11-20 had 5 crypto ETFs among the top-25 shorts and 2 inverse crypto ETPs
    among the top-25 longs;
  - **peer-group laggards:** managed care moved as one group on 11-18 (6 names) and 11-19.
- **Recommend: Yes.** Research time only; nothing goes live without the usual bars.
- Evidence: REPORT.md §3, scan/NOTES.md.

## FYI | bdi-1121 | Discover workflow not run yet today
- Today's scheduled discover run had not started by 16:25 UTC. Last week's scheduled run started about 5 hours
  late. The bar cache and backlog re-test therefore stand at 11-14 (run 43630905330, success).
- If no 11-21 run shows by Sunday, it can be started by hand (Actions → discover → Run workflow).
- That re-test scores only 66 of 380 runnable entries (312 have no lab module). Two broken entries are
  housekeeping fixes.

## FYI | bdi-1121 | Week 11-16..11-20 scorecard (Primary is the scoreboard)
- **Primary:** +4.1R / 193 trades, +$766.61, 2/5 green days.
- It is a one-big-day week: 11-16 made +25.3R, and without it the week is −0.156R a trade.
- Best: L3-fromopen +11.5R (`1 day`), RW5 +8.2R, RW3 +6.3R. Worst: NM-ETF −12.1R (all on 11-20) and ST7 −9.7R
  (leaves 11-23).
- **Give-back:** 44.3R from intraday peaks, made of open winners stopped (−25.2R, mostly 11-19) and entries after
  the peak (−19.6R, mostly 11-20 NM-ETF).
- **The −2R latch:** net cost about 2.8R this week. It saved 19.6R on 11-19 and cost 14.3R on 11-17.
- **Twin cap:** did not bind in Primary.
- **Rule changes:** 11-12 LR8 costs; 11-17 TSZ1 testing sizing; 11-19 NS5 out of Primary; 11-23 ST7 out,
  BRAKE-BURST, retirements.
