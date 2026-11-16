# Diagnosis: Failed Opening-Range-Low Break Long (0.1 ATR) [fill] (`CWT14-failbrk-orl-p10-long`)
Mechanic, 2026-11-16. Educational only — not financial advice.

Parent runs in **Graveyard** (moved there from Testing 2 on 2026-10-21). Live record used here for **diagnosis only**
(owner 2026-11-16: the pass decision uses the identical backtests, never the parent's live stats): 723 trades,
25 sessions 2026-10-12..11-13, avg -0.085R after costs, win 65%, avg R w/o best day -0.109R.
Rule changes inside that window: Testing 2 live scale-out (10-17), moved to Graveyard (10-21), Graveyard -2R latch
kept / testing-account latches off (10-23), Graveyard BP 3.8 -> 1.6 and per-setup cap 25 -> 75 (11-12), LR1 flatten
time and LR5 position check (11-12), LR8 live cost model (11-12). So the 10-12..10-20 Testing 2 trades (scale-out on)
and the Graveyard trades (no scale-out, -2R latch) are not the same rules.

Engine: `CWT14-failbrk-orl-p10-long_engine.png` (parts P1..P21, as in `CWT14-failbrk-orl-p10-long.md`).
Catalogue parts (research/workbench/PARTS_CATALOGUE.md) are named in brackets.

## The 3 trades

### Worst 1: VXX 2026-10-15 (testing2 #3283), -2.62R, stop (`..._trade1_VXX_2026-10-15.png`)
The 09:30-10:00 low (OR low) was 17.485; VXX poked to 17.40 (0.19 ATR under) and the 10:30 bar closed back above at
17.505 (signal). Daily ATR 0.44 (2.5% of price), so 1R = 0.11. Live decided 10:33:53 (3.9 min after the bar closed)
and filled 17.41 — already 0.86R below the signal close; the stop stayed at 17.395 (signal close - 1R), so only
$0.015/share of risk was left. The stop hit 30 s later at 17.39. Loss $1.06 raw / $2.12 after the stop allowance:
tiny in dollars, -2.62R because the R denominator had shrunk to $0.015.

| What happened | Which part [catalogue] | What a small tweak would have done to THIS trade |
|---|---|---|
| Fill 0.86R below the signal close, stop not moved: R shrank to $0.015 | P14 entry / latency [Entry / sizing] + P15 1R | WB1 (1R = 0.30 ATR): stop 17.373, risk $0.037 -> about -1.5R instead of -2.6R (replay: -1.42R -> -1.35R) |
| The reclaim failed; VXX fell to 17.0 by 11:15 | P8 sensor [Sensors] | No tested sensor change filters it (poke 0.19 ATR, reclaim 0.045 ATR are mid-range) |
| Window | P5 [Timer] | WB2 (start 10:30) still takes it (signal bar 10:30) |
| Intake | P1 [Intake] | WB3 (ATR >= 2.0%) still takes it (2.5%) |
| — | P14 drift guard (untested idea) | "skip if the price is > 0.5R from the signal close at order time" would have skipped it — runner-level, not a spawn parameter; not tested, not counted |

### Worst 2: UVXY 2026-10-15 (testing2 #3279), -2.24R, stop (`..._trade2_UVXY_2026-10-15.png`)
Same minute, same mechanism: OR low 17.03, low 16.92 (0.17 ATR poke), 10:30 signal close 17.06; ATR 0.632 (3.7%),
1R = 0.158. Decided 10:33:45, filled 16.92 (0.89R under the signal close), stop 16.902 -> $0.018 risk; stop 10:34:20
at 16.90, $1.08 raw loss = -2.24R.

| What happened | Which part [catalogue] | What a small tweak would have done to THIS trade |
|---|---|---|
| Late fill far below the signal close, stop not re-anchored | P14 / P15 [Entry / sizing] | WB1: risk $0.05 -> about -1.4R (replay -1.31R -> -1.26R) |
| Volatility ETP squeeze down at 10:33 | P8 [Sensors] | none of the tested tweaks removes it |
| Window / intake | P5 / P1 | WB2 and WB3 both still take it |

### Best: BABA 2026-11-05 (graveyard #10085), +1.86R, target (`..._best1_BABA_2026-11-05.png`)
OR low 106.31, low 106.00 (0.10 ATR poke, just at the threshold), 10:10 signal close 106.33; ATR 3.07 (2.9%), 1R 0.77.
Filled 10:11:43 at 105.97 (0.47R under the signal close), stop 105.566, target 106.712 hit 10:16:34 (+1.86R). The
mirror image of the two losers: fill drift away from the signal close inflates a winner's R.

| What happened | Which part | What the tweaks do to THIS trade |
|---|---|---|
| Quick target, fill below signal close made R small | P14 / P15 | WB1: +2.29R -> +1.73R in the replay (wider R, same exit) |
| 10:10 signal | P5 | WB2 (10:30 start) skips it (and the 10:25 re-signal that the replay stops out) |
| ATR 2.9% | P1 | WB3 keeps it |

**The two worst trades are an R-measurement artefact of entry latency (P14), not a big dollar loss.** The R-size
part (P15) is the only tested part that softens them.

## All live trades (723) — component by component
| Part [catalogue] | Evidence (live, diagnosis only) | Evidence (2-year TRAIN split only, 2024-10..2025-12, 28,116 replayed trades, avg -0.151R) | Lead? |
|---|---|---|---|
| P1 intake ATR% [Intake] | ATR 1-2%: -0.18R, 2-2.9%: -0.26R, 2.9-4%: -0.07R, > 4%: -0.04R (406 trades matched to frames) | ATR < 1.8%: -0.234R; > 4.1%: -0.108R; risk < 0.42% of price: -0.289R vs > 0.73%: -0.10R | **Yes -> WB3** (ATR >= 2.0%) |
| P2 ADV floor [Intake] | flat across ADV quartiles except top (-0.08R) | ADV >= $150M: +0.004R | no |
| P5 window [Timer] | entries 10:05-10:30: 397 trades -0.148R; 10:30-12:00: 326 trades -0.009R | gradient weak: 10:05-10:25 -0.15/-0.19R, 11:05-12:00 -0.115R; start 10:30 +0.017R | **Yes -> WB2** (10:30 start; live is the strongest evidence) |
| P7 refire / P9-P12 caps [Refire / caps] | -2R latch blocked 378 of 1,684 live signals (22%); quote checks 17% | not modelled (isolated test) | no (account-level) |
| P8 sensor depth / reclaim [Sensors] | poke depth / reclaim size quartiles all -0.10..-0.20R | poke >= 0.15 ATR (p15): +0.001R; reclaim > 0.08 ATR -0.21R, cap at 0.08: +0.015R | weak (tried, not shortlisted) |
| Gates: market day type [Gates] | — | 2y: up days -0.009R, flat -0.124R, down -0.227R | **strongest untested lead** -> backlog idea, not built (a gate is a new condition, beyond a one-part tweak here) |
| P14 entry latency [Entry / sizing] | fill drift vs signal close: fills > 0.12R below the signal close -0.20R, > 0.13R above -0.03R; the worst trades come from it | — (backtest fills 1 min after the bar) | idea only (runner-level) |
| P15 1R size / P18 stop [Stop] | 222 stops = -254R; 37 of them had first gone >= +0.4R (almost to target) | stop x1.2 alone: -0.114R (+0.037); 1R x1.2 (stop and target): -0.116R (+0.035); stop x0.8: -0.211R; 9.8% of base stop-outs win with the wider stop | **Yes -> WB1** (r_atr_frac 0.30 — the spawnable form; stop-only width is not a spawn parameter) |
| P19 target [Target] | 466 targets +204R | target 0.4R: -0.149R (+0.002); 0.6R: -0.155R | no |
| P20 scale-out [Target / scale-out] | Testing 2 ran it 10-17..10-20 | half at +0.35R, rest to breakeven: -0.172R (worse) | no |
| P21 time exit [Time exit] | 35 flatten exits -11.5R (-0.33R each) | flat at 13:00 instead of 15:55: -0.151R (no change; median hold 20 min) | no |

Shortlist (each one part): **WB1** P15 1R 0.25 -> 0.30 x ATR, **WB2** P5 window 09:50 -> 10:30 start, **WB3** P1
extra intake filter ATR >= 2.0% of price; plus **WB4** = WB1 + WB3 (each passed alone; counted as its own config).
Results: RESULTS.md.

---
# Rerun (supervisor standard, owner 2026-11-16): 5 worst + 5 best live trades, every part again
Mechanic rerun, 2026-11-16 (during market hours; research files only). Educational only — not financial advice.
Live record now (diagnosis only, not in the pass decision): 735 trades / 26 sessions 2026-10-12..11-16, avg -0.079R after
costs, win 65%, w/o best day -0.101R. Rule changes in the window as above (Testing 2 scale-out 10-17, Graveyard move
10-21, latch policy 10-23, Graveyard BP / caps + LR1 / LR5 / LR8 on 11-12); no rule change for this setup after 11-12.
Engine: `CWT14-failbrk-orl-p10-long_engine.png` (refreshed). Trade teardowns `..._rerun_worst{1-5}_*.png`,
`..._rerun_best{1-5}_*.png` (every price and time on the chart).

## The 5 worst and 5 best live trades, and what WB5 does with each
"1R" is the live R denominator |fill - stop|; drift = (fill - signal close) / 1R(0.25 ATR); cost/R = WB5's intake test
(2 x (1c + 1 bp) + 2c) / (0.30 ATR); SPY = SPY since 09:50 at the decision bar (gate needs >= -0.20%).

| Trade | Live R | What happened | Part | drift | cost/R | SPY since 09:50 | WB5 |
|---|---|---|---|---|---|---|---|
| W1 VXX 10-15 10:30 | -2.62 | filled 0.86R under the signal close, 1R shrank to $0.015, stop 30 s later | P14 / P15 | -0.86 | 0.33 | +0.16% | **skipped** (cost/R) |
| W2 UVXY 10-15 10:30 | -2.24 | same minute, same mechanism | P14 / P15 | -0.89 | 0.23 | +0.16% | **skipped** (cost/R) |
| W3 KEY 11-04 10:05 | -2.10 | $21 bank, ATR 2.0%: 1R $0.02 after drift, stop in 9 s | P1 / P14 | -0.81 | 0.35 | +0.11% | **skipped** (cost/R; WB4 ATR >= 2% also borderline) |
| W4 ORCL 11-06 11:25 | -1.84 | real failure: the reclaim faded, stop 12:36, ORCL fell to 109 | P8 sensor | -0.16 | 0.03 | -0.05% | taken; stop 112.90 (0.45 ATR) also hit at 12:36 -> about -1.0R |
| W5 FNB 11-04 10:05 | -1.80 | $18 bank, 1R $0.04, stop in 39 s | P1 / P14 | -0.61 | 0.37 | +0.11% | **skipped** (cost/R) |
| B1 BABA 11-05 10:10 | +1.86 | target in 5 min (R inflated by a fill under the signal close) | P19 | -0.47 | 0.07 | -0.54% | **skipped** (gate) |
| B2 VTWO 10-14 10:10 | +1.82 | target 10:44 | P19 | — | 0.15 | -0.41% | skipped (ATR 1.2% < 2%: already out in WB4) |
| B3 TNA 10-14 10:10 | +1.74 | target 10:44 | P19 | — | 0.08 | -0.41% | **skipped** (gate) |
| B4 TRGP 11-16 10:15 | +1.62 | target 10:31 | P19 | — | ~0.05 | n/a (today, no cached SPY) | intake passes; gate not checkable here |
| B5 PLTR 10-16 10:05 | +1.55 | target in 8 min | P19 | — | 0.04 | -0.10% | taken; replay +0.96R (wider stop: smaller R on the same target) |

Reading: 4 of the 5 worst are the same machine fault — a thin 1R on a cheap name, shrunk further by a fill under the
signal close, so a few cents of noise is -2R. One intake part (cost-to-R) removes all four without touching the signal.
The 5th (ORCL) is a genuine failed reclaim; the wider stop does not save it but halves its R. The gate gives back 2-3
of the 5 best (they fired on mornings where SPY was falling after 09:50 and then turned) — that is where the copy gives
something back.

## All trades — every part again (2-year TRAIN split, on WB4's trade set unless noted)
| Part [catalogue] | Evidence | Lead? |
|---|---|---|
| P1 intake: cost-to-R [Intake] | the R-shrink losers all have cost/R > 0.20; cost/R <= 0.10 vs WB4: train -0.096 -> -0.080, 2y -0.079 -> -0.061, replay -0.101 -> -0.080 (paired vs WB4 t 7.5 on 2y) | **Yes -> C1** |
| Gates: SPY since 09:50 [Gates] | >= 0: replay +0.015 but 2y -0.079 (no gain); >= -0.10%: 2y -0.077; **>= -0.20%: 2y -0.072, replay -0.053, worst day 2y -151 -> -77R**; SPY range / VWAP / breadth gates weaker or inconsistent (RESULTS) | **Yes -> G3** (mainly a worst-day / down-day part) |
| P14 entry drift [Entry] | in the backtest (1-minute fill) |drift| > 0.5R is rare: guard 0.5R changes avg R by +0.002; the runner's own cost filter at the fill (Testing max_stop_cost_r 0.15) does more (-0.063 2y) and C1 already contains it | covered by C1 (+ the Testing CF) |
| P7 refire / lots [Refire / caps] | max 2 lots per symbol (2nd after a 10-min cooldown or after the 1st exits): -0.078 / -0.080 2y, worst day worse (-179R) | no |
| P5 window [Timer] | 10:15 start: 2y -0.072 but replay -0.112; 10:30 start: replay -0.142; 09:50-11:00: -0.083; to 13:00: -0.079 | no (inconsistent across tests) |
| P18 stop width [Stop] | stop 1.2R: 2y -0.062; on C1+G3: 1.0R -0.050, 1.2R -0.038, **1.5R -0.027**, 2.0R -0.020 (2y); per $ traded 2y -5.6 / -5.1 / -4.6 / -4.2 bps — part of the R gain is the bigger denominator, but the per-notional loss also shrinks | **Yes -> stop 1.5R** |
| P19 target [Target] | 0.7R: -0.080 (worst day -191R); 0.4R with stop 1.5R: -0.028 (no better than 0.5R) | no |
| Exit management [Time exit / Target] | breakeven after +0.3R -0.094; max hold 30 / 60 min -0.095 / -0.086; trail without target -0.118; levels from the fill -0.076 (all on WB4, 2y); on C1+G3: structural stop under the poke low -0.073 (replay -0.125), breakeven after +0.4R with stop 1.2R -0.045, stop 1.5R + max hold 60 -0.035 | no |
| Day caps [Refire / caps] | -10R / -20R setup latch -0.081 / -0.080; first 40 trades/day -0.082 2y but replay -0.017 and worst day -40R | account-level idea (no per-setup trades/day knob) |
| Sensors (poke, reclaim, RSI, VWAP, flow, gap, rel. strength, ADV, price) | quintiles on the C1+G3 set are flat within ±0.03R and flip sign between train and valid | no |
