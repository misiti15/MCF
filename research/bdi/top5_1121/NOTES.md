Educational only — not financial advice.

# Top-20 conditions + top-5 execution tune, 2026-11-21 (twentieth run, Saturday weekly): FAILED the Testing bar, 0 of 105; 11 variants beat their parent

- **Live** numbers are **paper** trades (rule 7): a diagnosis, not evidence. They are re-priced on the **LR8 cost
  basis** (`mcf.costs.cost_r_lr8`, DQ-P3) for every row, including rows before LR8's 11-12 start. **History** numbers
  are **backtests** on the open two-year history: production + time-of-day costs, x3 on the extended tier, TRAIN
  (<= 2025-12) and VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**. No
  holdout was scored, because nothing reached the Testing bar.
- **Data:** live journals of all 10 accounts (`fetch_live.py`, the `footrace.live_trades` reader with entry/exit time,
  side and MFE/MAE kept; cross-account duplicate signals counted once): 29,564 closed run-1 trades, 10-06..11-20.
  Market data by Alpaca market-data GET only. 2-year frames per `research/bdi/1104/DATA.md` (frames to 2026-11-04);
  Part A 2-year reads use the bt_lab1104 trade lists (unchanged since 11-04, so those reads repeat earlier weeks).
- **Reused, not redone:** final1121 (140 configs, nothing passed; its do-not-re-run list was not touched), qa_1121,
  whatworks_1120 (random-entry null), remedyq_1120 (12:30 cut-offs; tonight's 12:30 window split for NM-MF3 /
  L3-rsi5hi is a per-setup knob on two other setups, not a re-run of the Primary trio).
- **Configurations scored: 105** (21 one-knob variants x 5 setups, pre-declared in `PLAN.md` before any row was
  scored). G20 (first signal per symbol-day) is identical to the parent for the three non-refire setups (MF4, NM-MF3,
  NS5); counted anyway. Part A reads are descriptive and tune nothing (11 dimensions x 20 setups live, 10 setups 2y).
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.**
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00005R, 100% within 0.01R; NS3V1 on its cache
  geometry, row P0).
- Nothing in config/, mcf/, docs/live/ or the workflows was changed. Outputs: 16 backlog lines, tag `top5-tune` (5 grid lines
  parked, 11 beat-parent lines rework), in `backlog_proposals.jsonl`.

## Rule changes in effect inside the stats windows (research/ledger.jsonl effective dates)
- **Part A live window, 10-06..11-20** (everything since 11-10's block, plus the earlier list in top5_1110/NOTES.md):
  EXPO1109 revert + TEAM-6 Primary (11-11); **LR8 live cost model, On Deck split-tape short gate off (ODX-1), testing
  per-setup caps raised (10 -> 30 B-F), Testing A full universe again, account halts 300R, Testing D/E/F wired and
  filled, GEN-GRAD (11-12)**; GY arena moves (11-13); RW7-FD On Deck -> Testing F, ROT1 block 1 (11-16); **TSZ1
  testing half-size lots, 2x slots, cap 100 (11-17; R comparable, $ not)**, 15 Workbench copies, SPYEXIT engine (11-17);
  GY-BENCH (11-18); C3 bundle (NS5 Primary -> On Deck, EXIT100, ROT2, U9-TGT, U9-ETB; 11-19); ultimate_1119
  admissions, stop rounding, ROT block 2 (11-20). All live R is on one cost basis (LR8), so the 11-12 cost change does
  not split the record; sizing changes (TSZ1) change $ only.
- **Part B live window, 11-16..11-20:** TSZ1, Workbench copies, SPYEXIT (11-17), GY-BENCH (11-18), C3-NS5 / EXIT100 /
  ROT2 / U9 quote and borrow checks (11-19), ultimate_1119 admissions + stop rounding (11-20).
- **After the windows:** burst brake (30 entries / setup / 10 min) + watchdog act on all accounts (11-23), ST7-FD
  Primary -> On Deck (11-23, ST7-MOVE), Remedy-Q 12:30 Testing copies of L3-fromopen / RW3 / RW5 (11-23). Primary from
  11-23 = NM-ETF-late-dip-di-long, RW5-FD, RW3-FD, L3-fromopen-FD.

## Part A - top-20 conditions (live all 20, 2y for 10)
Full rows: `research/bdi/top20/CONDITIONS.md` (2026-11-21 block, at the top of the table); outputs
`research/bdi/top20/live_*`, `hist_bt_*` (scripts `conditions_live_1121.py`, `conditions_2y_bt_1121.py`).
Top 20 = leaderboard as of 11-20, >= 20 trades, GEN-* out (also the five GEN-GRAD setups in Testing A-F, which hold
three of the top four leaderboard places). Weekly full pass: all 20 live; 2y second opinion for the 10 with a bt_lab1104
list (L3-fromopen, L3-lowdist, RW3-FD, RW5-FD, NM-MF3, L3-rsi5hi, RW7-FD, MF4 base, NS1, RW1-FD). The other 10 are new
Workbench / ULT / NM / GY copies without a 2-year list.

**Top "thrives when" findings**
1. **L3-gap-slope-fromopen-FD (Primary): SPY above its open at 10:00** (live +0.39R, n 190) vs below (-0.06R, n 73);
   compass UP +0.35R (n 183). The record does **not** lean on one day (w/o 10-20 +0.148R, 39% of R). Live loses after
   13:00 (-0.71R n 15 / -0.29R n 32) while 2y's best slice is 14:00+ (+0.142R, both splits): they still disagree, and
   the Remedy-Q 12:30 copy in Testing F (from 11-23) is the live test.
2. **RW3-FD (Primary): deep gap-downs (gap < -3%: +0.55R, n 38) and SPY below its open at 10:00 (+0.48R, n 66)**;
   flat gaps (-1..+1%) carry 65% of the losing R on 47% of trades. The record leans on 10-22 (71%; w/o it +0.051R).
   Skipping compass-UP entries passes the no-strangle screen (+0.156 -> +0.230R, keeps 73% / 95%): on deck / sizing idea.
3. **RW5-FD (Primary): ETFs (+0.46R, n 50)**; stocks hold 91% of losing R on 75% of trades; 13:00-14:00 is the weak hour
   (-0.13R, n 43; skipping it passes the screen, +0.106 -> +0.165R). The record leans on 10-22 (82%; w/o it +0.022R).

**Other reads**
- The **unconfirmed compass** is again the losing state for the CWT09 short (g10: 74% of losing R on 42%), RW6G1-FD
  and CWT12-flag; NM-MF3 is the opposite (unconfirmed is its best state, DOWN holds 78% of its losing R).
- **One-day records** (>= 50% of R on one session): ULT-05 (1 session), NM-RWN4 (106%), CWT14-orl-WB5 (108%), NM-MF3
  (170%), NM-RWR4 (135%), L3-rsi5hi-FD (100%), RW7-FD-WB3 (150%), MF4 base (454%), L3-lowdist-FD (79%), RW3-FD (71%),
  RW5-FD (82%), RW7-FD (90%), RW3-FD-WB4 (60%). Only L3-fromopen-FD (39%) and CWT09-g10 (49%) are under 50%; the other five have a flat or negative total. Several new copies have
  traded only on SPY-down days (RW3-WB4, CWT14-orl-WB5, RW7-WB3, ULT-05).
- **Live vs 2y disagree** on L3-fromopen (13:00+), L3-lowdist (SPY flat at 10:00 is live's worst and 2y's best) and
  L3-rsi5hi (14:00+). Price < $20 remains the weakest 2y bucket for the three L3s.
- Screen-passing skips, live only (n small, on deck only, none scored as filters): L3-fromopen skip 14:00+, L3-lowdist
  skip leveraged ETFs, RW3-FD skip compass UP, RW5-FD skip 13:00-14:00, RW7-FD / RW1-FD skip SPY flat at entry,
  L3-rsi5hi skip SPY below its open at 10:00 (on 2y at signal: +0.025R, t 0.82, keeps 69% of top decile - fails the
  screen), MF4 skip price >= $150 (2y: +0.014R, t 1.21, keeps 49% of top decile - fails).

## Part B - top-5 execution tuning
Selection (PLAN.md section 1): MF4-h40-open-flowsell (47, Testing A), NM-MF3-qqqdn-gapdn-FD (33, Testing A),
NS3V1-am-widestop-short (31, Testing A), L3-gap-slope-rsi5hi-FD (29, On Deck), NS5-sma50-flush-oversold-long (22, On
Deck; Primary until 11-18). Rotated out: the pdl lineage, the ten setups tuned in top5_1106 / 1109 / 1110 with no
setup change since (incl. RW1-FD 103, L3-fromopen-FD 70, MF2-FD 48, RW3-FD 43, RW5-FD 34), the Workbench copies
(MF2-FD-WB3, L3-fromopen-FD-WB4: exits not modelled by the harness; C3-WB) and NM-ETF-late-dip-di-long (not in the
harness). MF4 base and NM-MF3-FD are first top-5 tunes.

### Live (paper, 11-16..11-20, LR8 R)
| setup | n | win | avg R | w/o best day (share) | avg win / loss | BE win | med MFE / MAE | losers never +0.2R | give-back of losers | where losers cluster |
|---|---|---|---|---|---|---|---|---|---|---|
| MF4 base | 47 | 80.9% | +0.097 | -0.096 (11-20, 140%) | +0.33 / -0.87 | 72.8% | 0.35 / 0.40 | 3 of 9 | 1.15R | 11-16 (-1.7R); 7 stops avg -1.08R vs 38 targets +0.33R |
| NM-MF3-FD | 33 | 63.6% | +0.127 | -0.037 (11-20, 122%) | +0.60 / -0.70 | 53.8% | 0.55 / 0.45 | 6 of 12 | 1.03R | 11-18 (9 trades -3.8R); 10:30-11:30 (-0.61R, n 3) |
| NS3V1 | 31 | 51.6% | +0.018 | -0.036 (11-19, 280%) | +0.29 / -0.28 | 48.5% | 0.37 / 0.31 | 5 of 15 | 0.56R | 11-18 (22 trades -1.8R); 09:50-10:00 (-0.26R, n 7); 21 of 31 exit at the 15:55 flatten (-0.11R) |
| L3-rsi5hi-FD | 29 | 62.1% | -0.007 | -0.067 (11-20) | +0.44 / -0.73 | 62.7% | 0.42 / 0.29 | 6 of 11 | 0.99R | 11-19 (-2.4R); entries before 11:30 (2 trades, both stops) |
| NS5 | 22 | 40.9% | -0.304 | -0.47 (11-18) | +0.69 / -0.99 | 59.0% | 0.55 / 0.81 | 1 of 13 (6 reached +0.5R) | 1.48R | 11-19 in On Deck (16 trades -6.5R) |

Live vs backtest win% (TRAIN+VALID parent): MF4 80.9 vs 62.6%, NM-MF3 63.6 vs 51.6%, NS3V1 51.6 vs 65.8%, L3-rsi5hi
62.1 vs 66.5%, NS5 40.9 vs 49.8%. MF4's live win rate is far above its backtest but still under its 72.8% break-even
(small wins at a t05s1 target vs full-size stops). NS5's losers go green first (6 of 13 reached +0.5R; give-back 1.48R),
the pattern a break-even / partial exit is meant for, but on two years G05 (half off at 0.5 x target + BE) is flat (+0.004R).

### History (backtest parents, TRAIN+VALID)
| setup | n | win / BE | exp | TRAIN / VALID | up / down sessions | beat parent | best variant (d R; t) | its TRAIN / VALID |
|---|---|---|---|---|---|---|---|---|
| MF4 base | 2,656 | 62.6 / 70.5% | -0.119 | -0.146 / -0.072 | -0.23 / +0.01 | 6 | G13 CF +0.064 (5.55) | -0.109 / -0.032 |
| NM-MF3-FD | 1,692 | 51.6 / 51.9% | -0.004 | -0.010 / +0.004 | -0.18 / +0.04 | 1 | G13 CF +0.034 (2.47) | **+0.052 / +0.020** |
| NS3V1 | 1,560 | 65.8 / 59.4% | **+0.069** | **+0.040 / +0.106** | -0.02 / +0.13 | 0 | G13 CF +0.008 (1.86) | +0.059 / +0.104 |
| L3-rsi5hi-FD | 8,383 | 66.5 / 69.6% | -0.047 | -0.084 / +0.011 | -0.08 / +0.00 | 4 | G13 CF +0.058 (4.57) | **+0.001 / +0.030** |
| NS5 | 1,053 | 49.8 / 52.4% | -0.050 | -0.174 / +0.163 | +0.18 / -0.13 | 0 | G19 ADV x1.2 +0.021 (1.84) | -0.154 / +0.177 |

- **CF (G13) is the best knob again on 3 of 5** (MF4, NM-MF3, L3-rsi5hi beat the parent with it; NS3V1 +0.008R flat;
  NS5 -0.002R flat). Per the remedies rule: 3 improve (+0.034..+0.064R per parent signal), 2 flat, 0 worse. It keeps
  70-98% of trades and 100% of top-decile winners. It does not make MF4 positive (still -0.079R) and it leaves L3-rsi5hi
  and NM-MF3 negative in up sessions and (L3-rsi5hi) without the best day.
- **MF4 base (first tune):** six knobs beat the parent - G13 CF, G01 stop x1.5, G14 skip < $20, G11 entries before 10:15
  (keeps 21%: strangles), G19 ADV x1.2, G16 SPY side (keeps 41%: strangles). Every variant still loses in TRAIN and in up
  sessions (-0.18..-0.31R): MF4 is a down-tape short, like the RW/MF shorts in top5_1110.
- **NM-MF3-FD (first tune):** flat parent on two years. G13 CF passes the setup bar exactly (t 2.47) and is positive in
  TRAIN and VALID, but t TRAIN+VALID 1.09 vs BAR90 4.72, up sessions -0.14R. The loser pattern (skip DOWN-confirmed
  compass, G21) is +0.020R, t 0.85, and keeps 50% of trades.
- **NS3V1:** the parent is positive on both splits (+0.069R, t 2.39) and no knob improves it; the live loser pattern
  (entries before 10:00) is the parent's best 2y slice (+0.172R), so G21 is worse (d -0.007R). The parent is the best
  execution found.
- **L3-rsi5hi-FD:** same as top5_1105 - G13 CF, G14 skip < $20, G19 ADV >= 95M and G01 stop x1.5 beat the parent;
  G13 / G14 pass the no-strangle screen (81% / 100%, 71% / 99%) but t TRAIN+VALID 0.28-0.30 vs BAR90 4.50.
- **NS5:** nothing beats the parent; the TRAIN -0.174 / VALID +0.163 split and the down-session loss are unchanged.
- Tighter stop (G02) is the worst knob on 3 of 5 (MF4, NM-MF3, L3-rsi5hi; d -0.029..-0.043R); flat on NS3V1 / NS5.
- Bars: per-setup 2.47, study-wide 3.05 (N 105); BAR90 4.41-4.72 on lineage N. Configs counted: 105.

## Owner inbox
Two FYI lines (`inbox_lines.md`). No DECISION.

## Files
`PLAN.md` (pre-declaration), `fetch_live.py`, `live_rank.py` / `live_rank.csv` / `live_top5*.{csv,txt}`,
`build_cache.py`, `scan_1121.py`, `report_1121.py` / `report_out.txt` / `results.csv` / `summary.json` /
`hist_parent_detail.txt`, `make_proposals.py` / `backlog_proposals.jsonl`. Part A scripts and outputs in
`research/bdi/top20/`. Scratch (/dev/shm/t21: journals, bars, signal cache, simulated trades) deleted after the run.
