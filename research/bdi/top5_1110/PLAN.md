# top5_1110 pre-declaration: execution variants of the top live setups (nineteenth run)

*Educational only - not financial advice.*

Written 2026-11-10 (after the close) after the live ranking (`live_rank.py`, live paper trades only), the Part A live
bucket reads and the signal-cache build (signal times only, no R read), **before any history configuration below was
scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-11-04, 11-05, 11-06, 11-09, 11-10 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-*
out (so the EXPO1109 GEN setups in Testing 1/2 on 11-09 / 11-10 are out), "-FD" copies are their own setup. Last 3 runs
= top5_1109, top5_1106, top5_1105.

Rule changes in effect inside this window (research/ledger.jsonl effective dates): NS5-FD / ST4-FD / RW6G1-FD ->
Graveyard and the UNI1 top-500 pool in Testing 2 (11-04); ROLL1 low-rep setups -> Explore 1 / Live Lab (11-05);
**EXPO1109 temporary moves (11-09 + 11-10): five GEN setups Gen -> Testing 1 / 2** (reverted from 11-11). Already in
force for the whole window: CF cost filter in Testing 1/2 + BAR90 (10-30), Primary ~$4k (10-28), Primary -2R per-setup
latch (10-29). None of the 5 setups below had a setup or exit change since its last tune (top5_1104). Market: 11-05 SPY
-4.2%, 11-06 quiet with a 10:41 squeeze, 11-09 SPY +1.4%, 11-10 midday flip-up (+0.56% 10:08 -> -0.38% 12:45 -> +0.27%).

- **Out - pdl lineage exhaustively tuned (pdl1030/b/c):** CWT14-failbrk-pdl-p10 (120), p05-R2A-long (97), p10-lowvol
  (70), p05-R2A-short (22).
- **Out - tuned in the last 3 runs, no setup/exit change since:** RW3S-FD (180), exhaustion_short-FD (32), RW1-FD (30),
  NM-AR-AM (18), L3-lowdist-FD (14) (top5_1109); CWT13-z05-long (124), MF4-FD (78), exhaustion_short (34), NM-HL, NS3
  base (top5_1106); NS1-FD (45), MF5 (18), NS3V1 (23), L3-rsi5hi-FD (17), NS5 (top5_1105).
- **Out - not coverable by the gates1021 harness:** CWT05-flush-m05-v3-long (34), intraday_momentum (18).
- **Scored (next eligible by live count; all last tuned top5_1104, short):**
  1. RW7-gapdn-bounce-early-short-FD (145, T1). t1s1, ADV >= $95M.
  2. MF2-open-rsimidhi-flowsell-FD (67, Primary). t1s05 (target 1 unit, stop 0.5 unit), ADV >= $95M.
  3. RW3-gapdn-rsi5pop-flowsell-short-FD (42, Primary). t1s1, ADV >= $95M.
  4. L3-gap-slope-fromopen-FD (34, Primary). t1s1, no ADV floor.
  5. RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (33, Primary). t1s1, ADV >= $95M.
  Four are Primary setups. Tonight a winner can at most be proposed as an **additional Testing setup**; no Primary change
  is proposed here (the owner's Wednesday Primary decision, TEAM-6, is prepared separately).

## 2. Harness, data, costs, splits (unchanged from top5_1109)
- Data: 2-year lab frames per `research/bdi/1104/DATA.md` (frames to 2026-11-04).
- Entries: gates1021 live-shaped signal rows rebuilt by `build_cache.py` (to /dev/shm/t5_1110/g). Exits: the top5_1028
  simulator, unchanged; 0.25-ATR units; r divided by the stop multiple (same $ risk; MF2-FD cache R and control also
  divided by 0.5, as since top5_1104).
- **Parity gate:** each parent's simulated R must equal the cached production R (mean |d| < 0.002R).
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16 onward) dropped, scored once only for a Testing candidate.
- Random control = gates1021 same-minute random entry at the parent geometry.
- Compass on history (G17 / G18): W60 15-min compass from `research/bdi/top20/compass_2y.py`, state at the latest
  15-min mark <= the signal bar's start.

## 3. Grid (one knob per row, relative to each parent; every row counts): 19 x 5 = **95 configurations**
| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / x0.75 (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | half off at 0.5 x target distance, stop to break-even |
| G06 / G07 | time stop 30 / 60 min if best < +0.25R |
| G08 | **clock exit 13:00 for all five** (new tonight: the 11-10 midday flip took the open short book; trades opened before 13:00 flatten at 13:00, later entries unchanged) |
| G09 | limit entry 0.1 x stop better |
| G10 | next-bar entry |
| G11 / G12 | **window halves at 11:00** (new tonight: 11-10 Primary entries 11:00-13:59 -35.8R): entries < 11:00 / >= 11:00 |
| G13 | CF: est. round-trip cost <= 0.15 x stop $ |
| G14 | skip price < $20 |
| G15 | first 5 per session |
| G16 | SPY side filter (shorts: SPY below its open at signal) - the loser pattern "SPY above its open" (Part A: RW3, MF2, RW5) as an opportunity |
| G17 | skip against a confirmed compass (shorts: skip W60 UP-confirmed) |
| G18 | half size against a confirmed compass (same trades; R x 0.5 on those) - a sizing idea, not a filter |
| G19 | ADV floor x1.2 (114M); L3-fromopen (no floor) -> ADV >= 95M |

- Beats parent: d R per parent signal > 0 in TRAIN and in VALID, and day-clustered t of the improvement >=
  max(1.5, sqrt(2 ln 19)) = 2.43 (per setup) - study-wide N = 95 -> 3.02 reported too.
- **Testing bar (rule 22, BAR90):** beats parent, exp > 0 in TRAIN and VALID, day-clustered t (TRAIN+VALID) >=
  0.9 x max(1.5, sqrt(2 ln N_lineage)), WF >= 54% positive months, up and down sessions > 0, positive without the best
  day, beats random entries. Lineage N = top5_1104 lineage + 19: RW7-FD 83,081 (BAR90 4.28); L3-fromopen-FD 274,321
  (4.50); RW5-FD 935,035, RW3-FD / MF2-FD 935,034 (4.72).
- No-strangle screen (BDI charter) reported for every filter row: keeps >= 70% of trades and >= 90% of top-decile winners.
- Only a variant meeting the Testing bar is scored once on HOLD (rule 18 rising bar) and proposed as a DECISION.
- Winners (beats parent) go to research/backlog.jsonl, tag `top5-tune`; the grid line per setup is logged as parked.
