# top5_1121 pre-declaration: execution variants of the top live setups (twentieth run)

*Educational only - not financial advice.*

Written 2026-11-21 (Saturday, weekly run) after the live ranking (`live_rank.py`, live paper trades only), the Part A
live bucket reads and while the signal cache was being built (signal times only, no R read), **before any history
configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-11-16..11-20 (5). Primary + On Deck (`testing`, old Testing 1) + Testing A (`testing2`, old Testing 2)
journals, run_id 1, R on the LR8 cost basis (`fetch_live.py`, the `mcf.report.footrace.live_trades` reader with the
extra columns kept), S6 and GEN-* out, "-FD" and "-WBn" copies are their own setup. Last 3 runs = top5_1110,
top5_1109, top5_1106 (no top-5 run between 11-11 and 11-20).

- **Out - pdl lineage exhaustively tuned (pdl1030/b/c):** CWT14-failbrk-pdl-p05-R2A-long (297), -p10-long (192),
  -p05-R2A-short (129).
- **Out - tuned in the last 3 runs, no setup / exit change since** (moves and the LR8 cost basis are not setup changes):
  RW1-FD (103, top5_1109), L3-fromopen-FD (70, top5_1110), CWT13-z05-long (63, top5_1106), MF4-FD (51, top5_1106),
  MF2-FD (48, top5_1110), exhaustion_short-FD (45, top5_1109), RW3-FD (43) and RW5-FD (34) (top5_1110), NM-AR-AM (21,
  top5_1109). Remedy-Q (a) 12:30 cut-off copies of the Primary trio start 11-23 as separate Testing copies; parents
  unchanged.
- **Out - Workbench copies (MF2-FD-WB3 28, L3-fromopen-FD-WB4 27):** brand-new setups (ledger 11-19 "tweaked copies"),
  their WB exits (75-minute close, WB3 knobs) are not modelled by the gates1021 harness, and C3-WB forbids tunes of a
  losing 100+-trade parent's copy (MF2-FD).
- **Out - not coverable by the gates1021 harness:** NM-ETF-late-dip-di-long (24, Primary from 11-11; not in the harness'
  setup list).
- **Scored (next eligible by live count):**
  1. MF4-h40-open-flowsell (47, Testing A; **first top-5 tune**; Primary until 11-10, TEAM-6). t05s1 short, 09:50-11:00, ADV >= $95M.
  2. NM-MF3-qqqdn-gapdn-FD (33, Testing A; **first top-5 tune**). t1s1 short, 09:50-15:00, ADV >= $95M, QQQ context.
  3. NS3V1-am-widestop-short (31, Testing A; last tuned top5_1105). Live stop 0.5 ATR, target 0.25 ATR (units up 1 / dn 2), 09:50-11:30, refire.
  4. L3-gap-slope-rsi5hi-FD (29, On Deck; last tuned top5_1105). t05s1 short, 09:50-15:00, refire cd 6, no ADV floor.
  5. NS5-sma50-flush-oversold-long (22, On Deck + Primary until 11-18; last tuned top5_1105). t1s1 long, 09:50-11:30.
  None is a Primary setup now. A winner can at most be proposed as an **additional Testing setup**.

Rule changes in effect inside the Part B window (research/ledger.jsonl effective dates): TSZ1 testing half-size lots +
2x slots + cap 100 (11-17; R comparable, $ not), Workbench copies added (11-17), SPYEXIT engine (11-17, used only by
WB4 copies), GY-BENCH + guests (11-18), NS5 Primary -> On Deck (C3-NS5, 11-19), C3-EXIT100 / ROT2 / U9-TGT quote check /
U9-ETB borrow list (11-19), ultimate_1119 admissions (11-20), stop rounding direction + ROT block 2 (11-20). Already in
force: LR8 cost model (11-12; all R here re-priced on LR8), On Deck split-tape short gate off + caps raised + Testing A
full universe (11-12). After the window: burst brake + watchdog act (11-23), ST7 Primary -> On Deck (11-23), Remedy-Q
copies (11-23).

## 2. Harness, data, costs, splits (unchanged from top5_1110)
- Data: 2-year lab frames per `research/bdi/1104/DATA.md` (frames to 2026-11-04).
- Entries: gates1021 live-shaped signal rows rebuilt by `build_cache.py` (to /dev/shm/t21/g); config and modules of
  the 5 setups are byte-identical between the harness checkout and HEAD (only `former_primary` metadata differs).
  Exits: the top5_1028 simulator, unchanged; 0.25-ATR units; r divided by the stop multiple (same $ risk).
- **Parity gate:** each parent's simulated R must equal the cached production R (mean |d| < 0.002R). NS3V1 is checked on
  its cache geometry (row P0, t05s1 at 1 unit; not counted), as in top5_1105.
- Costs: entry 1c + 1 bps x time-of-day multiplier; target limits free; stops +2c; market exits 1c + 1 bps; x3 on the
  extended tier. (Backtest cost model, not LR8; LR8 is used for live rows only.)
- Locked block 2024-11-01..2025-02-28 never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07..09-15; HOLD
  (2026-04..06, 2026-09-16 onward) dropped, scored once only for a Testing candidate.
- Random control = gates1021 same-minute random entry at the parent geometry (NS3V1 and t05s1 setups: the nearest
  column, disclosed in results).
- Compass on history (G17 / G18): W60 15-min compass from `research/bdi/top20/compass_2y.py`.

## 3. Grid (one knob per row, relative to each parent; every row counts): 21 x 5 = **105 configurations**
| id | knob |
|---|---|
| G01 / G02 | stop x1.5 / x0.75 (same $, target price unchanged) |
| G03 / G04 | target x0.75 / x1.5 |
| G05 | half off at 0.5 x target distance, stop to break-even |
| G06 / G07 | time stop 30 / 60 min if best < +0.25R |
| G08 | clock exit: 12:00 for the morning-window setups (MF4, NS3V1, NS5), 13:00 for NM-MF3 / L3-rsi5hi |
| G09 | limit entry 0.1 x stop better |
| G10 | next-bar entry |
| G11 / G12 | window halves: MF4 < 10:15 / >= 10:15; NS3V1 / NS5 <= 10:30 / > 10:30; NM-MF3 / L3-rsi5hi < 12:30 / >= 12:30 (the Remedy-Q 12:30 cut-off, as a per-setup knob) |
| G13 | CF: est. round-trip cost <= 0.15 x stop $ |
| G14 | skip price < $20 |
| G15 | first 5 per session |
| G16 | SPY side filter (shorts: SPY not above its open at signal; long NS5: SPY not below) |
| G17 | skip against a confirmed compass |
| G18 | half size against a confirmed compass (sizing, same trades) |
| G19 | ADV floor x1.2 (114M); L3-rsi5hi (no floor) -> ADV >= 95M |
| G20 | re-entry cooldown: first signal per symbol-day only |
| G21 | **loser pattern as opportunity** (from Part A / the live read, one per setup): MF4 skip price >= $150 (live -0.34R n 16); NM-MF3 skip DOWN-confirmed compass (78% of live losing R on 57%); NS3V1 skip entries before 10:00 (live -0.26R n 7); L3-rsi5hi skip SPY below its open by > 0.10% at signal (live at 10:00 -0.33R n 33); NS5 skip SPY below its open by > 0.5% (index veto) |

- Beats parent: d R per parent signal > 0 in TRAIN and in VALID, and day-clustered t of the improvement >=
  max(1.5, sqrt(2 ln 21)) = 2.47 (per setup); study-wide N = 105 -> 3.05 reported too.
- **Testing bar (rule 22, BAR90):** beats parent, exp > 0 in TRAIN and VALID, day-clustered t (TRAIN+VALID) >=
  0.9 x max(1.5, sqrt(2 ln N_lineage)), WF >= 54% positive months, up and down sessions > 0, positive without the best
  day, beats random entries. Lineage N (conservative, earlier lineage + earlier top-5 grids + 21 tonight):
  L3-rsi5hi-FD 274,357 + 21 = 274,378 (BAR90 4.50); NS3V1 163,111 + 21 = 163,132 (4.41); NS5 934,988 + 21 = 935,009
  (4.72); MF4 base: MF family as MF4-FD 935,022 + 21 = 935,043 (4.72); NM-MF3-FD: discovery count (mf3swarm1020)
  inside the MF family, largest backlog lineage used, 935,043 + 21 = 935,064 (4.72).
- No-strangle screen (BDI charter) reported for every filter row: keeps >= 70% of trades and >= 90% of top-decile winners.
- Only a variant meeting the Testing bar is scored once on HOLD (rule 18 rising bar) and proposed as a DECISION.
- Winners (beats parent) go to research/backlog.jsonl, tag `top5-tune`; the grid line per setup is logged as parked.

## 4. Part A (descriptive, tunes nothing, not in N)
Full 20 read live (weekly full pass; the table was last updated 11-10). Two-year second opinion for the 10 of the 20
that have a bt_lab1104 trade list (all others are newer than the lists or Workbench / ULT / NM copies without one).
