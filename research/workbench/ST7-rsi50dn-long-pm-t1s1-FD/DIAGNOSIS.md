# Diagnosis: RSI Collapse Dip Buy (all day) `ST7-rsi50dn-long-pm-t1s1-FD` (Primary, leaderboard rank 9)
Mechanic, 2026-11-16 (built during market hours; nothing in any config changed). Educational only — not financial advice.

Live record used for diagnosis only (owner: the parent's live stats do not decide a pass): 43 trades / 15 sessions,
2026-10-12..11-13, avg +0.150R, win 58%, avg R w/o best day +0.061R (best day 10-12 = 63% of R, "1 day" — PBF +3.78R was
carried overnight, an exit no backtest can make). Primary 27 trades +0.12R, Testing 1 (as On Deck) 16 trades +0.20R.
Rule changes inside that window (ledger): promotion Testing 1 -> Primary 10-26 (move), Primary size ~$4-5k and per-setup
cap 30 (10-28), Primary -2R per-setup latch (10-29), Testing cost filter CF 0.15R (10-30, Testing only), LR1/LR3/LR5/LR7
(11-12). The replay below applies today's Primary rules to every session, so none of these mixes into the comparison.

## Teardown (engine view, `ST7-rsi50dn-long-pm-t1s1-FD_engine.png`, blueprint `ST7-rsi50dn-long-pm-t1s1-FD.md`)
P1 universe (ADV >= $5M, ATR >= 1%) · P2 ADV20 >= $95M · P3 price >= $5 · P4 earnings blackout · P5 window 09:50-15:00 ·
P6 no entries before 09:50 · P7 first bar per symbol-day · P8 RSI(14) crosses below 50 · P9 RSI(14) <= 30 · P10 down > 1%
from the open · P11 19-bar buy pressure > 0 · P12 30 open lots · P13 3 lots/symbol · P14 -2R latch · P15 -20R account ·
P16 quote/spread checks (blocked 24 of 73 live signals) · P17 long at market · P18 1R = 0.25 x ATR · P19-20 size ·
P21 stop 1R · P22 target +1R · P23 no scale-out · P24 flat 15:55.

## The 5 worst and 5 best live trades
| Trade | What happened | Part responsible | Small tweak and its effect on THIS trade |
|---|---|---|---|
| FNB 11-04 10:45, -1.33R stop | 1R only $0.10 on an $18.50 stock; went +0.61R, then stopped; costs turned -1.12R gross into -1.33R | P18 1R vs P1 intake (cost/R 0.45) | cost/R <= 0.10-0.15 skips it; SPY gate keeps it (SPY -0.11% since 09:50) |
| CSX 10-29 10:45, -1.25R stop | Faded alone while SPY was up +0.26% since 09:50; never better than +0.15R | Gates (none) | skip-when-SPY-up > +0.10% (WB1) skips it |
| KEY 11-04 10:45, -1.20R stop | Touched +1.00R (target needs a 1c trade-through), then stopped; 1R $0.10 | P22 / P18 cost | cost/R skips it; WB1 keeps it (SPY -0.11%) |
| SMR 10-21 13:50, -1.19R stop | $5.61 stock, 1R $0.13; RSI collapsed on a 1-cent drift while SPY was +0.36% since 09:50; slid into the stop at 15:09 | Gates (none) + P3/P18 | WB1 skips it; cost/R skips it |
| Z 10-21 13:50, -1.12R stop | Same 13:50 bar as SMR (one bet twice) with SPY +0.36%; best +0.21R | Gates (none) | WB1 skips it |
| PBF 10-12 10:45, +3.78R | Ran +3.85R; the 1R target did not fill; carried overnight (live artefact) | P22 | — (backtests flatten it; not reproducible) |
| KR 10-30 10:45, +1.47R target | Market dipping too (SPY -0.05% since 09:50) | — | WB1 keeps it |
| IBN 11-05 10:45, +1.26R target | SPY -1.46% since 09:50: classic "dip with the market" | — | WB1 keeps it |
| WCN 10-30 10:45, +1.14R target | SPY -0.05% | — | WB1 keeps it |
| RF 11-04 10:45, +1.05R target | SPY -0.11% | — | WB1 keeps it |

## All 43 live trades — which part is behind the losses
- **Market state at entry is the dividing line (Gates, no part today).** SPY since its 09:50 close at the signal bar
  (35 trades with frames): <= 0: 24 trades +0.43R avg; > 0: 11 trades -0.24R. All of the five 10-21 / 10-29 stops fired
  while SPY was rising — the stock was falling alone. 2-year backtest of the parent: trades with SPY up > +0.10% since
  09:50 = 325 trades -0.12R (on down-closing days -0.80R), the rest 684 trades +0.08R.
- **Stops are not "too tight".** 10 of 12 live stops never got to +0.5R first (MFE median +0.15R); a wider stop (1.25R)
  or break-even move does nothing useful (2-year +0.014 / -0.018).
- **Thin-R names (P18 vs cost).** 23 of 43 live trades had stop round-trip cost > 10% of 1R (FNB 0.45, KEY 0.44, HBAN 0.50,
  RIG 0.83); they averaged +0.13R vs +0.17R — cost drag, not the main failure. The 2-year test agrees it helps a little.
- **Time exits (P24)** — 13 trades flattened at 15:55, +0.31R avg (PBF), +0.02R without PBF: neutral; the time-stop and
  max-hold copies hurt the 2-year test.
- **10:45 bar (P5/P8 RSI gap artefact, st7_1022):** live the 10:45 bar is the GOOD part (28 trades +0.39R vs 15 others
  -0.30R); skipping it (V01/V02) loses in both tests. Not a fix.
- **Up days (the long side's weak spot):** 2-year parent by SPY day type up +0.17 / flat +0.03 / down -0.14R.

Candidate tweaks (one part each): gate "skip when SPY is up since 09:50" (+0.30 / +0.20 / +0.10 / 0.00 / -0.10%),
cost/R intake, ATR >= 2%, price >= $10, fromOpen < -1.5, buy pressure > 0.10, window, exits. All scored in RESULTS.md.
