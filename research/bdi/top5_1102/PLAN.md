# top5_1102 pre-declaration: execution variants of the top live setups (thirteenth run)

*Educational only - not financial advice.*

Written 2026-11-02 (after the close) after the live ranking (`live_rank.py`, live paper trades only), **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-27, 10-28, 10-29, 10-30, 11-02 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-*
out, "-FD" copies are their own setup.

Rule changes in effect inside this window (research/ledger.jsonl): GX1 5-minute clock gate (from 10-27); Primary
per-setup -2R daily stop (from 10-28); Setup Generator paused after 10-28; Testing 1/2 CF cost filter, skip if
stop-exit cost > 0.15R (from 10-30); moves: pdl-p05 / p05-lowvol -> Graveyard (10-30), L3-rsi5hi-FD and
L3-fromopen-FD -> Primary (10-30), PDL-1a R2A legs into Testing 2 (10-30), NS3-FD + RW4-FD -> Graveyard (11-01),
MF3-FD + MF5-FD -> Graveyard (11-02), R2A scale-out cap exemption (11-02).

- **Out - rotated, pdl lineage exhaustively tuned (pdl1030 / b / c, 245 configs, 0 pass):** CWT14-failbrk-pdl-p05-long
  (233), p10 (160), p05-lowvol (156), p10-lowvol (97), CWT14-failbrk-pdl-p05-R2A-long (19; same signal lineage, owner
  forward observation).
- **Out - Graveyard:** CWT12-coil-k4-long (150), MF3-FD (43), MF5-FD (31), RW4-FD (25), NS3-FD (19).
- **Out - tuned in the last 3 runs (top5_1030, swarm15_1029 / p1_1029, top5_1028), no setup/exit change since:**
  RW7-FD (94), exhaustion_short-FD (62), L3-fromopen-FD (52), L3-rsi5hi-FD (23), NS3V1 (19), RW5-FD (18), RW1-FD (18),
  NS1-FD (14). MF5-flowsell-vwapup-rsi5hi (17, T1): same signal as MF5-FD (tuned 10-30, 15 configs incl. its window
  cuts; Graveyard 11-02) inside a sub-window -> treated as tuned. intraday_momentum (14): classic, no lab kernel.
- **Scored:**
  1. CWT13-vwapstretch-z05-long (85, T2) - **first history kernel**: `cwt_live_lib.b2(z=0.5, long)` on the lab frame
     plus the 09:35-09:45 head rows (refire1014 head_rows, as research/bdi/cwt/live/verify.py), window 11:00-15:00,
     ADV >= 95M, first signal per symbol-day, t05s1. Parity gate: n and exp vs `cwt/live/verify.json`
     (18,135 trades, -0.0796R over all open months) and sim R = production R per trade.
  2. NM-HL-T75-pm-long (35, T2; first tune). t05s1 long, 13:00-15:00, ADV >= 125M, no refire.
  3. exhaustion_short (18, T1; last tuned top5_1027). t1s1 short, 13:00-15:00, refire cd 1.
  4. MF4-h40-open-flowsell-FD (15, Primary; last tuned top5_1026). t05s1 short, 09:50-15:00, no refire.
  5. NM-AR-AM-gapdown-capitulation-long (15, T2; last tuned top5_1027; NM-mined on this history = in-sample).
     t1s1 long, 09:50-11:00, no refire.
  A variant can at most be an **additional Testing setup**; MF4-FD stays in Primary unchanged without the owner.

## 2. Harness, data, costs, splits
- Entries 2-5: gates1021 live-shaped signal rows (live module, window, ADV, refire chain) rebuilt to scratch by
  `build_cache.py`. Entry 1: the CWT13 kernel above, computed per month inside `scan_1102.py`.
- Exits: the top5_1028 simulator, unchanged (stop first, limit-entry mode, clock exit only for trades opened before it,
  costs x3 on the extended tier), in 0.25-ATR units; r divided by the stop multiple (same $ risk).
- **Parity gate:** each parent's simulated R must equal the production R (mean |d| < 0.002R) before a variant is read.
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16 onward) dropped, scored once only for a Testing candidate.
- Random control = gates1021's same-minute random entry (ADV >= 95M) at the parent geometry (c_{side}_{geom}).

## 3. Grid (one knob per row, relative to each parent; every row counts)
| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / x2.0 (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | earlier partial: half off at 0.5 x target distance, stop to break-even |
| G06 | clock exit (trades opened before it): MF4-FD / NM-AR-AM 12:00, CWT13 14:00, NM-HL / exhaustion_short 14:30 |
| G07 | time stop 60 min if best < +0.25R |
| G08 | limit entry 0.1R better, valid one bar |
| G09 | enter on the next bar's close (entry timing) |
| G10 | index veto: shorts skip SPY up > 0.5% from open; longs skip SPY down > 0.5% |
| G11 | first half of the window only: CWT13 <= 13:00, NM-HL / exhaustion_short <= 14:00, MF4-FD < 11:30, NM-AR-AM < 10:30 |
| G12 | second half only: CWT13 > 13:00, NM-HL / exhaustion_short > 14:00, MF4-FD >= 11:30, NM-AR-AM >= 10:30 |
| G13 | skip when the stock is down > 2% from the open |
| G14 | exhaustion_short (refire): one entry per symbol per session; the others (no refire, G14 would be a no-op): SPY-side filter, longs skip SPY below its open, shorts skip SPY above it |
| G15 | session cap: first 5 signals per session (recurring live pattern: 21-55 same-day CWT13 trades on 10-30 / 11-02, 24 NM-HL on 11-02) |
| G16 | CF cost filter as live in Testing since 10-30: skip if (2 x (1c + 1 bps) + 2c) / R > 0.15 at the parent stop |

**Total N = 16 x 5 = 80.** Setup bar (beats parent) = paired day-clustered t >= max(1.5, sqrt(2 ln 16)) = 2.35 with
d > 0 in TRAIN and VALID. Study bar max(1.5, sqrt(2 ln 80)) = 2.96 also reported.

**Testing bar (rule 22 BAR90):** beats parent; exp > 0 in TRAIN and VALID; day-clustered TRAIN+VALID t >= 0.9 x
max(1.5, sqrt(2 ln N_lineage)); walk-forward positive months >= 54%; up and down sessions > 0; avg R without the best
day > 0; beats random. Lineage N (earlier lineage count + earlier top-5 grids + 16 tonight):
- CWT13: swarm1017-rework-cwt-family 115,242 + package B B2 64 + 16 = 115,322 -> full 4.83, BAR90 4.35.
- NM-HL-T75: swarm1017 bar 4.57 (misc-heatlong-pm-strict 34,000) + 16 = 34,016 -> 4.57, BAR90 4.11.
- exhaustion_short: bdi-tg-exhaustion-short 856,048 + 18 (top5_1027) + 16 = 856,082 -> 5.23, BAR90 4.71.
- MF4-FD: MarcoFlow discovery count unrecorded; the largest backlog lineage (934,970) + 18 (top5_1026) + 16 =
  935,004 -> 5.24, BAR90 4.72.
- NM-AR-AM: swarm1017 arena-am-long-gapdown-capitulation 43,340 + 18 (top5_1027) + 16 = 43,374 -> 4.62, BAR90 4.16.
