# top5_1104 pre-declaration: execution variants of the top live setups (fifteenth run)

*Educational only - not financial advice.*

Written 2026-11-04 (after the close) after the live ranking (`live_rank.py`, live paper trades only), **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-29, 10-30, 11-02, 11-03, 11-04 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-*
out, "-FD" copies are their own setup. Last 3 runs = top5_1103, top5_1102, top5_1030.

Rule changes in effect inside this window (research/ledger.jsonl effective dates): Primary per-setup -2R daily stop
(10-29); Setup Generator paused after 10-28; CF cost filter in Testing 1/2 (10-30); moves: pdl-p05 / p05-lowvol ->
Graveyard (10-30), L3-rsi5hi-FD and L3-fromopen-FD -> Primary (10-30), R2A legs into T2 (11-02), NS3-FD + RW4-FD ->
Graveyard (11-02), MF3-FD + MF5-FD -> Graveyard (11-03), R2A cap exemption (11-03), RW3S-FD into Testing 2 (11-03),
NS5-FD / ST4-FD / RW6G1-FD -> Graveyard (11-04), UNI1 top-500 pool in Testing 2 (11-04). Just before: Primary size ~$4k
(10-28). After the window: ROLL1 Explore 1 / Live Lab low-rep homes (11-05).

- **Out - pdl lineage exhaustively tuned (pdl1030/b/c):** CWT14-failbrk-pdl-p10 (118), p10-lowvol (81), p05 (57),
  p05-lowvol (49), p05-R2A (39).
- **Out - tuned in the last 3 runs, no setup/exit change since:** CWT13-z05-long (97), NM-HL-T75 (35), MF4-FD (27),
  NM-AR-AM (15), exhaustion_short (top5_1102); RW3S-FD (51), exhaustion_short-FD (37), RW1-FD (18), ST7-FD (17),
  L3-lowdist-FD (top5_1103); L3-rsi5hi-FD (24), MF5 (25), NS1-FD (15) (top5_1030).
- **Out - Graveyard:** MF3-open-flowsell-rsi5hi-FD (20, since 11-03), MF5-FD (14).
- **Out - no lab kernel / not covered by the gates1021 harness:** intraday_momentum (19, classic), CWT05-flush-m05-v3-long
  (16, `covered=False`).
- **Scored (all t1s1 short unless noted, 09:50-15:00):**
  1. RW7-gapdn-bounce-early-short-FD (63, T1; last tuned swarm15_1029).
  2. L3-gap-slope-fromopen-FD (49, Primary + T1; last tuned swarm15_1029; no ADV floor).
  3. RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (26, Primary; last tuned p1_1029).
  4. RW3-gapdn-rsi5pop-flowsell-short-FD (20, Primary; last tuned p1_1029).
  5. MF2-open-rsimidhi-flowsell-FD (16, Primary; t1s05 = target 2R / stop 1R; last tuned p1_1029 / top5_1026).
  Four of the five are Primary setups: a variant can at most be an additional Testing / low-rep setup; the Primary
  setup stays unchanged without the owner.

## 2. Harness, data, costs, splits (unchanged from top5_1103)
- Data: the 2-year lab frames rebuilt tonight by the BDI daily agent (`research/bdi/1104/DATA.md`; frames now run to
  2026-11-04, ~19 sessions longer, which only adds HOLD rows).
- Entries: gates1021 live-shaped signal rows rebuilt by `build_cache.py` (to /dev/shm).
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
| G06 | clock exit (trades opened before it): RW7-FD / RW5-FD / RW3-FD 14:00; L3-fromopen-FD / MF2-FD 14:30 |
| G07 | time stop 60 min if best < +0.25R |
| G08 | limit entry 0.1R better, valid one bar |
| G09 | enter on the next bar's close (entry timing) |
| G10 | index veto: shorts skip SPY up > 0.5% from open |
| G11 | first part of the window: RW5-FD < 11:30; RW7-FD / L3-fromopen-FD / RW3-FD / MF2-FD <= 13:00 |
| G12 | the rest: RW5-FD >= 11:30; the others > 13:00 |
| G13 | skip when the stock is down > 2% from the open |
| G14 | SPY-side filter: shorts skip SPY above its open |
| G15 | session cap: first 5 signals per session |
| G16 | CF cost filter as live in Testing since 10-30: skip if (2 x (1c + 1 bps) + 2c) / R > 0.15 at the parent stop |
| G17 | skip when SPY is within +/-0.10% of its open at the signal |
| G18 | **new, from tonight's top-20 live buckets** (L3-fromopen-FD struggles at price >= $150, -0.14R n 39; L3-lowdist the same): skip price >= $150 |

**Total N = 18 x 5 = 90.** Setup bar (beats parent) = paired day-clustered t >= max(1.5, sqrt(2 ln 18)) = 2.40 with
d > 0 in TRAIN and VALID. Study bar max(1.5, sqrt(2 ln 90)) = 3.00 also reported.

**Testing bar (rule 22 BAR90):** beats parent; exp > 0 in TRAIN and VALID; day-clustered TRAIN+VALID t >= 0.9 x
max(1.5, sqrt(2 ln N_lineage)); walk-forward positive months >= 54%; up and down sessions > 0; avg R without the best
day > 0; beats random. Lineage N, conservative (may double count):
- RW7-FD: 83,044 (swarm15_1029) + 18 = 83,062 -> BAR90 4.28.
- L3-fromopen-FD: 274,284 (swarm15_1029) + 18 = 274,302 -> BAR90 4.50.
- RW5-FD / RW3-FD / MF2-FD: discovery count unrecorded, so the largest backlog lineage (934,970) + earlier grids
  (top5_1023 18 / 17, top5_1026 17, p1_1029 10 each) + 18 -> ~935,016 / 935,015 / 935,015 -> BAR90 4.72.

## 4. Part A sizing checks (research/bdi/top20/sizing_check.py, counted in the study N)
Half size in the live "struggles" condition, only where it is point-in-time and the 2-year frame can see it; scored on
TRAIN and VALID, bar max(1.5, sqrt(2 ln k)) for k checks. Declared after the live read, before any 2-year read of
these setups:
- S1 MF4-h40-open-flowsell-FD: half size when SPY is within +/-0.10% of its open at entry.
- S2 RW7-gapdn-bounce-early-short-FD: half size when SPY is within +/-0.10% of its open at 10:00.
- S3 NS4-pm-vwap-reclaim-oversold-short: half size when ATR% is 2-3.5.
- S4 MF3-open-flowsell-rsi5hi: half size for entries 09:50-10:30.
- S5 exhaustion_short: half size when SPY is below its open at 10:00 (by more than 0.10%).
k = 5 -> bar 1.79.
