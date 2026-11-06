# top5_1105 pre-declaration: execution variants of the top live setups (sixteenth run)

*Educational only - not financial advice.*

Written 2026-11-05 (after the close) after the live ranking (`live_rank.py`, live paper trades only) and the Part A
live / two-year bucket reads, **before any history configuration below was scored**. Results go in `NOTES.md`; this
file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-30, 11-02, 11-03, 11-04, 11-05 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-*
out, "-FD" copies are their own setup. Last 3 runs = top5_1104, top5_1103, top5_1102.

Rule changes in effect inside this window (research/ledger.jsonl effective dates): CF cost filter in Testing 1/2 and
BAR90 (10-30); L3-rsi5hi-FD / L3-fromopen-FD -> Primary (10-30); R2A legs into Testing 2 (11-02); NS3-FD + RW4-FD ->
Graveyard (11-02); MF3-FD + MF5-FD -> Graveyard and the R2A scale-out cap exemption (11-03); RW3S-FD into Testing 2
(11-03); NS5-FD / ST4-FD / RW6G1-FD -> Graveyard and the UNI1 top-500 pool in Testing 2 (11-04); ROLL1: 42 low-rep
setups move from Testing 1 (12) / Testing 2 (30) to Explore 1 / Live Lab (11-05). Already in force: Primary ~$4k
(10-28), Primary -2R per-setup daily stop (10-29). 11-05 was a SPY -4.2% session.

- **Out - pdl lineage exhaustively tuned (pdl1030/b/c):** CWT14-failbrk-pdl-p10 (110), p05-R2A-long (76), p10-lowvol
  (65), p05-R2A-short (13).
- **Out - tuned in the last 3 runs, no setup/exit change since:** RW7-FD (95), MF2-FD (35), RW3-FD (30), RW5-FD (26),
  L3-fromopen-FD (11) (top5_1104); RW3S-FD (111), RW1-FD (21), exhaustion_short-FD (19), ST7-FD (18) (top5_1103);
  CWT13-z05-long (193), MF4-FD (38), NM-HL-T75 (38), NM-AR-AM (15) (top5_1102).
- **Out - not coverable by the gates1021 harness:** CWT05-flush-m05-v3-long (28; needs 09:35-09:45 head rows),
  intraday_momentum (19; classic, no lab mask).
- **Out - Graveyard now:** NS5-sma50-flush-oversold-long-FD (10, since 11-04).
- **Scored (next eligible by live count):**
  1. MF5-flowsell-vwapup-rsi5hi (23, T1 + T2 split copies; first top-5 tune of the base version; the -FD copy was tuned
     top5_1022 / top5_1030). t1s1 short, 09:50-15:00, ADV >= $95M, no refire.
  2. L3-gap-slope-rsi5hi-FD (14, Primary; last tuned top5_1030). t05s1 short, 09:50-15:00, refire cd 6.
  3. NS1-rsidip-rsi5pop-long-FD (11, T1; last tuned top5_1030). t05s1 long, 09:50-15:00, ADV >= $95M, refire cd 3.
  4. NS5-sma50-flush-oversold-long (11, Primary; first top-5 tune). t1s1 long, 09:50-11:30, ADV >= $95M, no refire.
  5. NS3V1-am-widestop-short (10, T2; last tuned top5_1030). NS3 signal, 09:50-11:30, live R = 0.5 ATR, target 0.25
     ATR (= stop 2 / target 1 in 0.25-ATR units; parity row P0 on the cache geometry t05s1, not counted), refire cd 1.
  Two of the five are Primary setups: a variant can at most be an additional Testing / low-rep setup; the Primary setup
  stays unchanged without the owner.

## 2. Harness, data, costs, splits (unchanged from top5_1104)
- Data: 2-year lab frames per `research/bdi/1104/DATA.md` (frames to 2026-11-04), read from /home/user/MCF.
- Entries: gates1021 live-shaped signal rows rebuilt by `build_cache.py` (to /dev/shm). Exits: the top5_1028
  simulator, unchanged; 0.25-ATR units; r divided by the stop multiple (same $ risk).
- **Parity gate:** each parent's simulated R must equal the cached production R (mean |d| < 0.002R); NS3V1 on P0.
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16 onward) dropped, scored once only for a Testing candidate.
- Random control = gates1021 same-minute random entry at the parent geometry (NS3V1: c_short_t1s1, no exact t1s2
  column, disclosed as on 10-30).

## 3. Grid (one knob per row, relative to each parent; every row counts)
| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / x2.0 (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | earlier partial: half off at 0.5 x target distance, stop to break-even |
| G06 | clock exit (trades opened before it): MF5 / L3-rsi5hi-FD / NS1-FD 14:00; NS5 / NS3V1 12:00 |
| G07 | time stop 60 min if best < +0.25R |
| G08 | limit entry 0.1R better, valid one bar |
| G09 | enter on the next bar's close (entry timing) |
| G10 | index veto: shorts skip SPY up > 0.5% from open; longs skip SPY down > 0.5% |
| G11 | first part of the window: MF5 / L3-rsi5hi-FD / NS1-FD < 11:30; NS5 / NS3V1 <= 10:30 |
| G12 | the rest: MF5 / L3-rsi5hi-FD / NS1-FD >= 11:30; NS5 / NS3V1 > 10:30 |
| G13 | skip when the stock is down > 2% from the open |
| G14 | SPY-side filter: shorts skip SPY above its open, longs skip SPY below it |
| G15 | session cap: first 5 signals per session |
| G16 | CF cost filter as live in Testing since 10-30: skip if (2 x (1c + 1 bps) + 2c) / R > 0.15 at the parent stop |
| G17 | skip when SPY is within +/-0.10% of its open at the signal |
| G18 | **new, from tonight's top-20 two-year reads** (CWT09-vwaploss price < $20 -0.85R both splits; 8 of 10 setups lost there on 11-04): skip price < $20 |

**Total N = 18 x 5 = 90.** Setup bar (beats parent) = paired day-clustered t >= max(1.5, sqrt(2 ln 18)) = 2.40 with
d > 0 in TRAIN and VALID. Study bar max(1.5, sqrt(2 ln 90)) = 3.00 also reported.

**Testing bar (rule 22 BAR90):** beats parent; exp > 0 in TRAIN and VALID; day-clustered TRAIN+VALID t >= 0.9 x
max(1.5, sqrt(2 ln N_lineage)); walk-forward positive months >= 54%; up and down sessions > 0; avg R without the best
day > 0; beats random. Lineage N, conservative (may double count):
- L3-rsi5hi-FD: 274,339 (top5_1030) + 18 = 274,357 -> BAR90 4.50.
- NS3V1: 163,093 (top5_1030) + 18 = 163,111 -> BAR90 4.41.
- MF5 / NS1-FD / NS5: discovery count unrecorded, so the largest backlog lineage (934,970) + earlier grids + 18
  -> ~935,063 / 935,063 / 934,988 -> BAR90 4.72.

## 4. Part A (descriptive, tunes nothing, not in N)
Tonight's Part A deep set is the 3 top-20 setups not read in depth on 11-03 / 11-04 (CWT09-gapdn-vwaploss-g5-short,
CWT09-gapdn-bounce-g5-lowerhalf-short, NM-HL-T75-pm-long) plus CWT13-vwapstretch-z075-short's two-year read completed
(22 of 22 months; 11 on 11-04). No sizing checks are declared tonight.
