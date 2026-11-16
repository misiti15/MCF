# Diagnosis: 20-Minute Opening Range Breakout (`orb20_a`)
Mechanic, 2026-11-16 (built during market hours; research files only, no config touched). Educational only — not financial advice.

Parent runs in **On Deck** (`config/account_testing.yaml`; demoted from Primary 2026-10-11). Live record, used here for
**diagnosis only** (owner 2026-11-16: the pass decision uses the identical backtests, never the parent's live stats):
42 trades / 19 sessions 2026-10-06..11-12 (Primary 9, On Deck 33), avg **-0.012R** after costs, win 48%, avg R w/o best
day **-0.145R**. Leaderboard rank 23. 42 trades is a small sample, so the parts are judged mainly on the 2-year backtest
(2,710 trades) and the replay (209 trades); the live trades show the failure modes.

Rule changes inside the live window (research/ledger.jsonl, 15 entries): probation after the Apr-Jun holdout (10-07),
Primary -> Testing demotion (10-12), twin rule / -2R setup latch in Testing (10-20) and the latch off again (10-23, ST-A),
Primary sizing changes (10-28) and Primary -2R latch (10-29), the 0.15R stop-cost filter in Testing 1/2 (10-30), LR1
flatten time / LR3 / LR5 / LR7 (11-12). The 10-06..10-09 Primary trades and the On Deck trades do not run under one rule set. The backtests apply one rule set throughout (LR8 costs, no latch, no caps).

Engine: `orb20_a_engine.png` (P1..P20). Note: `python -m mcf.report.blueprint orb20_a` reads this builtin as if it were a
lab setup (it prints window 09:50-15:00, 1R = 0.25 ATR, t1s1 — none of which is this setup). The engine image here is
drawn from the ORB20 class itself (mcf/strategies/research_setups.py):

| Stage | Part | Setting |
|---|---|---|
| Intake | P1 account universe | ADV >= $5M core (extended $1M with rvol >= 3), ATR >= 1% |
| | P2 liquidity check (class) | prior close >= $5, ATR >= $0.50, avg >= 1M shares/day |
| | P3 earnings blackout / PTP | 4 days either side / excluded |
| | P4 stocks in play | top 20 by 09:30-09:49 relative volume (rank_rvol20) |
| | P5 rvol floor | 09:30-09:49 rvol >= 1.5 |
| Timer | P6 opening range | 09:30-09:49 high / low, known at 09:50 (no entry before 09:50) |
| | P7 entry window | stop order works 09:50-11:30 |
| | P8 refire | one order per symbol-day |
| Sensors | P9 direction | long if 09:49 close > 09:30 open, short if below |
| | P10 VWAP agreement | 09:49 close on the trade side of VWAP |
| Gates | P11 caps / latch / account stop | 150 lots, 3 per symbol, latch off, -300R |
| | P12 cost filter | skip if stop cost > 0.15R (live) |
| | P13 quote / spread | spread <= 30 bps and <= 0.25 of stop |
| | P14 borrow | shorts ETB only |
| Entry | P15 order | buy stop at high +1c / sell stop at low -1c (live: "missed" if it traded through on an earlier bar) |
| | P16 size | min(0.25% equity at risk, slot) |
| Exhaust | P17 stop | 0.5 x range beyond the entry level (= 1R) |
| | P18 target | 0.75 x range (= +1.5R) |
| | P19 time exit | 15:50 (class exit_by) / flatten 15:55 live |
| | P20 scale-out / management | none |

## The 5 worst live trades
Charts `orb20_a_worst{1-5}_*.png` (every price and time printed; callouts A-D name the part). "Lab rank" = rank_rvol20
inside the 1,226-name research universe (the live runner ranks ~3,900 names, so live and lab ranks differ; names outside
the research universe have no lab rank).

### Worst 1: IXUS 2026-10-23 (On Deck #5814), long, -1.36R, stop
09:30-09:49 range 92.03-92.27 = **0.24 x ATR** (an international-equity ETF on a quiet morning). 1R = $0.08 = 0.09% of
price, so a round trip plus stop slippage cost ~0.9R. Filled 92.24 at 09:54, peaked +1.5R at 10:00, fell through the stop
(92.16) at 10:10, then went on to the target (92.45) at 11:27 — the stop sat inside the noise.

| What happened | Part | What a small tweak would have done to THIS trade |
|---|---|---|
| Range 0.24 ATR: stop $0.08 wide, costs ~0.9R | P6 range / P17 stop | range >= 0.3 ATR skips it; stop 0.75 / 1.0 x range (92.11 / 92.05) is still hit (low 91.88) |
| Lab rank 14 of 20 | P4 stocks in play | top 10 (WB1 / WB3) skips it |
| $92 ETF | P2 price | price >= 20 keeps it |

### Worst 2: ILF 2026-10-23 (#5813), long, -1.30R, stop
Range 37.12-37.30 = 0.23 ATR; 1R $0.10 (cost ~0.48R). Filled 37.32 at 10:00, MFE +0.1R, stopped 10:05.

| What happened | Part | Tweak |
|---|---|---|
| Thin range, immediate failure | P6 / P17 | range >= 0.3 ATR skips it |
| Not in the research universe (no lab rank) | P4 | unknown; price >= 20 keeps it |

### Worst 3: CART 2026-10-27 (#6355), short, -1.18R, stop
Range 59.82-60.81 = 0.39 ATR; short break at 59.81 filled 59.77 at 09:59, MFE +0.15R, drifted back over VWAP and stopped at
60.38 at 10:59 (the breakdown failed).

| What happened | Part | Tweak |
|---|---|---|
| Failed breakdown | P9 / P10 sensors | none of the tested sensor tweaks (move >= 0.25 ATR, close in the outer third) skips it |
| Lab rank 13 | P4 | top 10 skips it |

### Worst 4: AVPT 2026-10-28 (#6631), long, -1.14R, stop
$17 stock, range 0.75 ATR, filled 17.43 at 09:51 with **20 bps slippage**, stopped 10:00 (MFE +0.18R).

| What happened | Part | Tweak |
|---|---|---|
| Low-priced name, wide spread / slippage | P2 price | price >= 20 (WB2 / WB3) skips it |

### Worst 5: BRZE 2026-10-20 (#4329), short, -1.13R, stop
Range 45.28-45.58 = **0.20 ATR**; 1R $0.15 (cost ~0.33R). Filled 45.27 at 10:40, never more than +0.07R, stopped 11:56.

| What happened | Part | Tweak |
|---|---|---|
| Thin range, late (10:40) break | P6 / P7 | range >= 0.3 ATR skips it; window to 10:30 skips it |
| Not in the research universe | P4 | unknown |

## The 5 best live trades (contrast)
| Trade | R | What the copy (WB3: top 10 + price >= 20) does |
|---|---|---|
| CQQQ 10-15 long (best1) | +1.68 target | kept by price ($41); not in the research universe (rank unknown) |
| AVEX 10-22 short (best2) | +1.59 target | **lost** (price $10.5) |
| GMAB 10-28 long (best3) | +1.53 target | kept (lab rank 10, $45; a 6-ATR range after news) |
| BKH 10-07 long (best4) | +1.44 target | kept by price ($76); rank unknown |
| SCZ 10-08 long (best5) | +1.38 target | kept (lab rank 4); a range >= 0.3 ATR filter would have LOST it (0.27 ATR) |

## All live trades (42)
- Exits: 14 stops (-1.11R avg), 10 targets (+1.30R), 18 flattens (+0.12R). Longs +0.058R (25), shorts -0.116R (17).
- Price: < $20 13 trades -0.045R; >= $20 29 trades +0.002R.
- Lab rank (19 trades in the research universe): rank <= 10 13 trades **+0.25R**; rank 11-20+ 6 trades **-0.45R**.
- Trades the recommended copy would keep (price >= $20 and not a known rank > 10): 24 trades +0.071R.
- Thin ranges: 4 of the 5 worst had a range of 0.20-0.39 ATR; stop-cost-to-R > 0.4R on 3 trades (-0.43R avg).
- Signals: 21 "missed: triggered at 09:50" (live never takes a 09:50 trigger; the backtest does), 8 not shortable, 6 split-tape
  gate (10-12..10-14, gate now off), 3 cost filter, 7 spread.

## Across ALL backtest trades (2-year, 2,710 trades, parent)
| Component | Split (avg R after costs) |
|---|---|
| P2 price | <$10 41 tr -0.518; $10-20 222 tr -0.055; $20-50 765 -0.029; $50-100 885 +0.000; >$100 797 -0.035 |
| P4 rvol rank | 1-5 649 tr +0.024; 6-10 668 -0.033; 11-15 700 -0.055; 16-20 693 -0.055 |
| P6 range width | < 0.3 ATR 120 tr -0.199; 0.3-0.5 286 -0.088; 0.5-1.0 879 -0.030; 1.0-1.5 664 -0.000; > 1.5 761 -0.010 |
| P7 entry time | 09:50-09:55 1,492 tr -0.015; 09:55-10:00 364 -0.021; 10:00-10:30 600 -0.037; 10:30-11:30 254 -0.125 |
| P9 side | long 1,435 -0.033; short 1,275 -0.028 |
| P17-P19 exits | stop 40% (-1.13R), target 27% (+1.44R), time 33% (+0.13R); only 8.7% of stops had first reached +1R |

**Which part is most often responsible for the losses:** the intake (P2 / P4) — the setup is a stocks-in-play breakout,
and the lower half of the "in play" list and the cheap names carry the losses (rank 11-20: -0.055R on 1,393 trades;
<$20: -0.12R on 263 trades). The stop is not the problem in the usual sense (only 8.7% of stopped trades had reached
+1R first; wider or tighter stops trade one test against the other), and the exits are close to optimal for this target
(every exit / management change tested lost in the 2-year test). Thin ranges (P6) are the second source (< 0.5 ATR:
-0.12R on 406 trades), but a range filter costs the replay (it removes good thin-range ETF breaks like SCZ).

Candidate tweaks (each one part): **P4 top 20 -> top 10** (WB1), **P2 price floor $5 -> $20** (WB2), and their
combination (WB3). Results: RESULTS.md.
