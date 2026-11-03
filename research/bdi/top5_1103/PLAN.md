# top5_1103 pre-declaration: execution variants of the top live setups (fourteenth run)

*Educational only - not financial advice.*

Written 2026-11-03 (after the close) after the live ranking (`live_rank.py`, live paper trades only), **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-28, 10-29, 10-30, 11-02, 11-03 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-*
out, "-FD" copies are their own setup. Last 3 runs = top5_1102, top5_1030, top5_1029 (= swarm15_1029 + p1_1029).

Rule changes in effect inside this window (research/ledger.jsonl effective dates): Primary size ~$4k (10-28); Primary
per-setup -2R daily stop (10-29); Setup Generator paused after 10-28; CF cost filter in Testing 1/2 (10-30); moves:
pdl-p05 / p05-lowvol -> Graveyard (10-30), L3-rsi5hi-FD and L3-fromopen-FD -> Primary (10-30), R2A legs into T2
(11-02), NS3-FD + RW4-FD -> Graveyard (11-02), MF3-FD + MF5-FD -> Graveyard (11-03), R2A cap exemption (11-03), RW3S-FD
into Testing 2 (11-03). After the window: NS5-FD / ST4-FD / RW6G1-FD -> Graveyard and UNI1 top-500 pool in T2 (11-04).

- **Out - pdl lineage exhaustively tuned (pdl1030/b/c, 245 configs):** CWT14-failbrk-pdl-p05 (134), p10 (132),
  p05-lowvol (85), p10-lowvol (73), p05-R2A (39).
- **Out - Graveyard (or moving there):** CWT12-coil-k4 (77), MF3-FD (25), RW4-FD (22), MF5-FD (17), NS3-FD (14),
  NS5-FD (14, from 11-04), RW6G1-FD (10, from 11-04).
- **Out - tuned in the last 3 runs, no setup/exit change since:** CWT13-z05-long (84), NM-HL-T75 (35), MF4-FD (17),
  NM-AR-AM (15), exhaustion_short (12) (top5_1102); L3-rsi5hi-FD (21), NS3V1 (19), NS1-FD (14), MF5 (25, = MF5-FD
  signal) (top5_1030); RW7-FD (84), L3-fromopen-FD (51) (swarm15_1029); RW5-FD (30), RW3-FD (15) (p1_1029).
  intraday_momentum (16): classic, no lab kernel.
- **Scored:**
  1. exhaustion_short-FD (44, T1+T2; last tuned top5_1028). t1s1 short, 09:50-15:00, ADV >= 95M.
  2. RW3S-gapdn-flowsell-short-FD (24, T2; **first tune**, added 11-03 as observation). t1s1 short, 09:50-15:00.
  3. RW1-gapdn-bounce-flowsell-short-FD (17, T2; last tuned top5_1028). t1s1 short, 09:50-15:00.
  4. L3-gap-slope-lowdist-FD (11, T1; last tuned top5_1027). t1s1 short, 09:50-15:00, no ADV floor.
  5. ST7-rsi50dn-long-pm-t1s1-FD (10, Primary; **first top-5 tune**). t1s1 long, 09:50-15:00. A variant can at most
     be an additional Testing setup; ST7-FD stays in Primary unchanged without the owner.

## 2. Harness, data, costs, splits (unchanged from top5_1102)
- Entries: gates1021 live-shaped signal rows rebuilt by `build_cache.py` (to /dev/shm: the disk is full tonight).
- Exits: the top5_1028 simulator, unchanged; 0.25-ATR units; r divided by the stop multiple (same $ risk).
- **Parity gate:** each parent's simulated R must equal the cached production R (mean |d| < 0.002R).
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16 onward) dropped, scored once only for a Testing candidate.
- Random control = gates1021 same-minute random entry at the parent geometry.

## 3. Grid (one knob per row, relative to each parent; every row counts)
| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / x2.0 (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | earlier partial: half off at 0.5 x target distance, stop to break-even |
| G06 | clock exit (trades opened before it): RW3S / RW1-FD 12:00, L3-lowdist-FD 14:00, exhaustion_short-FD / ST7-FD 14:30 |
| G07 | time stop 60 min if best < +0.25R |
| G08 | limit entry 0.1R better, valid one bar |
| G09 | enter on the next bar's close (entry timing) |
| G10 | index veto: shorts skip SPY up > 0.5% from open; longs skip SPY down > 0.5% |
| G11 | first part of the window: RW3S <= 10:30, L3-lowdist < 11:30, exhaustion_short-FD / RW1-FD / ST7-FD <= 13:00 |
| G12 | the rest: RW3S >= 10:30, L3-lowdist >= 11:30, exhaustion_short-FD / RW1-FD / ST7-FD > 13:00 |
| G13 | skip when the stock is down > 2% from the open |
| G14 | SPY-side filter: shorts skip SPY above its open, longs skip SPY below it |
| G15 | session cap: first 5 signals per session |
| G16 | CF cost filter as live in Testing since 10-30: skip if (2 x (1c + 1 bps) + 2c) / R > 0.15 at the parent stop |
| G17 | **new, from tonight's top-20 live loser clusters** (RW1-FD, RW7-FD, MF4-FD, RW3S lose most when SPY is flat at entry): skip when SPY is within +/-0.10% of its open at the signal |

**Total N = 17 x 5 = 85.** Setup bar (beats parent) = paired day-clustered t >= max(1.5, sqrt(2 ln 17)) = 2.38 with
d > 0 in TRAIN and VALID. Study bar max(1.5, sqrt(2 ln 85)) = 2.98 also reported.

**Testing bar (rule 22 BAR90):** beats parent; exp > 0 in TRAIN and VALID; day-clustered TRAIN+VALID t >= 0.9 x
max(1.5, sqrt(2 ln N_lineage)); walk-forward positive months >= 54%; up and down sessions > 0; avg R without the best
day > 0; beats random. Lineage N (backlog lineage + earlier top-5 grids + 17 tonight), conservative:
- exhaustion_short-FD: 856,048 + 15 (1022) + 18 (1027, same signal) + 14 (1028) + 16 (1102, same signal) + 17 = 856,128 -> BAR90 4.70.
- RW3S-FD: RW lineage bdi-rw-gapdn-bounce-flowsell 82,068 + simple1102 89 + 17 = 82,174 -> BAR90 4.28.
- RW1-FD: 82,068 + 15 (1022) + 14 (1028) + 17 = 82,114 -> BAR90 4.28.
- L3-lowdist-FD: 274,247 + 18 (1027) + 17 = 274,282 -> BAR90 4.50.
- ST7-FD: bdi-st-st7 120,375 + 17 = 120,392 -> BAR90 4.35.
