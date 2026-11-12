Educational only — not financial advice.

# obs-unrated — the 39 unrated setups and Testing A's full-universe lever (Observer, 2026-11-11 ~19:45 ET; descriptive, 0 configs)

Lead lead-20261111-1905-2. `unrated.py` -> `unrated_out.txt`. Expected setup-days/week = 5 x p_day, p_day = 1 - exp(-0.193 x lab trades/day)
(Scout's REPS2 fit). Lab rate: Gen setups from config/account_gen.yaml gen.screen.per_day (2y screen); others from rates stated in research
notes (cited); else 'no lab rate found'.

## Results
- **25 of 39 have a lab rate; together they add ~40 setup-days/week** (~+8% on REPS3's 482.8). **39.4 of the 40 come from 22 Gen setups.**
  Top: GEN-261023-09 (ORBfailDn ... LATE, 12.7 trades/day screen -> ~4.6 days/week), GEN-261020-10 3.3, GEN-261028-10 3.1,
  GEN-POD1022-01 (Thrasher breadth thrust) 3.1, GEN-261022-09 2.9; then ten more at 1-2.3 days/week each.
- **Calibration of the screen rate** on the 71 Gen setups that already have live records: predicted p_day 0.52 vs live 0.46,
  median live/predicted 0.94, corr 0.43. So the totals are roughly right, and any single setup is +-1 day/week.
- The 14 non-Gen setups have no lab rate in a file I can read (IDX1/2/3 index trails, LD4-8, CWT04-backside a25 variants, CWT14-pdl-R2A-short,
  NM-RWR1, LIQ-pdl-sweep). The 3 with stated rates are rare: LD1 0.33, LD3 0.25, IDX5 0.04 days/week. **The index (IDX) and SPY-dip (LD6/LD8)
  setups fire on a market state, so at most once a day by design; expect well under 1 day/week each.** Builder's lists could rate them exactly.
- Placement: the unrated Gen setups are the only large block. They add days only where Gen has room: Gen's halt and buying power skips
  (REPS1b) cut submitted days, so placing the top Gen-unrated setups in a testing area with free slots (Testing D-F) is where they add the most days.

## Testing A's full-universe lever: not measurable from the journals
- The top-500 pool works BEFORE a signal is logged, so there are no 'universe' skip rows (0.0 per session before and after 11-04).
- Before (10-20..11-03, 11 sessions) vs after (11-04..11-10, 5): signals 270 -> 280/session, trades 150 -> 155, setup-days 17.2 -> 13.2,
  avg R -0.060 -> -0.196. **Confounded:** setups moved out on 11-05 (ROLL1 homes), the CF cost filter started 10-30, and 11-04/05 is the sell-off.
- To measure it: replay Testing A's setups on the lab universe for 11-04..11-10 with and without the top-500 cut (Builder's FWDCAL mirror
  can do it), counting setup-days and gross R of the names the cut removed.
