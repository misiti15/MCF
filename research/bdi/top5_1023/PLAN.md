# top5_1023 pre-declaration: execution variants of the top live setups (eighth run)

*Educational only - not financial advice.*

Written 2026-10-23 after the live ranking (`live_rank.py`, live paper trades only) and **before any history
configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-19, 20, 21, 22, 23; Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-* out, "-FD" copies
are their own setup. Account membership from `docs/live/assignments.json` (16:00 ET 10-23); Graveyard setups are out
(heat_fade_short-FD 87, pdh-p10-short 79, pdh-p05-lowvol-short 63, orl-p05 62, orl-p05-lowvol 57, heat_fade_short 55, ...).

- **Out - tuned in the last 3 top-5 runs (1020 / 1021 / 1022), no change since:** CWT14-failbrk-pdl-p05-long (226; 1020),
  RW7-FD (62; 1022), coil-k4 (59; 1021), MF3-FD (57; 1022), pdl-p10-lowvol-long (55; 1021), exhaustion_short-FD (46; 1022),
  RW4-FD (46; 1022), coil-k6 (40; 1021).
- **Out - cited, not redone:** NS3-failed-vwap-reclaim-short-FD (62, T2): ns3var1022 scored 95 configurations on it
  yesterday (windows, stop widths, filters, refire) and its decision V1 was applied on 10-22 (NS3V1 + twin group);
  a third grid in two days would repeat it.
- **Scored (next eligible by live count):**
  1. CWT14-failbrk-pdl-p05-lowvol-long (115, T2) - last tuned top5_1019 (18 knobs, no change since).
  2. L3-gap-slope-fromopen-FD (114, T1; demoted from Primary 10-22) - never top-5 tuned (l3_1022 review: 22 variants).
  3. CWT14-failbrk-pdl-p10-long (99, T2) - last tuned top5_1019 (no change since).
  4. RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (54, Primary) - never top-5 tuned.
  5. RW3-gapdn-rsi5pop-flowsell-short-FD (43, Primary) - never top-5 tuned.
  The two Primary setups are analysed only; a variant can at most be proposed as an **additional Testing setup**.
  Primary is never changed by this routine.

## 2. Harness, data, costs, splits
- CWT14 (long, t05s1: target 0.5R, stop 1R, R = 0.25 x daily ATR, first signal per symbol-day, window 09:50-15:00,
  ADV >= 95M): top5_1019 `scan_1019` kernels (`S6.b3_any`, parity-checked against `cwt_live_lib.b3` and
  `gates.lab_trades` in top5_1019) and random control (5 same-bar random symbols, same mechanics, per variant).
- L3-FD / RW5-FD / RW3-FD (short, t1s1): gates1021's cached live-shaped signal rows (live module, window, ADV, live
  refire chain) as in top5_1022; random control = the cache's same-minute random-short column (parent geometry).
- Exits: a copy of the top5_1019 5-minute simulator (stop first; entry 1c + 1 bps x time-of-day multiplier, target
  limits free, stops +2c, market exits 1c + 1 bps) with one added mode: **limit entry** (see L-row below).
- Stop-distance rows at the same $ risk (r divided by stop / parent stop; target price unchanged).
- Open months only; the locked block 2024-11-01..2025-02-28 is never loaded. TRAIN <= 2025-12; VALID 2026-01..03 +
  2026-07..09-15; HOLD (2026-04..06, 2026-09-16..10-07) is dropped and scored once only for a Testing candidate.

## 3. Grids (one knob per row; every row counts)

### CWT14 pdl-p05-lowvol-long and pdl-p10-long (14 each) - only knobs top5_1019 did NOT score
| id | knob |
|---|---|
| C01 | stop x1.5, target price unchanged (same $) |
| C02 | stop x2.0, target price unchanged (same $) |
| C03 | target 0.35R |
| C04 | target 0.75R |
| C05 | "never worked" time stop: 15 min if best < +0.1R (live: 21 of 44 pdl-p05-lowvol losers never reached +0.2R) |
| C06 | time stop 90 min if best < +0.25R |
| C07 | clock exit 14:00 |
| C08 | window end 13:00 |
| C09 | skip 09:50-09:59 (live loser cluster pdl-p05-lowvol: 16 trades -0.29R; same config as top5_1019 E09, re-scored and counted) |
| C10 | skip 10:00-10:29 |
| C11 | extra filter: skip when SPY is down > 0.5% from its open |
| C12 | extra filter: skip when the stock itself is down > 2% from its open |
| C13 | re-entry after the first trade exits, cooldown 15 min (3 bars) |
| C14 | limit entry 0.1R better than the signal close, valid one bar; no fill -> no trade |

### L3-FD / RW5-FD / RW3-FD (short t1s1): top5_1022's E01-E15 + E16-E17 (17 each), RW5 + E18
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
| E13 | skip entries 10:00-10:29 |
| E14 | extra filter: skip shorts while SPY is up from the open |
| E15 | "never worked" time stop 15 min if best < +0.1R (L3-FD live: 15 of 35 losers never reached +0.2R) |
| E16 | clock exit 14:00 (L3-FD live: 58 of 114 trades ended at the 15:55 flatten) |
| E17 | limit entry 0.1R better than the signal close, valid one bar; no fill -> no trade |
| E18 (RW5 only) | window end 14:00 (live loser cluster: 14:00+ entries 6 trades -0.29R) |

Limit entry (C14 / E17): fill only if the next 5-minute bar trades through the limit; the entry bar is checked for the
stop only (never for the target), and the normal entry cost is still charged (conservative).

Not scored, declared: signal thresholds +-20% (CWT14 p +-20% already scored in top5_1019; the cached signals of the
three short setups carry no threshold hook).

**N (study) = 14 x 2 + 17 x 3 + 1 = 80.** Study bar max(1.5, sqrt(2 ln 80)) = **2.96**; setup bars sqrt(2 ln 14) = 2.30
(CWT14), sqrt(2 ln 17) = 2.38 (L3, RW3), sqrt(2 ln 18) = 2.40 (RW5).

## 4. Bars (fixed now)
- **Beats parent** (backlog, tag `top5-tune`): d > 0 on TRAIN and on VALID, and day-clustered t of d over TRAIN+VALID
  >= the setup bar.
- **Testing candidate:** beats parent, exp > 0 on TRAIN and VALID, VALID day-clustered t >= 2.96, up and down SPY
  sessions each > 0, ex-best-day > 0, excess over random > 0; then HOLD once. Otherwise no proposal.
- Every row reported in `results.csv`, failures first.
