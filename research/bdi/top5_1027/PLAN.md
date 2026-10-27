# top5_1027 pre-declaration: execution variants of the top live setups (tenth run)

*Educational only - not financial advice.*

Written 2026-10-27 after the live ranking (`live_rank.py`, live paper trades only), **before any history
configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-21, 22, 23, 26, 27 (10-26 started ~10:39 ET; GX1 5-minute clock gate live from 10-27, so 10-27 counts
run higher). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-* out, "-FD" copies are their own setup.
Account membership from `docs/live/assignments.json` (last change 2026-10-27 16:42 ET). Graveyard setups are out
(CWT14 pdh-p10-short 65, coil-k6 48 (Graveyard since 10-27), pdh-p05-lowvol-short 44).

- **Out - tuned in the last 3 top-5 runs (1022 / 1023 / 1026), no setup/exit change since** (account moves are not
  setup changes): pdl-p05-long (272; 1026), pdl-p05-lowvol (159; 1023), pdl-p10 (110; 1023), L3-fromopen-FD (72; 1023),
  RW7-FD (71; 1022), exhaustion_short-FD (61; 1022), RW5-FD (47; 1023), NS3-FD (40; 1026), MF2-FD (34; 1026), MF3-FD (34;
  1022), RW3-FD (34; 1023), RW4-FD (33; 1022), L3-rsi5hi-FD (29; 1026), RW1-FD (28; 1022), MF5-FD (24; 1022), MF4-FD
  (23; 1026).
- **Cannot be backtested:** CWT13-vwapstretch-z05-long (40, Testing 2 since 10-27): not in the two-year signal cache
  (needs 09:35-09:45 head rows) and no CWT13 kernel in the harness (same as top5_1026). Skipped; next taken.
- **Scored (next eligible by live count):**
  1. CWT12-coil-k4-long (176, T2) - last tuned top5_1021. Parent t05s1 + half scale-out at +0.35R (rest to breakeven),
     window 09:50-11:30, ADV >= 95M, first signal per symbol-day.
  2. CWT14-failbrk-pdl-p10-lowvol-long (78, Primary through 10-27, Testing 2 from 10-28) - last tuned top5_1021.
     Parent t05s1, no scale-out, window 09:50-15:00.
  3. NM-AR-AM-gapdown-capitulation-long (25, T2) - never top-5 tuned. t1s1 long, window 09:50-11:00, no refire.
  4. exhaustion_short (25, T1) - the 13:00-15:00 original (its -FD copy was tuned in 1022). t1s1 short, refire cd1.
  5. L3-gap-slope-lowdist-FD (18, T1) - never top-5 tuned. t1s1 short, window 09:50-15:00, no refire.
  None is in Primary from 10-28; a variant can at most be an **additional Testing setup**.

## 2. Harness, data, costs, splits
- CWT pair: top5_1021 kernels (coil `S5._b4a(k=4, 0.5, 0.25)`, CWT14 `S6.b3_any(PD, p 0.10, vr 1.0, long)`) inside the
  top5_1026 simulator (limit-entry mode, clock exit only for trades opened before it, x3 extended tier) + 5 same-bar
  random symbols per signal (seed 20261027). **Parity gate:** each CWT parent's exp must match top5_1021's parent
  (coil-k4 R0..P, pdl-p10-lowvol P) within 0.003R before any variant is read.
- Cached setups: gates1021 live-shaped signal rows (live module, window, ADV, refire chain) rebuilt to scratch by
  `build_cache.py` for the 3 setups. Random control = cache's same-minute random column at the parent side/geometry.
  **Parity gate:** each parent's simulated R must equal the cache's production R (mean |d| < 0.002R).
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier. Stop-distance rows at the same $ risk (target price unchanged).
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16..10-07) dropped, scored once only for a Testing candidate.
- Bars: beats parent = paired day-clustered t_improve >= max(1.5, sqrt(2 ln N_setup)) and d > 0 in TRAIN and VALID.
  Testing bar = beats parent, exp > 0 in TRAIN and VALID, VALID t >= study bar max(1.5, sqrt(2 ln N_total)), up and
  down sessions > 0, avg R without best day > 0, beats random.

## 3. Grids (one knob per row; every row counts)

### CWT12-coil-k4-long (13; knobs top5_1021 did not score)
| id | knob |
|---|---|
| K01 | stop x2.0 (same $) |
| K02 | target 0.75R (scale-out 0.35 kept) |
| K03 | target 1.0R (scale-out 0.35 kept) - bdi1027 "+1R target would have made +21.9R today" |
| K04 | "never worked" time stop 15 min if best < +0.1R (live: 44 of 62 losers never reached +0.2R) |
| K05 | time stop 90 min if best < +0.25R |
| K06 | clock exit 13:00 |
| K07 | skip 10:00-10:29 |
| K08 | skip when SPY down > 0.5% from open |
| K09 | skip when the stock is down > 2% from open |
| K10 | skip when SPY up > 0.5% from open (index-chase veto) |
| K11 | limit entry 0.1R better, valid one bar |
| K12 | window end 10:30 (live: 10:30-11:30 137 trades -0.095R, 11:30+ -0.30R) |
| K13 | target 1.0R, no scale-out |

### CWT14-failbrk-pdl-p10-lowvol-long (14; knobs top5_1021 did not score)
| id | knob |
|---|---|
| K01 / K02 | stop x2.0 / x2.5 (same $) - top5_1026 queue: stop curve still rising at x2.0 |
| K03 / K04 | target 0.35R / 0.75R |
| K05 | time stop 15 min if best < +0.1R (live: 14 of 26 losers never reached +0.2R) |
| K06 | time stop 90 min if best < +0.25R |
| K07 | clock exit 14:00 |
| K08 | window end 13:00 |
| K09 | skip when SPY down > 0.5% |
| K10 | skip when the stock is down > 2% |
| K11 | skip when SPY up > 0.5% (index-chase veto) |
| K12 | limit entry 0.1R better |
| K13 | skip 10:00-10:29 (10-27: 12 names bought in the 10:10 poll before the 10:17 index low) |
| K14 | skip 10:30-11:29 |

### Cached setups (18 each; t1s1 geometry)
| id | knob |
|---|---|
| E01 / E02 / E15 | time stop 30 min if best < +0.2 / 60 min if best < +0.25 / 15 min if best < +0.1 |
| E03 / E04 / E05 | stop x0.85 / x1.25 / x1.5 (same $) |
| E06 | scale half + stop to breakeven at +0.5 |
| E07 | breakeven after +0.5 |
| E08 / E09 | target 0.75 / 1.5 |
| E10 | wait one bar |
| E11 / E12 / E13 | windows: L3-lowdist from 10:30 / until 13:00 / skip 10:00-10:29; exhaustion from 13:30 / until 14:00 / until 14:30; NM-AR-AM from 10:00 / until 10:30 / skip 10:00-10:29 |
| E14 | shorts: skip when SPY up from open; long: skip when SPY down from open |
| E16 | clock exit: L3-lowdist 14:00, exhaustion 15:00, NM-AR-AM 12:00 |
| E17 | limit entry 0.1R better |
| E18 | shorts: skip when SPY up > 0.5% (index-reversal veto, bdi1027 recurring pattern); long: skip when SPY down > 0.5% |

**Total N = 13 + 14 + 3 x 18 = 81.** Study bar max(1.5, sqrt(2 ln 81)) = 2.96. Setup bars: coil-k4 2.27,
pdl-p10-lowvol 2.30, cached 2.40.
