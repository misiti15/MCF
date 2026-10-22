# top5_1022 pre-declaration: execution variants of the top live setups (seventh run)

*Educational only - not financial advice.*

Written 2026-10-22 ~22:10 UTC after the live ranking (`live_rank.py`, live paper trades only) and **before any history
configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-16, 19, 20, 21, 22; Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-* out, "-FD" copies
are their own setup. Account membership from `docs/live/assignments.json` (17:07 ET 10-22); Graveyard setups are out.

- **Out - tuned in the last 3 runs (top5_1019 / 1020 / 1021), no change since:** CWT14 pdl-p05-long (169), pdl-p10-long
  (81), pdl-p05-lowvol-long (76), coil-k4 (50), pdl-p10-lowvol-long (49), coil-k6 (39).
- **Out - studied today (cited, not redone):** L3-gap-slope-fromopen-FD (118; l3_1022, now Testing 1),
  NS3-failed-vwap-reclaim-short-FD (68; ns3var1022), RW5-FD (51) / RW3-FD (47) / MF2-FD (35) / MF4-FD (35) (bdi1022
  gap-down family window study), pdh-p10 family (pdh1022, Graveyard).
- **Scored (next eligible by live count):** MF3-open-flowsell-rsi5hi-FD (74, T1), RW7-gapdn-bounce-early-short-FD (62,
  T1), RW4-ns3-adv150-short-FD (54, T1+T2), exhaustion_short-FD (39, T1+T2), and the tie at 29 for fifth:
  MF5-flowsell-vwapup-rsi5hi-FD (T2) and RW1-gapdn-bounce-flowsell-short-FD (T2) - both scored. **6 setups.**
- MF3-FD was queued by top5_1021 ("needs an MF3 harness") - this run supplies it.

## 2. Harness, data, costs, splits
- Entries: gates1021's cached live-shaped signal rows (`gates1021/scripts/scan.py`: live module, live window, min ADV,
  live refire/cooldown chain) for the 6 setups. Exits: top5_1019 `sim` on the 5-minute paths from
  `top5_1019.build_paths` (stop first; costs entry 1c + 1 bps x ToD, limits free, stops +2c, market exits 1c + 1 bps).
  All 6 parents are short t1s1 (target 1R, stop 1R, R = 0.25 x daily ATR), flatten 15:55.
- Parity: the sim parent vs gates1021's cached production R per trade (report match share / mean |d|); deltas are
  always variant sim vs parent sim on the same harness.
- Open months only; the locked block 2024-11-01..2025-02-28 is never loaded (cache asserts no locked rows). TRAIN
  <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD (2026-04..06, 2026-09-16..10-07) scored once only for a
  Testing candidate.
- Random control: gates1021's same-minute random-symbol control (c_short_t1s1) for the parent; for any Testing
  candidate the control is re-run under that variant's knob before a proposal.
- Stop-distance rows at the same $ risk (r divided by stop / parent stop).

## 3. Grid (one knob per row; every row counts)
| id | knob |
|---|---|
| E01 | time stop 30 min if best < +0.2R |
| E02 | time stop 60 min if best < +0.25R |
| E03 | tighter stop x0.85 (same $) |
| E04 | wider stop x1.25 (same $) |
| E05 | wider stop x1.5 (same $) |
| E06 | scale half at +0.5R, stop to breakeven |
| E07 | breakeven (no scale) after +0.5R |
| E08 | target 0.75R |
| E09 | target 1.5R |
| E10 | wait one bar (enter next bar's close) |
| E11 | window start 10:30 |
| E12 | window end 13:00 |
| E13 | skip entries 10:00-10:29 (live loser cluster, MF3-FD 20 trades -0.78R) |
| E14 | extra filter: skip shorts while SPY is up from the open (> 0) |
| E15 | loser pattern "never worked" (RW7-FD 17 of 31 live losers never reached +0.2R): time stop 15 min if best < +0.1R |

Not scored, declared: thresholds +-20% (the cached signals carry no module-threshold hook; would need each module
re-run) and re-entry cooldown (the cached chain already applies the live refire/cooldown).

**N (study) = 15 x 6 = 90.** Study bar max(1.5, sqrt(2 ln 90)) = **3.00**; setup bar (N 15) sqrt(2 ln 15) = **2.33**.

## 4. Bars (fixed now)
- **Beats parent** (backlog, tag `top5-tune`): d > 0 on TRAIN and on VALID, and day-clustered t of d over TRAIN+VALID
  >= 2.33.
- **Testing candidate:** beats parent, exp > 0 on TRAIN and VALID, VALID day-clustered t >= 3.00, up and down SPY
  sessions each > 0, ex-best-day > 0, excess over random > 0; then HOLD once. Otherwise no proposal.
- Every row reported in `results.csv`, failures first.
