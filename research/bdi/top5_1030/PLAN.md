# top5_1030 pre-declaration: execution variants of the top live setups (twelfth run)

*Educational only - not financial advice.*

Written 2026-10-30 (after the close) after the live ranking (`live_rank.py`, live paper trades only), **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-26..10-30 (5). Primary + Testing 1 + Testing 2 reports, run_id 1, S6 and GEN-* out, "-FD" copies are
their own setup. Membership from `docs/live/assignments.json` / config at HEAD.

- **Out - rotated (exhaustively tuned today, pdl1030 / 1030b / 1030c, 245 configs, 0 pass):** CWT14-failbrk-pdl-p05-long
  (257), pdl-p05-lowvol (172), pdl-p10 (147), pdl-p10-lowvol (88). The two p05 rows are Graveyard from 10-30.
- **Out - Graveyard:** CWT12-coil-k4-long (202).
- **Out - tuned in the last 3 runs (top5_1027 / 1028 / 1029 = swarm15_1029 + p1_1029), no setup/exit change since:**
  RW7-FD (106; 1028, swarm15), L3-fromopen-FD (90; swarm15; re-promoted to Primary 10-30 = account move only),
  exhaustion_short-FD (65; 1028), MF3-FD (40; 1028), exhaustion_short (33; 1027), RW4-FD (26; 1028),
  L3-lowdist-FD (21; 1027), RW1-FD (19; 1028), RW5-FD (18; p1_1029).
- **Cannot be backtested:** CWT13-vwapstretch-z05-long (75, T2) - no CWT13 kernel in the history harness (fifth run).
- **Scored (next eligible by live count):**
  1. L3-gap-slope-rsi5hi-FD (39, Primary from 10-30 / T2 before; last tuned top5_1026). t05s1 short, refire cd 6.
  2. MF5-flowsell-vwapup-rsi5hi-FD (24, T2; last tuned top5_1022). t1s1 short, no refire.
  3. NS3-failed-vwap-reclaim-short-FD (20, T2; last tuned top5_1026). t1s1 short, refire cd 1.
  4. NS3V1-am-widestop-short (16, T2; first tune). NS3 signal, 09:50-11:30, R = 0.5 ATR, t05s1 (= stop 2 / target 1
     in 0.25-ATR units), refire cd 1.
  5. NS1-rsidip-rsi5pop-long-FD (14, T1; first top-5 tune). t05s1 long, refire cd 3.
  (MF4-FD also had 14 live trades; NS1-FD is taken as the first not-yet-tuned setup at that count.)
  A variant can at most be an **additional Testing setup**; L3-rsi5hi-FD stays in Primary unchanged without the owner.

## 2. Harness, data, costs, splits
- Entries: gates1021 live-shaped signal rows (live module, window, ADV, refire chain) rebuilt to scratch by
  `build_cache.py` for the 5 setups. Exits: the top5_1028 simulator (stop first, limit-entry mode, clock exit only for
  trades opened before it, costs x3 on the extended tier), in 0.25-ATR units; R per row = stop distance at the same $.
- **Parity gate:** each setup's simulated cache geometry must equal the cache's production R (mean |d| < 0.002R) before
  any variant is read. NS3V1: the cache stores t05s1 at R = 0.25 ATR, so parity is checked on that geometry (row P0,
  not counted) and the parent is the live geometry (stop 0.5 ATR, target 0.25 ATR).
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier.
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16..10-07) dropped, scored once only for a Testing candidate.
- Random control = the cache's same-minute random entry at the parent geometry (NS3V1 has no exact column: t1s1 used,
  disclosed).

## 3. Grid (one knob per row, relative to each parent; every row counts)
| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / x2.0 (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | earlier partial: half off at 0.5 x target distance, stop to break-even |
| G06 | clock exit 12:00 (trades opened before it) |
| G07 | time stop 60 min if best < +0.25R |
| G08 | limit entry 0.1R better, valid one bar |
| G09 | enter on the next bar's close (entry timing) |
| G10 | index veto: shorts skip SPY up > 0.5% from open; the long skips SPY down > 0.5% |
| G11 | window end 11:30 (NS3V1: window start 10:30) |
| G12 | window start 11:30 (NS3V1: window end 10:30) |
| G13 | skip when the stock is already > 2% against the trade from the open (shorts: down > 2%; long: down > 2%) |
| G14 | re-entry cooldown: one entry per symbol per session |
| G15 | session cap: first 5 signals per session (recurring live pattern: 13-16 same-day losers on 10-27 / 10-28) |

**Total N = 15 x 5 = 75.** Setup bar (beats parent) = paired day-clustered t >= max(1.5, sqrt(2 ln 15)) = 2.33 with
d > 0 in TRAIN and VALID.

**Testing bar (rule 22 BAR90):** beats parent; exp > 0 in TRAIN and VALID; day-clustered TRAIN+VALID t >= 0.9 x
max(1.5, sqrt(2 ln N_lineage)); walk-forward positive months >= 54%; up and down sessions > 0; avg R without the best
day > 0; beats random. Lineage N (backlog configs_tried + earlier grids + 75): L3-rsi5hi-FD 274,339 -> 4.50; NS3-FD /
NS3V1 (ns3var1022 lineage bar 4.90, N ~163k) -> 4.41; MF5-FD / NS1-FD (MarcoFlow discovery count not recorded; the
largest lineage in the backlog, 934,970, is used) -> 4.72. Study bar max(1.5, sqrt(2 ln 75)) = 2.94 also reported.
