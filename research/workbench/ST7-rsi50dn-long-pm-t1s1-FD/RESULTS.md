# Workbench results: RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` vs its copies
Mechanic, 2026-11-16 (built during market hours, research only; no config, setup or exit changed). Educational only — not financial advice.

## Verdict
| Copy | Change | Replay avg R (parent +0.043) | 2-year avg R (parent +0.013) | Avg R w/o best day (replay / 2y) | Worst day (replay / 2y) | Trades (replay / 2y) | Verdict |
|---|---|---|---|---|---|---|---|
| **`ST7-rsi50dn-long-pm-t1s1-FD-WB1`** | Gates (new layer): skip while SPY is up > +0.10% since its 09:50 close | **+0.128** | **+0.077** | +0.006 / +0.062 (parent -0.051 / +0.003) | -2.4R / -8.7R (parent -4.2 / -26.9) | 53 / 684 (parent 77 / 1001) | **PASS — recommended** |
| alt (not spawned) | WB1 + cost/R <= 0.15 (Y1) | +0.097 | +0.108 | -0.060 / +0.090 | -2.4 / -8.7 | 38 / 545 | pass; not chosen (replay gain half of WB1's; the Testing accounts' own CF 0.15R filter applies it live anyway) |
| alt (not spawned) | skip SPY > 0.00% (W06) | +0.151 | +0.065 | +0.018 / +0.046 | -2.4 / -8.7 | 48 / 557 | pass; not chosen (2-year lower, 19% fewer trades than WB1) |

Pass rule (RULES.md, clarification 2026-11-16): meets or exceeds the parent's avg R after costs in BOTH tests and is not
worse on avg R w/o best day / worst day by more than 0.02R / 10%. WB1 beats the parent clearly in both tests, on every one of
those measures, and in both 2-year halves (train ..2025-12: -0.067 -> +0.026R; valid 2026-01..10-09: +0.058 -> +0.103R).
Total R also rises (replay +3.3 -> +6.8R; 2-year +13.4 -> +52.9R) although it trades 31-32% less.

## Supervisor sign-off — WB1
- **What changed:** one new layer at the GATES stage. At the signal bar the copy reads SPY's move since its 09:50 bar close
  (owner direction rule: anchored after 09:50, never the open or prior close) and skips the buy while SPY is up more than
  +0.10%. Everything else (P1-P24) is the parent's.
- **Why:** ST7 is a dip buy. It works when the stock dips WITH the market and fails when it falls alone into a rising tape
  (live: SPY up since 09:50 = 11 trades -0.24R vs 24 trades +0.43R; the five 10-21 / 10-29 stops all fired that way).
  This is the mechanism st7_1022 found with QQQ vs VWAP (ST7Q), re-measured the owner-approved way (after 09:50).
- **Overall before -> after (parent -> WB1):** replay +0.043 -> +0.128R/trade (paired by day +3.5R, t 0.62), 2-year
  +0.013 -> +0.077R/trade (paired by day +39.4R, t 1.18); w/o best day -0.051 -> +0.006 / +0.003 -> +0.062; worst day
  -4.2 -> -2.4R / -26.9 -> -8.7R; win 55.8 -> 60.4% / 52.6 -> 56.4%; avg win / loss (2y) +0.81/-0.88 -> +0.83/-0.90;
  median hold 80 -> 78 min. Positive after costs in both tests.
- **Where it gives back:** (1) trades -31% (2-year 1.6 -> 1.1 per session), (2) up-day total R: per trade better
  (+0.17 -> +0.31R) but 174 of the 304 up-day trades are skipped, so the up-day total falls +51.6 -> +40.0R (down days
  -47.1 -> -0.9R, flat +8.9 -> +13.8R) — the long side's up-day behaviour improves per trade and loses some volume;
  (3) the 2y valid-half day-paired total is only +9.7R (t 0.72) — most of the gain is in 2025.
- **Honest limits:** neither paired difference clears the configs-counted bar max(1.5, sqrt(2 ln 47)) = 2.78 (reported,
  not a pass hurdle). The replay is small (77 -> 53 trades) and one-day heavy for BOTH (best day = 97% of WB1's replay R,
  > 100% of the parent's) — the "w/o best day" column is the fair read there. **Twin check:** 72% of WB1's 2-year trades
  also have QQQ at/below VWAP (ST7Q's rule; ST7Q-like trades on this bench: 506, +0.115R). ST7Q now runs only in
  Explore 1, so WB1 must not go to Explore 1; in a Testing account it is a different gate (after-09:50 SPY move) on a
  mostly shared signal set — the owner may prefer to judge WB1 and ST7Q side by side.
- Signed: the copy is a clear overall improvement on the identical tests, not a technical pass.

## Configurations counted: 47 (+ the parent)
Round 1 (18 one-part copies V01-V18 + the parent without the book as a reference), declared after the live teardowns and
before any score; Round 2 (16: cost/R and SPY-gate neighbours + combinations); Round 3 (8: neighbours of skip-SPY>0 and
add-ons); Round 4 (4 add-ons on X2 = WB1). Declarations: `code/decl.py`. Bar max(1.5, sqrt(2 ln 47)) = 2.78.
**Failures (not kept):** V01 skip the 10:45 bar when gapped up and V02 start 10:50 (both tests negative: the 10:45 bar is
the setup's better half), V03 end 14:00, V05 buy pressure > 0.10, V08 price >= $10 (replay), V09 1R 0.30 ATR, V11 target
0.8R, V12 max hold 90, V13 time stop 60 min if < 0.3R (2y), V14 break-even after +0.6R (worst of all: -0.018R 2y),
V15 skip SPY down > 0.30% (helps nothing; the down-day trades it removes were not the losers), V18 10 open lots (replay);
all cost/R + SPY>+0.30% combos C1-C10 and X1 skip SPY > -0.10% fail on replay w/o best day (the 77-trade replay thins
to 18-44 trades). Passing but not chosen: V04, V06, V07, V10, V16, V17, W01-W06, X3-X8, Y1-Y4 (see the table).

## The tests (identical for the parent and every copy)
- **Replay of the live sessions:** every session 2026-10-12..11-10 (22 sessions; 11-11..11-13 have no cached bars yet —
  fetching the full universe is after-hours work) over the FULL universe (ADV20 >= $95M), not only the names that
  signalled live: lab frames from research/history2y to 11-04 and, 11-05..11-10, frames rebuilt from data/team 1-minute
  bars by the CWT14 Mechanic job (same setup_lab pipeline; parity 526/526 on 11-02..11-04). Parity with live: 37 of the
  38 live trades inside that window are on the bench at the same bar (10:45-10:47 live = the 10:45 bar).
- **2-year backtest:** 2024-10-01..2026-10-09, open months only; **locked block 2024-11-01..2025-02-28 never read**
  (lib refuses the months; asserts on candidates and paths). Train ..2025-12-31, valid 2026-01-01..10-09.
- **Engine:** 5-minute lab-frame signals, first qualifying bar per symbol-day, price >= $5; fill = open of the 1-minute
  bar starting at the signal-bar close (live fills ~2 s after); stop / target from the signal-bar close (LabStrategy);
  1-minute exit walk, stop first, target only when traded through by >= $0.01, flat 15:55; R = net P/L / |fill - stop|;
  **LR8 costs** (entry (1c + 1 bp) x time-of-day mult + 1 bp cushion; target at the limit; stop (1c + 1 bp) + max(2c, 4 bp);
  time exit (1c + 1 bp) + max(1c, 1 bp); SEC / TAF / CAT); Primary's book (<= 30 open lots, -2R per-setup latch after
  costs). Not modelled: quote/spread checks (P16 blocked 33% of live signals), the -20R account stop.
- SPY since 09:50 from SPY 1-minute closes completed by the bar (code/ctx.py, from the CWT14 job; equals the runner's
  `spy_fo`-based value: correlation 1.0000, threshold agreement 100%). Module parity: `modules/...-WB1.py` = the
  bench rule on 2 test months (0 mismatches of 82 bars).
- Code: `code/` (cand.py, ctx.py, paths.py, sim.py, load.py, decl.py, go.py); numbers `res_ROUND1..4.csv`.

## All configurations side by side (ALL = whole test; rule check vs parent)
| config | replay n | replay avg R | replay w/o best | replay worst day | 2y n | 2y avg R | 2y w/o best | 2y worst day | 2y up/flat/down | rule check |
|---|---|---|---|---|---|---|---|---|---|---|
| PARENT | 77 | +0.043 | -0.051 | -4.2 | 1001 | +0.013 | +0.003 | -26.9 | +0.17/+0.03/-0.14 | — |
| PARENT isolated (no book) | 78 | +0.055 | -0.035 | -4.2 | 1034 | +0.014 | +0.004 | -26.9 | +0.17/+0.03/-0.13 | pass |
| V01 P5/P8 skip the 10:45 bar when gap > 0 | 26 | -0.194 | -0.283 | -2.2 | 435 | -0.002 | -0.028 | -4.3 | +0.15/-0.09/-0.05 | fail (replay avg, replay w/o best, 2y avg, 2y w/o best) |
| V02 P5 start 10:50 | 25 | -0.158 | -0.248 | -2.2 | 425 | -0.003 | -0.030 | -3.1 | +0.15/-0.10/-0.05 | fail (replay avg, replay w/o best, 2y avg, 2y w/o best) |
| V03 P5 end 14:00 | 73 | +0.041 | -0.058 | -4.2 | 894 | +0.002 | -0.008 | -26.9 | +0.17/+0.03/-0.18 | fail (2y avg) |
| V04 P10 fromOpen < -1.5 | 39 | +0.108 | +0.010 | -2.0 | 613 | +0.006 | -0.011 | -23.6 | +0.14/-0.01/-0.10 | pass |
| V05 P11 buyPressure > 0.10 | 56 | +0.026 | -0.013 | -2.8 | 623 | +0.023 | +0.013 | -18.6 | +0.18/+0.01/-0.12 | fail (replay avg) |
| V06 P1 cost/R <= 0.10 | 30 | +0.160 | +0.005 | -2.4 | 582 | +0.025 | +0.005 | -17.5 | +0.16/+0.07/-0.14 | pass |
| V07 P1 ATR >= 2% of price | 64 | +0.060 | -0.024 | -2.4 | 959 | +0.018 | +0.006 | -26.9 | +0.17/+0.02/-0.13 | pass |
| V08 P3 price >= $10 | 72 | +0.027 | -0.077 | -4.2 | 983 | +0.021 | +0.010 | -25.6 | +0.16/+0.03/-0.12 | fail (replay avg, replay w/o best) |
| V09 P18 1R 0.30 ATR | 77 | +0.042 | -0.020 | -4.0 | 1001 | +0.002 | -0.008 | -26.3 | +0.16/+0.02/-0.16 | fail (2y avg) |
| V10 P21 stop 1.25R | 77 | +0.057 | -0.038 | -3.9 | 1002 | +0.014 | +0.004 | -26.1 | +0.16/+0.02/-0.13 | pass |
| V11 P22 target 0.8R | 77 | +0.020 | -0.109 | -4.2 | 1003 | +0.006 | -0.003 | -26.9 | +0.15/+0.01/-0.13 | fail (replay avg, replay w/o best) |
| V12 P24 max hold 90 min | 77 | +0.023 | -0.074 | -3.6 | 997 | -0.012 | -0.025 | -26.6 | +0.11/-0.00/-0.13 | fail (replay avg, replay w/o best, 2y avg, 2y w/o best) |
| V13 P24 60 min if best < 0.3R | 77 | +0.083 | -0.003 | -3.3 | 997 | -0.005 | -0.016 | -26.4 | +0.14/-0.01/-0.12 | fail (2y avg) |
| V14 P21 BE after +0.6R | 77 | -0.025 | -0.110 | -4.2 | 1001 | -0.018 | -0.030 | -26.9 | +0.09/-0.01/-0.12 | fail (replay avg, replay w/o best, 2y avg, 2y w/o best) |
| V15 gate skip SPY since 09:50 < -0.30% | 72 | +0.061 | -0.036 | -4.2 | 765 | +0.003 | -0.007 | -26.9 | +0.18/+0.02/-0.32 | fail (2y avg) |
| V16 gate skip SPY since 09:50 > +0.30% | 63 | +0.077 | -0.033 | -2.4 | 864 | +0.035 | +0.023 | -8.7 | +0.22/+0.01/-0.06 | pass |
| V17 gate skip SPY above 09:30-09:50 high | 58 | +0.102 | -0.015 | -2.4 | 752 | +0.013 | -0.002 | -26.9 | +0.29/+0.04/-0.13 | pass |
| V18 P12 open lots 10 | 67 | +0.003 | -0.081 | -4.2 | 938 | +0.026 | +0.017 | -11.0 | +0.17/+0.03/-0.11 | fail (replay avg, replay w/o best) |
| W01 cost/R <= 0.08 | 20 | +0.147 | +0.005 | -1.1 | 418 | +0.051 | +0.030 | -12.0 | +0.15/+0.13/-0.12 | pass |
| W02 cost/R <= 0.12 | 42 | +0.081 | -0.035 | -2.8 | 698 | +0.034 | +0.019 | -19.7 | +0.16/+0.04/-0.08 | pass |
| W03 cost/R <= 0.15 | 52 | +0.080 | -0.032 | -2.4 | 814 | +0.027 | +0.013 | -22.0 | +0.19/+0.01/-0.10 | pass |
| W04 skip SPY > +0.20% | 61 | +0.094 | -0.017 | -2.4 | 792 | +0.039 | +0.026 | -8.7 | +0.20/+0.03/-0.04 | pass |
| W05 skip SPY > +0.40% | 72 | +0.035 | -0.068 | -2.4 | 906 | +0.035 | +0.024 | -8.7 | +0.20/+0.01/-0.06 | pass |
| W06 skip SPY > 0.00% | 48 | +0.151 | +0.018 | -2.4 | 557 | +0.065 | +0.046 | -8.7 | +0.22/+0.04/+0.04 | pass |
| C1 cost/R 0.10 + SPY > +0.30% | 25 | +0.046 | -0.176 | -2.4 | 496 | +0.056 | +0.034 | -7.5 | +0.21/+0.05/-0.06 | fail (replay w/o best) |
| C2 cost/R 0.12 + SPY > +0.30% | 35 | -0.023 | -0.183 | -2.8 | 603 | +0.061 | +0.043 | -8.7 | +0.20/+0.03/-0.00 | fail (replay avg, replay w/o best) |
| C3 cost/R 0.15 + SPY > +0.30% | 44 | +0.025 | -0.119 | -2.4 | 701 | +0.052 | +0.036 | -8.7 | +0.24/-0.00/-0.02 | fail (replay avg, replay w/o best) |
| C4 C1 + stop 1.25R | 37 | -0.025 | -0.146 | -2.2 | 633 | +0.063 | +0.050 | -8.8 | +0.24/+0.01/-0.01 | fail (replay avg, replay w/o best) |
| C5 C1 + price >= $10 | 25 | +0.046 | -0.176 | -2.4 | 496 | +0.056 | +0.034 | -7.5 | +0.21/+0.05/-0.06 | fail (replay w/o best) |
| C6 C1 + 60 min if best < 0.3R | 25 | +0.082 | -0.131 | -2.4 | 495 | +0.030 | +0.008 | -7.5 | +0.18/+0.01/-0.06 | fail (replay w/o best) |
| C7 C1 + bp > 0.10 | 18 | +0.072 | -0.108 | -1.1 | 302 | +0.074 | +0.057 | -3.4 | +0.24/+0.04/-0.04 | fail (replay w/o best) |
| C8 cost/R 0.10 + SPY above 09:30-09:50 high | 23 | +0.083 | -0.153 | -2.4 | 432 | +0.043 | +0.018 | -17.5 | +0.28/+0.13/-0.14 | fail (replay w/o best) |
| C9 C1 + ATR >= 2% | 25 | +0.046 | -0.176 | -2.4 | 496 | +0.056 | +0.034 | -7.5 | +0.21/+0.05/-0.06 | fail (replay w/o best) |
| C10 C1 + open lots 10 | 25 | +0.046 | -0.176 | -2.4 | 477 | +0.054 | +0.031 | -7.5 | +0.21/+0.06/-0.06 | fail (replay w/o best) |
| X1 skip SPY > -0.10% | 21 | +0.245 | -0.160 | -2.4 | 452 | +0.075 | +0.052 | -8.7 | +0.32/+0.06/+0.04 | fail (replay w/o best) |
| X2 skip SPY > +0.10% | 53 | +0.128 | +0.006 | -2.4 | 684 | +0.077 | +0.062 | -8.7 | +0.31/+0.05/-0.00 | pass |
| X3 W06 + cost/R <= 0.15 | 33 | +0.125 | -0.056 | -2.4 | 441 | +0.098 | +0.074 | -8.7 | +0.26/+0.04/+0.09 | pass |
| X4 W06 + stop 1.25R | 48 | +0.141 | -0.001 | -2.2 | 558 | +0.069 | +0.052 | -8.8 | +0.26/+0.02/+0.04 | pass |
| X5 W06 + ATR >= 2% | 41 | +0.081 | -0.057 | -2.4 | 530 | +0.080 | +0.061 | -8.7 | +0.23/+0.05/+0.06 | pass |
| X6 W06 + price >= $10 | 46 | +0.138 | -0.007 | -2.4 | 546 | +0.074 | +0.055 | -8.7 | +0.22/+0.04/+0.05 | pass |
| X7 W06 + 60 min if best < 0.3R | 48 | +0.202 | +0.087 | -2.4 | 554 | +0.037 | +0.018 | -8.7 | +0.15/-0.02/+0.04 | pass |
| X8 W06 + target 1.25R | 48 | +0.164 | +0.084 | -2.4 | 556 | +0.040 | +0.021 | -8.7 | +0.22/+0.02/-0.00 | pass |
| Y1 X2 + cost/R <= 0.15 | 38 | +0.097 | -0.060 | -2.4 | 545 | +0.108 | +0.090 | -8.7 | +0.33/+0.05/+0.06 | pass |
| Y2 X2 + ATR >= 2% | 46 | +0.063 | -0.060 | -2.4 | 653 | +0.089 | +0.073 | -8.7 | +0.32/+0.05/+0.02 | pass |
| Y3 X2 + price >= $10 | 51 | +0.116 | -0.017 | -2.4 | 672 | +0.087 | +0.072 | -8.7 | +0.31/+0.06/+0.01 | pass |
| Y4 X2 + stop 1.25R | 53 | +0.119 | -0.013 | -2.2 | 685 | +0.074 | +0.061 | -8.8 | +0.30/+0.04/+0.00 | pass |

## Pending config change — "ready to deploy after close" (NOT applied; built ~14:45 ET during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective the next session. The parent stays
in Primary, unchanged (On Deck / Primary for the copy still needs the owner).
1. Module: `research/workbench/ST7-rsi50dn-long-pm-t1s1-FD/modules/ST7-rsi50dn-long-pm-t1s1-FD-WB1.py` (self-contained; used in place).
2. `config/account_testing2.yaml` (Testing 2 — not the parent's account, not Explore 1 where ST7Q runs; Testing 1 =
   Testing 2 in weight), under `strategies:` add
   ```yaml
   ST7-rsi50dn-long-pm-t1s1-FD-WB1:
     # Workbench copy of ST7-rsi50dn-long-pm-t1s1-FD (Primary), Mechanic 2026-11-16: + skip while SPY is up > +0.10% since 09:50;
     # research/workbench/ST7-rsi50dn-long-pm-t1s1-FD/RESULTS.md.
     enabled: true
     type: lab
     module: research/workbench/ST7-rsi50dn-long-pm-t1s1-FD/modules/ST7-rsi50dn-long-pm-t1s1-FD-WB1.py
     context: [spy_fo]
     min_adv: 95000000
     window: [950, 1500]
     scale_out_r: null
     twin_group: ST7-T1   # parent / ST7Q family: never two of them on the same symbol
     tags: [workbench, "parent:ST7-rsi50dn-long-pm-t1s1-FD"]
   ```
   and put `ST7-rsi50dn-long-pm-t1s1-FD-WB1` FIRST in `live.setup_order` (RULES.md 5). Testing 2's own CF filter
   (max_stop_cost_r 0.15) will also apply — close to the Y1 row (2-year +0.108R).
3. `config/setup_names.yaml`: `ST7-rsi50dn-long-pm-t1s1-FD-WB1: {name: "RSI Collapse Dip Buy (all day) — WB1: skip when SPY up > 0.10% since 09:50", side: long, what: "as the parent; no buy while SPY is up more than 0.10% since its 09:50 close (dip with the market, not alone)"}`.
4. `research/ledger.jsonl`: id `2026-11-16-wb-st7-wb1`, effective next session, title "Workbench copy
   ST7-rsi50dn-long-pm-t1s1-FD-WB1 added to Testing 2, first in setup_order (Mechanic pass)"; then
   `python -m mcf.research.ledger check`.
5. `python -m mcf.report.assignments` (regenerate docs/live/assignments.json in the same commit), `pytest -q`, PR with
   setup-freeze passing (after hours).
