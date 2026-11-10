# top5_1106 pre-declaration: execution variants of the top live setups (seventeenth run)

*Educational only - not financial advice.*

Written 2026-11-06 (after the close) after the live ranking (`live_rank.py`, live paper trades only) and the Part A
live / two-year bucket reads, **before any history configuration below was scored**. Results go in `NOTES.md`; this
file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-11-02, 11-03, 11-04, 11-05, 11-06 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-*
out, "-FD" copies are their own setup. Last 3 runs = top5_1105, top5_1104, top5_1103.

Rule changes in effect inside this window (research/ledger.jsonl effective dates): R2A legs into Testing 2 and the R2A
scale-out cap exemption (11-02 / 11-03); NS3-FD + RW4-FD -> Graveyard (11-02); MF3-FD + MF5-FD -> Graveyard (11-03);
RW3S-FD into Testing 2 (11-03); NS5-FD / ST4-FD / RW6G1-FD -> Graveyard and the UNI1 top-500 pool in Testing 2 (11-04);
ROLL1: low-rep setups move to Explore 1 / Live Lab (11-05). Already in force for the whole window: CF cost filter in
Testing 1/2 + BAR90 (10-30), Primary ~$4k (10-28), Primary -2R per-setup latch (10-29). 11-05 was a SPY -4.2% session;
11-06 a quiet session (SPY +0.07%) with a 10:41-10:51 squeeze. No setup / exit change on 11-06.

- **Out - pdl lineage exhaustively tuned (pdl1030/b/c):** CWT14-failbrk-pdl-p10 (131), p05-R2A-long (110),
  p10-lowvol (79), p05-R2A-short (13).
- **Out - tuned in the last 3 runs, no setup/exit change since:** RW3S-FD (140), RW1-FD (26), exhaustion_short-FD (31),
  ST7-FD (12), L3-lowdist-FD (15) (top5_1103); RW7-FD (107), MF2-FD (62), RW3-FD (31), RW5-FD (26), L3-fromopen-FD
  (top5_1104); NS3V1 (26), MF5 (25), NS1-FD (20), L3-rsi5hi-FD (13), NS5 (top5_1105). MF2-FD also had BURST2 / bdi1106
  remedy tests tonight and is under DM-MF2.
- **Out - not coverable by the gates1021 harness:** CWT05-flush-m05-v3-long (25), intraday_momentum (18).
- **Scored (next eligible by live count):**
  1. CWT13-vwapstretch-z05-long (143, T2; last tuned top5_1102, four runs ago; no change since). Kernel from top5_1102
     (`cwt_live_lib.b2(z=0.5, long)` + head rows, 11:00-15:00, ADV >= 95M, first per symbol-day), t05s1.
  2. MF4-h40-open-flowsell-FD (51, Primary; last tuned top5_1102; DM-MF4 pending). t05s1 short, 09:50-15:00.
  3. NM-HL-T75-pm-long (31, T2; last tuned top5_1102). t05s1 long, 13:00-15:00, ADV >= 125M.
  4. exhaustion_short (26, T1; last tuned top5_1102). t1s1 short, 13:00-15:00, refire cd 1.
  5. NS3-failed-vwap-reclaim-short (15, T1; first top-5 tune of the base version; its -FD copy was tuned top5_1030 and
     ns3var1022). t1s1 short, 09:50-11:30, no refire.
  MF4-FD is a Primary setup: a variant can at most be an additional Testing setup; the Primary setup stays unchanged.

## 2. Harness, data, costs, splits (unchanged from top5_1102 / top5_1105)
- Data: 2-year lab frames per `research/bdi/1104/DATA.md` (frames to 2026-11-04), read from /home/user/MCF.
- Entries 2-5: gates1021 live-shaped signal rows rebuilt by `build_cache.py` (to /dev/shm/t5_1106/g). Entry 1: the
  CWT13 kernel computed per month inside `scan_1106.py`. Exits: the top5_1028 simulator, unchanged; 0.25-ATR units;
  r divided by the stop multiple (same $ risk).
- **Parity gate:** each parent's simulated R must equal the cached production R (mean |d| < 0.002R).
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16 onward) dropped, scored once only for a Testing candidate.
- Random control = gates1021 same-minute random entry at the parent geometry (c_{side}_{geom}).

## 3. Grid (one knob per row, relative to each parent; every row counts)
New vs top5_1102 on the same setups: tighter stop (G02), 30-min time stop (G06), flush-chase guard (G13), price < $20
(G15), ADV threshold +20% (G18). The rest repeat the standard knobs because the frames are now ~19 sessions longer.

| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / **x0.75** (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | earlier partial: half off at 0.5 x target distance, stop to break-even |
| G06 | **time stop 30 min** if best < +0.25R |
| G07 | time stop 60 min if best < +0.25R |
| G08 | clock exit (trades opened before it): CWT13 14:00, MF4-FD 12:00, NM-HL / exhaustion_short 14:30, NS3 11:00 |
| G09 | limit entry 0.1R better, valid one bar |
| G10 | enter on the next bar's close (entry timing) |
| G11 | first part of the window: CWT13 <= 13:00, MF4-FD < 11:30, NM-HL / exhaustion_short <= 14:00, NS3 < 10:30 |
| G12 | the rest: CWT13 > 13:00, MF4-FD >= 11:30, NM-HL / exhaustion_short > 14:00, NS3 >= 10:30 |
| G13 | **flush-chase guard** (FB1 forward lead; 11-06 live near-LOD shorts -0.495R n 88 vs rest +0.195R): shorts skip entry-bar `dist_lod_atr <= 0.15`; longs (mirror) skip `dist_hod_atr <= 0.15` |
| G14 | CF cost filter as live in Testing: skip if (2 x (1c + 1 bps) + 2c) / R > 0.15 at the parent stop |
| G15 | skip price < $20 (top-20 two-year reads: losing bucket in both splits for 5 of tonight's 7 deep setups) |
| G16 | SPY-side filter: shorts skip SPY above its open, longs skip SPY below it |
| G17 | session cap: first 5 signals per session (CWT13 100 trades on 11-05) |
| G18 | exhaustion_short (refire): re-entry cooldown = one entry per symbol per session; the others: ADV floor x1.2 (threshold +20%: 114M; NM-HL 150M) |

**Total N = 18 x 5 = 90.** Setup bar (beats parent) = paired day-clustered t >= max(1.5, sqrt(2 ln 18)) = 2.40 with
d > 0 in TRAIN and VALID. Study bar max(1.5, sqrt(2 ln 90)) = 3.00 also reported. Random entries: each row's
same-minute random control is reported next to it.

**Testing bar (rule 22 BAR90):** beats parent; exp > 0 in TRAIN and VALID; day-clustered TRAIN+VALID t >= 0.9 x
max(1.5, sqrt(2 ln N_lineage)); walk-forward positive months >= 54%; up and down sessions > 0; avg R without the best
day > 0; beats random. Lineage N (conservative, earlier lineage + earlier top-5 grids + 18 tonight):
- CWT13: 115,322 (top5_1102) + 18 = 115,340 -> BAR90 4.35.
- NM-HL-T75: 34,016 + 18 = 34,034 -> BAR90 4.11.
- exhaustion_short: 856,082 + 18 = 856,100 -> BAR90 4.70.
- MF4-FD: 935,004 + 18 = 935,022 -> BAR90 4.72.
- NS3 base: ns3var1022 lineage (~163k, as NS3V1) + 18 -> BAR90 4.41.

## 4. Part A (descriptive, tunes nothing, not in N)
Deep set tonight: the 7 top-20 setups whose last deep read is oldest or never: NS1-rsidip-rsi5pop-long (new to the top
20), NM-MF3-qqqdn-gapdn-FD, NS4-pm-vwap-reclaim-oversold-short-FD, L3-gap-slope-lowdist-FD, RW1-gapdn-bounce-flowsell-
short-FD, ST7-rsi50dn-long-pm-t1s1-FD (all last deep 11-03) and MF2-open-rsimidhi-flowsell-FD (last deep 11-04; DM-MF2
pending). All 20 read live.
