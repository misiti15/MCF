# top5_1028 pre-declaration: execution variants of the top live setups (eleventh run)

*Educational only - not financial advice.*

Written 2026-10-28 after the live ranking (`live_rank.py`, live paper trades only), **before any history
configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-22, 23, 26, 27, 28 (10-26 started ~10:39 ET; GX1 5-minute clock gate live from 10-27, so 10-27 / 10-28
counts run higher). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-* out, "-FD" copies are their own
setup. Account membership from `docs/live/assignments.json` (last change 2026-10-28 18:00 ET).

- **Out - Graveyard:** CWT12-coil-k4-long (236; owner K4-2, Graveyard from 10-29), CWT14-pdh-p10-short (23),
  coil-k6 (17).
- **Out - tuned in the last 3 top-5 runs (1023 / 1026 / 1027), no setup/exit change since** (account moves and the
  Primary sizing / -2R stop changes are not setup/exit changes): pdl-p05-long (309; 1026), pdl-p05-lowvol (183; 1023),
  pdl-p10 (140; 1023), pdl-p10-lowvol (79; 1027), L3-fromopen-FD (74; 1023), RW5-FD (50; 1023), RW3-FD (33; 1023),
  MF2-FD (33; 1026), exhaustion_short (32; 1027), L3-rsi5hi-FD (30; 1026), NS3-FD (25; 1026), MF4-FD (24; 1026),
  NM-AR-AM (22; 1027), L3-lowdist-FD (17; 1027).
- **Cannot be backtested:** CWT13-vwapstretch-z05-long (40, T2): no CWT13 kernel in the harness (fourth run).
- **Avoided:** the high-frequency half-R cost-floor idea (covered by research/bdi/hf1027); none of tonight's setups is a
  half-R setup.
- **Scored (next eligible by live count; all last tuned top5_1022, four runs ago):**
  1. RW7-gapdn-bounce-early-short-FD (90, T1)
  2. exhaustion_short-FD (64, T1+T2 split)
  3. MF3-open-flowsell-rsi5hi-FD (35, T1, ex-primary)
  4. RW1-gapdn-bounce-flowsell-short-FD (31, T2)
  5. RW4-ns3-adv150-short-FD (31, T1+T2 split)
  All are t1s1 shorts, window 09:50-15:00. A variant can at most be an **additional Testing setup**.

## 2. Harness, data, costs, splits
- Entries: gates1021 live-shaped signal rows (live module, window, ADV, refire chain) rebuilt to scratch by
  `build_cache.py` for the 5 setups. Exits: the top5_1027 simulator (limit-entry mode, clock exit only for trades
  opened before it, x3 extended tier). Random control = the cache's same-minute random short at t1s1.
- **Parity gate:** each parent's simulated R must equal the cache's production R (mean |d| < 0.002R) before any
  variant is read.
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier. Stop-distance rows at the same $ risk (target price unchanged).
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16..10-07) dropped, scored once only for a Testing candidate.
- Bars: beats parent = paired day-clustered t_improve >= max(1.5, sqrt(2 ln 14)) = 2.30 and d > 0 in TRAIN and VALID.
  Testing bar = beats parent, exp > 0 in TRAIN and VALID, VALID t >= study bar max(1.5, sqrt(2 ln 70)) = 2.91, up and
  down sessions > 0, avg R without best day > 0, beats random.

## 3. Grid (one knob per row; every row counts; knobs top5_1022 did not score on these setups)
| id | knob |
|---|---|
| F01 / F02 | stop x2.0 / x2.5 (same $) - top5_1022 E04/E05 (x1.25/x1.5) beat the parent on 4 of 6; is the curve still rising? |
| F03 / F04 | target 0.5R / 2.0R |
| F05 / F06 | clock exit 12:00 / 14:00 |
| F07 | limit entry 0.1R better, valid one bar |
| F08 | skip when SPY up > 0.5% from open (index-reversal veto; bdi recurring pattern) |
| F09 | skip when SPY down > 0.5% from open (late short into a sell-off) |
| F10 | skip when the stock is already down > 2% from open |
| F11 / F12 | window end 11:30 / window start 11:30 |
| F13 | skip 10:30-11:29 |
| F14 | time stop 120 min if best < +0.25R |

**Total N = 14 x 5 = 70.** Study bar max(1.5, sqrt(2 ln 70)) = 2.91. Setup bar 2.30.
