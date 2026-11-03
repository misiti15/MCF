Educational only — not financial advice

# ex30 / xsec — cross-sectional rank setups: results (2026-11-03)

Pre-declared in PLAN.md (committed 33ddb6ace before any scoring). **39 configurations scored** (5 primaries, 10
neighbours, 24 information-only true-rank configs). **0 of 39 pass the light lane gate.** 0 of 5 delivered setups pass.
Locked block 2024-11-01..2025-02-28 never loaded. Costs in (gates.lab_trades production + time-of-day entry).
TRAIN = 234 sessions (2024-10, 2025-03..12), VALID = 114 sessions (2026-01..03, 2026-07-01..09-15). Backtest only — no
live or paper result exists for any of these. Files: `score.py`, `report.py`, `results.csv` (every config), `parity.csv`,
`modules/` (the 5 setups).

## Failures first

1. **Every primary is negative on TRAIN and on VALID** (avg R -0.04 to -0.17, day-clustered t -0.8 to -6.1). The gate
   needs >= -0.02 on both; none come close except XS4 on VALID (-0.039, t -0.82), which is -0.119 on TRAIN.
2. **The "against the tape" designs are still tape bets.** XS1 (short the laggard on a green tape) fires 67% of its TRAIN
   trades on SPY up days and loses -0.21R there; XS2 (buy the leader on a red tape) fires 70% on down days and loses
   -0.25R. Being in the universe's strong/weak tail does not protect a trade from the session's direction. Their edge over
   the day-matched random entry is small and positive in both splits (XS1 +0.005/+0.040R, XS2 +0.028/+0.022R; t <= 0.85),
   i.e. the relative-strength filter adds a little, but nowhere near the ~0.12-0.18R cost-and-direction hole.
3. **The quiet-day design does not make money on quiet days.** XS3/XS4 (fade the top/bottom outlier while SPY is flat and
   breadth is balanced) are -0.19/-0.12R (TRAIN) and -0.10/-0.08R (VALID) on quiet days. They are positive only when the
   day later trends their way (XS3 short +0.21R on TRAIN down days, XS4 long +0.23R on VALID up days). As a basket they
   are market-neutral in exposure but not in R: both legs lose on quiet days.
4. **The rank-change design (XS5) is the worst** (-0.11 / -0.15R, below random in both splits, t -1.8 / -2.2 vs random) and
   trades 36/session, above the 25 cap.
5. **True universe ranks (grid T, not live-runnable) are no better.** All 24 are negative on TRAIN (-0.03 to -0.15R).
   Two are about flat on VALID (vwapATR-1000 bottom10 momentum short +0.009R, vwapATR-1300 top10 fade short +0.005R),
   both negative on TRAIN (-0.14 / -0.10R) and both shorts with the usual up-day loss (-0.25 / -0.16R). With 24 tries,
   2 near-zero VALID results is what chance would give. The rank method by itself shows no edge here.

## Why the live runner cannot run a true rank (stated before scoring)

`LabStrategy` evaluates `mask(df)` on one symbol's frame. No context column carries a universe rank. A true top/bottom-k
setup would need a new lab context column (e.g. a percentile of fromOpen-in-ATR among the poll's peers), which is an
`mcf/strategies/lab_context.py` change outside this lane. The 5 delivered setups therefore use rank PROXIES the runner
already has: `breadth`, `breadth_open`, `spy_fo` (YAML `context: [...]`, listed in each module's CONTEXT).
Live/history difference: history context starts at the 09:50 bar; live has earlier bars, so XS5's 3-bar breadth change
at 10:00-10:05 can fire live where history had NaN (small).

## The 5 setups (delivered as modules; all gate_pass = false)

| setup | TRAIN avgR (n) | VALID avgR (n) | trades/session | vs random T/V | up / down / quiet R (TRAIN+VALID) | parity |
|---|---|---|---|---|---|---|
| XS1-laggard-greentape-short | -0.164 (2,700) | -0.145 (1,857) | 13.1 | +0.005 / +0.040 | -0.21 / -0.01 / -0.08 | 218/218 |
| XS2-leader-redtape-long | -0.167 (3,329) | -0.126 (1,580) | 14.1 | +0.028 / +0.022 | +0.12 / -0.22 / -0.05 | 4,427/4,427 |
| XS3-quiet-topoutlier-fade-short | -0.127 (3,818) | -0.089 (3,286) | 20.4 | -0.035 / -0.035 | -0.25 / +0.08 / -0.15 | 3,538/3,538 |
| XS4-quiet-bottomoutlier-fade-long | -0.119 (3,230) | -0.039 (2,536) | 16.6 | -0.038 / +0.040 | +0.12 / -0.28 / -0.11 | 4,094/4,094 |
| XS5-rankclimb-fallingtape-long | -0.114 (9,303) | -0.154 (3,323) | 36.3 | -0.032 / -0.061 | -0.02 / -0.22 / -0.12 | 742/742 |

Avg R without the best day is within 0.01-0.02R of the avg R for every primary (no one-day effect; all are uniformly
negative). Neighbours (plateau check) sit on the same negative plateau: best is XS4 ex=0.75 (-0.102 / -0.028R, 38.8
trades/session, above the cap). Parity = bar-by-bar mask match module vs harness on 2026-09, inside window and ADV 95M.

Gate per setup: XS1 fail (avg R); XS2 fail (avg R); XS3 fail (avg R); XS4 fail (avg R, TRAIN -0.119); XS5 fail (avg R
and trades/session 36 > 25). Trades/session, parity: XS1-XS4 within 1.5-25 and parity exact.

## Reading for the owner

If the exploratory accounts want this family anyway (the owner asked for exploration), the least bad are **XS4**
(VALID -0.039R, beats random on VALID, long side) and **XS2 / XS1** (the only primaries that beat random in both splits),
with the expectation from 2 years that they lose about 0.04-0.17R per trade after costs and the fail-fast rule
(5+ sessions, 45+ trades, avg R <= -0.30 or <= -15R) is the real test. They are listed, not recommended.

Rule-change context: none of these setups ran live; no ledger change applies to these backtest numbers (fixed
lab_trades cost model, R = 0.25 x ATR, no per-setup stop, no sizing). Live R would also carry the ledger's 10-27 GX1
clock and 10-30 Testing cost filter if placed in Testing-style accounts.

Educational only — not financial advice.
