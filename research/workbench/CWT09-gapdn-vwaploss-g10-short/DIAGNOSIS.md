# Diagnosis: Gap-Down VWAP Loss Short (10% gap) (`CWT09-gapdn-vwaploss-g10-short`)
Mechanic, 2026-11-16 (batch "send every setup to the workbench"). Educational only — not financial advice.

Parent runs in **On Deck** (account `testing`, from session 2026-11-12); before that Testing A (testing2, 10-12..11-04)
and Testing C (Live Lab, 11-05..11-11). Leaderboard rank 6. Live record — **diagnosis only**, never part of the pass
decision (owner 2026-11-16): **18 trades / 11 sessions** 2026-10-13..11-13, avg **+0.301R** after costs, win 83%,
avg R w/o best day +0.215R (best day 2026-10-30 = 48% of total R — close to the one-big-day line).
**18 trades is far too few to tune on. This teardown leans on the 2-year backtest (545 parent trades) and the replay of
the live sessions (57 parent trades); the live trades are used only to see which part fired.**

Rule changes inside the live window (research/ledger.jsonl; none touches this setup's signal or exits): 10-20 twin-held
check + per-setup -2R latch in Testing 1/2; 10-23 per-setup latch off in the testing accounts; 10-30 CF cost filter
(skip if stop-exit cost > 0.15R) in Testing 1/2; 11-05 ROLL1 move to Live Lab (Testing C); 11-11 TEAM-6; 11-12 LR1
flatten time, LR5 position check, On Deck build (move to On Deck). So the trades come from three accounts and two cost
filters, but the same signal and exits.

Engine: `CWT09-gapdn-vwaploss-g10-short_engine.png` (parts P1..P22, as in `CWT09-gapdn-vwaploss-g10-short.md`).
Catalogue parts (PARTS_CATALOGUE.md) in brackets. Trade charts: `..._worst<k>_*.png`, `..._best<k>_*.png` (blueprint
engine teardowns; a no-target formatting bug in mcf/report/engine.py was fixed to draw them).

Symptoms -> catalogue: (a) one-big-day dependence (2-year best day = 108% of total R; live 48%) -> Refire / caps, Gates,
Intake; (b) 16 of 18 live trades end at the 15:55 flatten, 3 gave back a >= 1R peak -> Time exit, Target, Stop mgmt;
(c) 2 stop-outs = -2.1R of the record -> Sensors (entry quality), Stop. Every part was still inspected (below).

## Live signal funnel (all 319 live signals, 10-12..11-16)
284 (89%) blocked by **P5 short borrow** (not ETB), 10 by **P15 spread**, 1 halted, 1 price, 1 size; 22 orders / 18
closed trades. The replay below uses the same ETB / universe / earnings lists per day, so it scores what the parent can
actually trade; every one of the 268 live signals to 11-13 is reproduced by the replay code (signal bar matches 98.5%).

## The 5 worst and 5 best live trades (18 in all; replay R = the same trade re-simulated with the backtest engine)
| # | Trade | Live R | What happened | Part that decided it [catalogue] | WB1 below-open | WB2 first-hour close > VWAP | WB4 (WB1+WB2+ADV 20M) |
|---|---|---|---|---|---|---|---|
| W1 | CIFR 10-13, 10:31 @ 10.94, stop 11.32 (first-hour high) | -1.08 (stop 12:17) | gap -13.4%, 2.7% under the open, clean VWAP loss; squeezed back to the first-hour high | P9 sensor fired correctly; P16/P17 structural stop [Stop] did its job | kept (-1.12 replay) | kept | kept |
| W2 | SOXS 11-06, 11:37 @ 70.25, stop 73.07 | -1.04 (stop 12:36) | inverse 3x ETF, gap -19.6% but trading **+7.3% above its open** — the "VWAP loss" was a pause in an up-day | **P9 sensor: no "below the open" check** [Sensors] | **skipped** | kept | **skipped** |
| W3 | SNDX 10-13, 10:33 @ 13.61, stop 14.74 | -0.27 (flat) | never closed a 5-min bar above VWAP in the first hour (wick only); 1.37 ATR stop, drifted | **P9 sensor: wick-only bounce** [Sensors] | kept (-0.28) | **skipped** | **skipped** |
| W4 | VIR 11-13, 10:31 @ 9.96 | +0.05 (flat) | wick-only bounce, no follow-through | P9 [Sensors] | kept (+0.01) | **skipped** | **skipped** |
| W5 | HPQ 10-30, 13:36 @ 28.81 | +0.09 (flat; MFE +2.2R) | signal 3 h after the bounce, still **+5.5% above the open**; ran +2.2R then gave it all back | P9 sensor [Sensors]; P22 flatten [Time exit] | skipped | kept | skipped |
| B1 | ARCO 10-26, 11:00 @ 7.29 | +1.31 | above the open (+2.0%) at the signal; ADV $18.6M | P9 / P2 | delayed to the first bar under the open (+0.08 replay) | kept | skipped (ADV < $20M) |
| B2 | DELL 10-30, 10:30 @ 431.50 | +0.97 (MFE +1.9R) | above the open (+3.2%) at 10:30, then sold off | P9 | delayed (-0.20 replay) | kept | delayed (-0.20) |
| B3 | CLSK 11-04, 10:30 @ 7.14 | +0.91 | 0.2% under the open, close above VWAP at 10:00 | — | kept (+0.84) | kept | kept |
| B4 | TECL 10-30, 10:31 @ 177.19 | +0.88 (MFE +2.6R) | crash-day ETF, under the open | — | kept (+0.64) | kept | kept |
| B5 | SOXL 11-05, 10:32 @ 48.81 | +0.69 | 15% under the open, wick-only bounce | P9 | kept (+0.42) | skipped | skipped |

**Honest read of the live sample:** on these 18 trades the two sensor parts are a wash — below the open 13 trades
+0.306R vs above 5 trades +0.288R; first-hour close above VWAP 14 trades +0.317R vs wick-only 4 trades +0.246R. WB4 would
have kept 9 live trades (+0.333R avg), delayed 2 (DELL, SMCI: -0.20 / -0.06 replay) and skipped 7 (incl. the ARCO
+1.31R winner and the SOXS -1.04R loser): about +0.25R on 11 trades vs the live +0.30R on 18. The case for the copy rests
on the 2-year backtest and the 57-trade replay, not on these 18 trades.

## All trades — component by component (2-year test 2024-10..2026-10-09, 545 parent trades, avg +0.079R; replay 57, -0.139R)
| Part [catalogue] | Evidence | Lead? |
|---|---|---|
| P1/P2 intake: gap size [Intake] | gap >= 8%: 2y +0.045 / replay -0.106; >= 12%: +0.095 / -0.182; >= 15%: +0.144 / -0.215 (2y and replay disagree) | no |
| P1/P2 intake: ADV floor [Intake] | ADV >= $20M: 2y +0.093 / replay -0.134 (w/o best day -0.219); >= $50M: +0.123 / -0.118 (w/o best day -0.218). Helps 2y, alone it fails the replay one-big-day test | yes, as a layer (WB4) |
| P1 intake: ETFs [Intake] | no ETFs: 2y +0.026 / replay -0.067 (leveraged ETFs carry the crash days) | no |
| P3 price, P4 earnings, P5 borrow, P15 spread | live gates; applied as live in both tests (2y has no earnings history: no blackout there, same for every copy) | not a knob |
| P6 window end [Timer] | end 11:00 / 12:00 / 13:00: replay -0.088 / -0.103 / -0.127, 2y +0.077 / +0.059 / +0.051 — late signals are fine over 2 years | no |
| P8 refire | first bar per symbol-day; nothing to change | no |
| P9 sensor: VWAP loss depth [Sensors] | close >= 0.5% under VWAP: 2y +0.083 / replay -0.117 (passes, small); >= 1.0%: 2y +0.042 (fails) | weak |
| **P9 sensor: below the day open** [Sensors] | fromOpen < 0 at the signal bar: 2y +0.084 (w/o best day +0.021 vs -0.006), replay **-0.023** (vs -0.139), replay stops 15 -> 7. A "VWAP loss" while still above the open is a pause in a recovery, not a failed bounce (SOXS, HPQ) | **yes -> WB1** |
| **P9 sensor: real bounce (a 5-min close above VWAP 09:35-10:30)** [Sensors] | 2y **+0.109**, worst day -7.1 vs -14.2R; replay -0.149 (about equal). Wick-only bounces never had buyers to trap | **yes -> WB2** |
| P9 sensor: bounce size >= 0.15 ATR | 2y +0.089 / replay -0.177 | no |
| P16/P17 1R = structural distance | stop distance <= 1.0 ATR: 2y +0.101 / replay -0.179; >= 0.3 ATR: +0.092 / -0.093 (passes; overlaps WB1) | weak |
| Gates (SPY since 09:50, measured after 09:50) | SPY <= 0: 2y +0.096 / replay -0.005 (w/o best day 2y -0.017); <= +0.25%: +0.076 / -0.153; >= -0.25%: +0.104 / -0.079 (replay w/o best day -0.237) — no clean gate | no |
| Stop (cap the structural stop at 0.5 / 0.75 / 1.0 ATR; signal-bar/VWAP stop) [Stop] | 2y +0.007 / +0.053 / +0.071 / -0.088 — the first-hour high is the right stop | no |
| Target 1R / 2R / 3R [Target] | 2y -0.009 / +0.012 / +0.012 (replay +0.016 / -0.062 / -0.139) — the edge is the all-day drift; a target cuts it | no |
| Stop mgmt: BE after +1R; trail 1R after +1R; lock +0.5R after +1.5R | 2y +0.078 / +0.031 / +0.069 (replay -0.125 / -0.079 / -0.125) | no (BE re-tested on WB3: +0.148 2y but replay -0.013 — not kept) |
| P22 time exit 13:00 / 14:00 / 15:00 [Time exit] | 2y -0.012 / -0.018 / +0.020 vs +0.079 (replay up) — the afternoon pays over 2 years | no |
| P10-P14 caps / latch | never bound live (0 of 319 signals) | no |
| Day type (2y, end-of-day SPY label, diagnostic) | up -0.362 / flat +0.268 / down +0.250 — up days lose; no gate measured after 09:50 fixes it without hurting the replay | noted |

Shortlist: **WB1** (below the open), **WB2** (first-hour close above VWAP), **WB3** = WB1 + WB2, **WB4** = WB3 + ADV >= $20M.
Results and every other config: RESULTS.md.
