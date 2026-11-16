# Diagnosis — Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` (Primary, TEAM-6)
Educational only — not financial advice. Mechanic, 2026-11-16 (built during market hours: research files only, no config change).

Engine: `RW3-gapdn-rsi5pop-flowsell-short-FD_engine.png` (P1..P26, blueprint `RW3-gapdn-rsi5pop-flowsell-short-FD.md`).
Live evidence = all 173 live trades (Primary 135, On Deck/Testing 1 38; 2026-10-12..11-16, 25 sessions; leaderboard row
at job start: 171 trades / 24 sessions, +0.202R) and 292 live signals. Live avg R +0.208, win 61%, avg R w/o best day
+0.078 — **best day 10-22 = 68% of total R (`1 day` tag)**; 10-22 (+24.3R) and 11-05 (+16.5R) together exceed the whole
record (+35.9R); the other 23 sessions sum to −4.9R. Live R mixes the old cost allowance (to 11-11) with LR8 (from 11-12);
13 rule changes sit inside the window (blueprint list: TEAM moves 10-15/10-21, per-setup −2R latch in Primary 10-29,
Primary size 10-28, CF stop-cost filter in Testing 1/2 10-30, LR1/LR3/LR5/LR7 11-12). Live numbers DIAGNOSE only; the pass
decision uses the identical backtests in RESULTS.md (owner 2026-11-16). Catalogue = research/workbench/PARTS_CATALOGUE.md.

## The 5 worst and 5 best live trades
| Trade (chart) | What happened | Part that caused it | Catalogue part | What the tweak does to THIS trade |
|---|---|---|---|---|
| XLI 10-13 −1.25R (`_worst1_XLI_2026-10-13.png`) | Signal 12:30, short 12:31:55 @ 167.62; 1R = $0.46 = **0.28% of price**; MFE +0.48R 13:01, P23 stop 14:06 @ 168.18 | P20 thin 1R (cost and noise large vs R) | Intake / Entry (1R) | ATR floor 1.6% (1R ≥ 0.40%): **not taken** (+1.25R) |
| PDBC 11-04 −1.25R (`_worst2_PDBC_2026-11-04.png`) | Signal 13:05, short @ 18.62; 1R = $0.08 (0.43% live, 0.38% in the replay frame); MFE +0.08R, stop 13:22 | P20 thin 1R + late entry | Intake / Entry (1R) | ATR floor: **not taken**; SPY was +0.22% since 09:50 → SPY gate also skips it |
| VG 11-03 −1.15R (`_worst3_VG_2026-11-03.png`) | Signal 09:55 (first bar of the window), short @ 13.07, MFE +0.43R 10:11, stop 10:25 | P6/P7 window start: the 09:50-10:30 pop is often the real reversal | Timer / window | start 10:30: **not taken** |
| MMM 11-03 −1.13R (`_worst4_MMM_2026-11-03.png`) | Signal 10:15, short @ 175.81, MFE +0.27R, stop 10:50 | P6/P7 window start | Timer / window | start 10:30: **not taken** |
| SQQQ 10-21 −1.13R (`_worst5_SQQQ_2026-10-21.png`) | Signal 12:25, short @ 36.46; MFE **+1.15R at 13:21** (target 36.03 missed by ~2c), drifted 2.5 h, P23 stop 15:02:57 | P24 target just missed + P26 long hold (stays in too long) | Target / Time exit | max hold 90-120 min: exit ~13:56-14:26 near 36.2-36.3 (≈ +0.5R); flat 15:00: exits ~36.7 (≈ −0.6R). Kept by WB3 (−1.13R) — max hold did not stack with WB3 overall (RESULTS D2/D3/D6) |
| APH 11-05 +2.82R (`_best1_APH_2026-11-05.png`) | Short 11:35:29 @ 74.00 (slip −64.6 bps in our favour), target 12:00 | works as designed; R > 1 is fill slip | — | all copies keep it (replay +0.99R) |
| BITX 11-05 +2.26R (`_best2_BITX_2026-11-05.png`) | 11:35, target | works as designed | — | kept |
| QLD 11-05 +2.21R (`_best3_QLD_2026-11-05.png`) | 11:20, target | works as designed | — | kept |
| TECL 11-05 +2.17R (`_best4_TECL_2026-11-05.png`) | 11:20, target | works as designed | — | kept |
| CSCO 11-05 +1.69R (`_best5_CSCO_2026-11-05.png`) | 11:20, MAE −0.72R, target | works as designed | — | kept |

All 5 best trades are from one session (11-05, SPY falling: −1.6% since 09:50 at entry) — the setup's edge is on
down-tape days; WB3 keeps every one of them and drops 4 of the 5 worst (it keeps SQQQ 10-21).

## Across all live trades (which part is behind the losses)
- **Gates / day type — the clearest pattern.** Replay of the live sessions by SPY change since the 09:50 close at the
  signal bar: ≤ +0.20% 159 trades +0.24R avg; > +0.20% 51 trades −0.06R. 2-year by day type (SPY open→close): down days
  +0.137R, flat +0.014R, **up days −0.255R** (1,569 trades). A gap-down name popping while the market rallies is more
  often a real recovery than a pop to fade. → new gate (anchored after 09:50, owner rule): skip while SPY > +0.20% since 09:50.
- **Timer / window start (P6/P7).** Live entries 09:50-10:30: 9 trades −0.57R (10:00-10:30 −0.19R avg); replay 10:00-10:30
  6 trades −0.47R avg; 10:30-13:00 is the core (live 134 trades +38.1R). → start 10:30. Window end (13:00) also tested.
- **Entry / 1R (P20) + intake.** Thin R (1R < ~0.4% of price) makes the fixed stop cost (max $0.02, 4 bps) and noise large:
  XLI, PDBC. 2-year: 1R < 0.30% of price −0.24R (71 trades in the best combo). → ATR floor (1R ≥ 0.30 / 0.40% of price).
- **Time exit (P26).** 55 live flattens at 15:55 avg −0.06R with avg MFE +0.43R; median live hold 104 min; replay
  time exits 69 (33%), 38 of them had MFE ≥ 0.5R first. → max hold 90/120, flat 15:00, BE after +0.5R.
- **Stop (P23).** 38 live stops avg −1.07R; only 2 had MFE ≥ 0.5R first → the stop is not cutting would-be winners; tested
  1.25R anyway. **Target (P24):** 80 targets (46%) at +1.0R, median MAE −0.23R; 0.8R tested.
- **Sensors (P9-P12).** Replay buckets show no clean threshold edge (heat ≤ −40 small n worse; buyPressure < −0.6 best;
  RSI(5) flat across 80-100; gap −0.5..−1% weak in the replay but not in the 2-year). Nudges tested: heat −25, buyPressure
  −0.40, RSI(5) 85, gap ≤ −0.5 / −1.0, price ≤ VWAP.
- **Gates P14-P18.** P16 −2R latch blocked 23 live signals (8%), P17 account halt 10, P18 quote/spread 35, P15 lots/symbol
  8 (refire is off, so the per-symbol cap only binds across accounts); P5 borrow 39 (13%, not tunable). Latch off and
  refire on (P8) tested. **Intake P1-P4:** ADV floor $150M tested; price ≥ $5 never binds; earnings blackout not tunable here.
- **P19/P21/P22 (order, size, max position):** market order at the signal-bar close; live slip averaged favourable on the
  best trades; size and max position change $ not R — no tweak.

## Candidates chosen and why
1. **WB1 — P6/P7 window starts 10:30** (live + replay early-entry losses).
2. **WB2 — new gate: skip while SPY > +0.20% since the 09:50 close** (up-tape is the losing day type; after-09:50 anchor).
3. **WB3 — WB1 + WB2 + daily ATR ≥ 1.6% (1R ≥ 0.40% of price)** — the best DEPLOYABLE combination (RESULTS.md).
Also passed but not spawned: flat 15:00 (good in both tests, but the live runner has no per-setup flatten time —
`Signal.exit_by` is backtest-only; backlog idea), max hold 120, RSI(5) > 85, refire, window end 13:00 (meets only).
