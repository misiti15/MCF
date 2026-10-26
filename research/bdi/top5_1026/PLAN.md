# top5_1026 pre-declaration: execution variants of the top live setups (ninth run)

*Educational only - not financial advice.*

Written 2026-10-26 after the live ranking (`live_rank.py`, live paper trades only) and after the signal cache rebuild
(`build_cache.py`, signals only, no variant scored), **before any history configuration below was scored**. Results go
in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-20, 21, 22, 23, 26 (10-26 started ~10:39 ET: no 09:50-10:39 trades that day); Primary + Testing 1 +
Testing 2 reports, run_id 1, S6 and GEN-* out, "-FD" copies are their own setup. Account membership from
`docs/live/assignments.json` (last change 2026-10-25 21:30 ET); Graveyard setups are out (pdh-p10-short 75,
pdh-p05-lowvol-short 54, ...).

- **Out - tuned in the last 3 top-5 runs (1021 / 1022 / 1023), no change since:** L3-gap-slope-fromopen-FD (149; 1023),
  coil-k4 (104; 1021, also D3 Graveyard proposal tonight), pdl-p05-lowvol (102; 1023), pdl-p10 (88; 1023), RW7-FD (57;
  1022), RW5-FD (51; 1023), pdl-p10-lowvol (49; 1021), coil-k6 (48; 1021, D3), MF3-FD (44; 1022), exhaustion_short-FD
  (43; 1022), RW3-FD (34; 1023), RW4-FD (33; 1022).
- **Cannot be backtested:** CWT13-vwapstretch-z05-long (39, Primary since 10-26): not in the two-year signal cache
  (gates1021 `why_not`: needs 09:35-09:45 head rows) and no CWT13 kernel exists in the top-5 harness. Skipped; next taken.
- **Scored (next eligible by live count):**
  1. CWT14-failbrk-pdl-p05-long (211, T1) - last tuned top5_1020 (R0, E01-E13, T1/T2). Parent = live t05s1 + 0.25R
     scale-out (half, rest to breakeven).
  2. NS3-failed-vwap-reclaim-short-FD (45, T2) - cited, not tuned, in top5_1021 / 1023 (gates1021 / ns3var1022 work).
     Parent t1s1, refire cd1 as run.
  3. MF2-open-rsimidhi-flowsell-FD (33, Primary) - never top-5 tuned. t1s05 (target 1.0, stop 0.5 in units of 0.25 ATR),
     refire cd1.
  4. MF4-h40-open-flowsell-FD (33, Primary) - never top-5 tuned. t05s1, no refire.
  5. L3-gap-slope-rsi5hi-FD (32, T2) - never top-5 tuned. t05s1, refire cd6, min_adv 0.
  MF2-FD / MF4-FD are Primary: analysed only; a variant can at most be an **additional Testing setup**.

## 2. Harness, data, costs, splits
- CWT14 pdl-p05-long: top5_1019 `scan_1019` kernels (`S6.b3_any(PD, p 0.05, any vol, long)`, window 09:50-15:00,
  ADV >= 95M, first signal per symbol-day) + 5 same-bar random symbols per signal (seed 20261026).
- Shorts: gates1021 live-shaped signal rows (live module, window, ADV, refire chain) rebuilt to scratch by
  `build_cache.py` (gates1021 `scan.month_job` unchanged). Random control = cache's same-minute random-short column at the
  parent geometry.
- Exits: top5_1023 simulator copy (stop first; entry 1c + 1 bps x time-of-day multiplier; target limits free; stops
  +2c; market exits 1c + 1 bps; x3 on the extended tier). Stop-distance rows at the same $ risk (target price
  unchanged). **Parity gate:** each short parent's simulated R must equal the cache's production R (mean |d| < 0.002R)
  before any variant is read.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16..10-07) dropped, scored once only for a Testing candidate.
- Bars: beats parent = paired day-clustered t_improve >= max(1.5, sqrt(2 ln N_setup)) and d > 0 in TRAIN and VALID.
  Testing bar = exp > 0 in TRAIN and VALID, VALID t >= study bar max(1.5, sqrt(2 ln N_total)), up and down sessions > 0,
  avg R without best day > 0, beats random.

## 3. Grids (one knob per row; every row counts)

### CWT14 pdl-p05-long (16): top5_1023 C01-C14 + 2 loser-pattern rows
| id | knob |
|---|---|
| C01 | stop x1.5, target and scale price unchanged (same $) - re-score of top5_1020 E05 |
| C02 | stop x2.0 (same $) |
| C03 | target 0.35R |
| C04 | target 0.75R |
| C05 | "never worked" time stop 15 min if best < +0.1R (live: 36 of 68 losers never reached +0.2R) |
| C06 | time stop 90 min if best < +0.25R |
| C07 | clock exit 14:00 |
| C08 | window end 13:00 |
| C09 | skip 09:50-09:59 |
| C10 | skip 10:00-10:29 |
| C11 | skip when SPY down > 0.5% from open |
| C12 | skip when the stock is down > 2% from open |
| C13 | re-entry after the first trade exits, cooldown 15 min |
| C14 | limit entry 0.1R better, valid one bar |
| C15 | skip 10:30-11:29 (live loser cluster: 46 trades -0.18R) |
| C16 | index-chase veto: skip when SPY is up > 0.5% from open (10-26 entries at the 11:02 index high) |

### Shorts (E01-E17 each; geometry-adjusted rows marked)
| id | knob |
|---|---|
| E01 | time stop 30 min if best < +0.2 (units of 0.25 ATR) |
| E02 | time stop 60 min if best < +0.25 |
| E03 / E04 / E05 | stop x0.85 / x1.25 / x1.5 (same $) |
| E06 | scale half + stop to breakeven at +0.5 (t05s1 setups MF4 / L3-rsi5hi: at +0.25) |
| E07 | breakeven after +0.5 (t05s1: after +0.25) |
| E08 | target 0.75 (t05s1: 0.35) |
| E09 | target 1.5 (t05s1: 0.75) |
| E10 | wait one bar |
| E11 | window start 10:30 |
| E12 | window end 13:00 |
| E13 | skip 10:00-10:29 |
| E14 | skip shorts while SPY is up from the open |
| E15 | "never worked" time stop 15 min if best < +0.1 |
| E16 | clock exit 14:00 |
| E17 | limit entry 0.1 better, valid one bar |
| E18 (NS3-FD) | window start 11:30 (live: 10:00-11:30 entries 14 trades -0.58R, 1 win) |
| E18 (MF4-FD) | window end 11:30 (live: 11:30-13:00 entries 11 trades -0.23R) |

NS3-FD's 10 of 32 live losers that reached +0.5R first are covered by E06 / E07 (profit protection).

**Total: 16 + 18 + 17 + 18 + 17 = 86 configurations** (plus 5 parent reference runs). Study bar
max(1.5, sqrt(2 ln 86)) = 2.98.
