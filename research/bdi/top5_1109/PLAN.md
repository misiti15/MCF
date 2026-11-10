# top5_1109 pre-declaration: execution variants of the top live setups (eighteenth run)

*Educational only - not financial advice.*

Written 2026-11-09 (after the close) after the live ranking (`live_rank.py`, live paper trades only), the Part A live
bucket reads and the signal-cache build (signal times only, no R read), **before any history configuration below was
scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-11-03, 11-04, 11-05, 11-06, 11-09 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-*
out (so the EXPO1109 GEN setups moved into Testing 1/2 on 11-09 are out), "-FD" copies are their own setup. Last 3 runs
= top5_1106, top5_1105, top5_1104.

Rule changes in effect inside this window (research/ledger.jsonl effective dates): RW3S-FD into Testing 2 and the R2A
scale-out cap exemption (11-03); NS5-FD / ST4-FD / RW6G1-FD -> Graveyard and the UNI1 top-500 pool in Testing 2 (11-04);
ROLL1 low-rep setups -> Explore 1 / Live Lab (11-05); **EXPO1109 temporary moves (11-09 + 11-10): GEN-261021-02 /
GEN-261019-03 / GEN-261026-02 Gen -> Testing 1, GEN-261022-07 / GEN-261026-03 Gen -> Testing 2** (they share Testing
1/2 capacity with tonight's setups on 11-09). Already in force for the whole window: CF cost filter in Testing 1/2 +
BAR90 (10-30), Primary ~$4k (10-28), Primary -2R per-setup latch (10-29). None of the 5 setups below had a setup or exit
change since its last tune (top5_1103). Market: 11-05 SPY -4.2%, 11-06 quiet with a 10:41 squeeze, 11-09 SPY +1.4%
(UP-confirmed from 10:00).

- **Out - pdl lineage exhaustively tuned (pdl1030/b/c):** CWT14-failbrk-pdl-p10 (120), p05-R2A-long (91), p10-lowvol
  (71), p05-R2A-short (22).
- **Out - tuned in the last 3 runs, no setup/exit change since:** CWT13-z05-long (123), MF4-FD (66), exhaustion_short
  (28), NM-HL, NS3 base (12) (top5_1106); NS1-FD (41), MF5 (24), NS3V1 (23), L3-rsi5hi-FD (12), NS5 (top5_1105); RW7-FD
  (105), MF2-FD (62), RW3-FD (32), RW5-FD (29), L3-fromopen-FD (18) (top5_1104).
- **Out - not coverable by the gates1021 harness:** CWT05-flush-m05-v3-long (28), intraday_momentum (18).
- **Scored (next eligible by live count):**
  1. RW3S-gapdn-flowsell-short-FD (143, T2; last tuned top5_1103; its 5-session owner observation ends 11-09). t1s1.
  2. exhaustion_short-FD (31, T1 + T2; last tuned top5_1103). t1s1.
  3. RW1-gapdn-bounce-flowsell-short-FD (24, T2; last tuned top5_1103). t1s1.
  4. NM-AR-AM-gapdown-capitulation-long (14, T2; **first top-5 tune**; swarm1017 near-miss). t1s1 long, signals only at
     10:50 / 10:55 bars (555 / 121 of 676 in the cache).
  5. L3-gap-slope-lowdist-FD (13, T1; last tuned top5_1103). t1s1, no ADV floor.
  None is a Primary setup. A winner can at most be proposed as an additional Testing setup.

## 2. Harness, data, costs, splits (unchanged from top5_1106)
- Data: 2-year lab frames per `research/bdi/1104/DATA.md` (frames to 2026-11-04).
- Entries: gates1021 live-shaped signal rows rebuilt by `build_cache.py` (to /dev/shm/t5_1109/g). Exits: the top5_1028
  simulator, unchanged; 0.25-ATR units; r divided by the stop multiple (same $ risk).
- **Parity gate:** each parent's simulated R must equal the cached production R (mean |d| < 0.002R).
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16 onward) dropped, scored once only for a Testing candidate.
- Random control = gates1021 same-minute random entry at the parent geometry.
- **Compass on history (new knobs G17 / G18):** W60 15-min compass from `research/bdi/top20/compass_2y.py` (same
  construction as hc1 / mcf.report.compass_live, breadth from the lab context tables), state at the latest 15-min mark
  <= the signal bar's start (strictly earlier information).

## 3. Grid (one knob per row, relative to each parent; every row counts): 19 x 5 = **95 configurations**
| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / x0.75 (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | half off at 0.5 x target distance, stop to break-even |
| G06 / G07 | time stop 30 / 60 min if best < +0.25R |
| G08 | clock exit: RW3S / RW1 12:00, exhaustion_short-FD 14:30, L3-lowdist 14:00, NM-AR-AM 13:00 |
| G09 | limit entry 0.1 x stop better |
| G10 | next-bar entry |
| G11 / G12 | window halves: RW3S <= 10:30 / >= 10:30; exhaustion_short-FD and RW1 <= 13:00 / > 13:00; L3-lowdist < 11:30 / >= 11:30; NM-AR-AM 10:50 bar / 10:55 bar |
| G13 | CF: est. round-trip cost <= 0.15 x stop $ |
| G14 | skip price < $20 |
| G15 | first 5 per session |
| G16 | SPY side filter (shorts: SPY below its open at signal; long: above) |
| G17 | **skip against a confirmed compass** (shorts: skip W60 UP-confirmed; long: skip DOWN-confirmed) |
| G18 | **half size against a confirmed compass** (same trades; R x 0.5 on those) - a sizing idea, not a filter |
| G19 | ADV floor x1.2 (114M); L3-lowdist (no floor) -> ADV >= 95M |

- Beats parent: d R per parent signal > 0 in TRAIN and in VALID, and day-clustered t of the improvement >=
  max(1.5, sqrt(2 ln 19)) = 2.43 (per setup) - study-wide N = 95 -> 3.02 reported too.
- **Testing bar (rule 22, BAR90):** beats parent, exp > 0 in TRAIN and VALID, day-clustered t (TRAIN+VALID) >=
  0.9 x max(1.5, sqrt(2 ln N_lineage)), WF >= 54% positive months, up and down sessions > 0, positive without the best
  day, beats random entries. Lineage N = top5_1103 lineage + 19: RW3S 82,193; exhaustion_short-FD 856,147; RW1 82,133;
  L3-lowdist 274,301; NM-AR-AM 43,359 (swarm1017 arena 43,340 + 19).
- Only a variant meeting the Testing bar is scored once on HOLD (rule 18 rising bar) and proposed as a DECISION.
- Winners (beats parent) go to research/backlog.jsonl, tag `top5-tune`; the grid line per setup is logged as parked.
