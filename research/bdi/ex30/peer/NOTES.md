Educational only — not financial advice

# ex30 / peer — peers, sympathy, dispersion: results (2026-11-03)

Pre-declared in PLAN.md (committed 441e43fa6 before any scoring). **15 configurations scored** (5 primaries, 10
neighbours); nothing else was scored. **0 of 15 pass the light lane gate; 0 of 5 delivered setups pass.** Closest:
PR5 passes the avg-R part (TRAIN -0.006, VALID -0.017) but trades 76/session (cap 25). Locked block
2024-11-01..2025-02-28 never loaded. Costs in (gates.lab_trades production + time-of-day entry). TRAIN = 234 sessions
(2024-10, 2025-03..12), VALID = 114 sessions (2026-01..03, 2026-07-01..09-15). Backtest only — no live or paper result
exists for any of these. Files: `score.py` (harness), `report.py`, `gen_modules.py` (writes the modules),
`results.csv` (every config), `parity.csv`, `modules/` (the 5 setups).

## Constraint stated before scoring

A lab module's `mask(df)` sees one symbol's frame plus `lab_context` columns. There is no per-symbol peer group, sector
ETF or pair leg among them (spy_fo, qqq_fo, breadth, breadth_open, qqq_vwap, spy_prng), and `qqq_vwap` is not in the
history2y context tables. So MH4's true residual-correlation peer groups and sector-ETF lead-lag **cannot run live
without a new context column (an `mcf/` change, not this lane)**. The 5 setups use SPY / QQQ as each name's moving peer,
with the name's own sympathy measured intraday from the frame (expanding correlation and beta of its 5-minute returns
vs SPY's / QQQ's, from bars >= 09:55), and `breadth_open` as the index's component set.

## Failures first

1. **Four of five primaries lose after costs on both splits** (PR1, PR2, PR4; PR3 on TRAIN). PR1 is -0.04 / -0.05R,
   PR2 -0.12 / -0.09R, PR4 -0.10 / -0.08R.
2. **The laggard catch-up (PR1) is a day-direction bet again.** It is +0.12R on SPY up days (TRAIN) but -0.76R on down
   days and -0.46R on quiet days; it does not beat the random entry (excess -0.01 / -0.08R). The MH4 cross-sectional
   edge does not survive when the "peer group" is just SPY — the name's own residual vs the index is mostly noise.
3. **The quiet-day designs do not make money on quiet days.** PR2 (decoupled breakdown, quiet tape) is -0.13 / -0.07R on
   quiet days; PR4 (QQQ residual pair-spread revert) -0.12 / -0.19R. Both are below random (small, t >= -0.9).
4. **PR3 (narrow-rally laggard short) is not a usable record.** It fires on only 5 sessions in TRAIN and 5 in VALID
   (34-282 trades on each of those days, all at once). TRAIN -0.19R; VALID +0.14R is carried by one day (2026-08-28,
   +114R of +137R, best-day share 0.83; without the best two days -0.03R). Its "VALID beats random t 4.1" is that one
   day. Called out per the one-big-day rule.
5. **PR5 fires far too often** (67 / 96 trades per session; cap 25): QQQ 10-minute impulses with lagging high-beta
   followers happen many times a day. Its R is about flat after costs (-0.006 / -0.017R) and it beats the random
   entry in both splits (+0.050R t 2.09 TRAIN, +0.029R t 1.04 VALID), but it is still a tape bet (+0.14 / +0.07R up,
   -0.14 / -0.13R down, ~0 quiet). The q = 0.30 neighbour is 26.4 trades/session, +0.012 / -0.027R (fails both parts).

## The 5 setups (delivered as modules; all gate_pass = false)

| setup | TRAIN avgR (n, t) | VALID avgR (n, t) | trades/session | vs random T / V | up / down / quiet R TRAIN | up / down / quiet R VALID | w/o best day T / V | parity |
|---|---|---|---|---|---|---|---|---|
| PR1-sympathy-laggard-long | -0.039 (5,643, -0.78) | -0.052 (3,791, -0.84) | 27.1 | -0.011 / -0.075 | +0.12 / -0.76 / -0.46 | +0.07 / -0.70 / -0.24 | -0.060 / -0.074 | 2,855/2,855 |
| PR2-decoupled-quiet-breakdown-short | -0.123 (1,590, -3.43) | -0.094 (1,007, -2.04) | 7.5 | -0.033 / -0.033 | -0.21 / +0.05 / -0.13 | -0.27 / -0.01 / -0.07 | -0.135 / -0.114 | 1,065/1,065 |
| PR3-narrow-rally-laggard-short | -0.192 (472, -2.06) | +0.142 (966, +1.14) | 4.1 (5 + 5 days) | +0.019 / +0.292 | -0.19 / n.a. / n.a. | -0.08 / +0.47 / +0.21 | -0.278 / +0.032 (VALID best day 83%) | 3,635/3,635 |
| PR4-qqq-residual-stretch-revert-short | -0.098 (1,439, -3.18) | -0.080 (817, -1.86) | 6.5 | -0.009 / -0.001 | -0.23 / +0.02 / -0.12 | -0.04 / -0.03 / -0.19 | -0.106 / -0.090 | 455/455 |
| PR5-qqq-impulse-leadlag-long | -0.006 (15,680, -0.19) | -0.017 (10,932, -0.53) | 76.5 | +0.050 / +0.029 | +0.14 / -0.14 / -0.00 | +0.07 / -0.13 / -0.01 | -0.018 / -0.027 | 673/673 |

Parity = bar-by-bar mask match module vs harness on 2026-09 inside window and ADV 95M (independent implementations:
numpy segment cumsums in score.py, pandas groupby in the modules). A live-shape check also passed: on 400 random
symbol-days the modules give the same mask on a single-symbol frame without symbol/date columns and with three
extra pre-09:50 bars (as the live frame has) — 2,000 checks, 0 mismatches.

Neighbours (plateau check, results.csv): PR1 res -0.35 / corr 0.35 sit on the same plateau (-0.02..-0.06R, 39-44
trades/session); PR2 -0.08..-0.14R; PR3 bo 0.40 is 0.6 + 4.6 trades/session, -0.44 / +0.30R (same one-day VALID);
PR3 spy 0.20 -0.11 / +0.04R; PR4 -0.05..-0.13R; PR5 q 0.15 -0.03 / -0.03R at 124/session.

Gate per setup: PR1 fail (avg R; 27.1 trades/session > 25); PR2 fail (avg R); PR3 fail (TRAIN avg R; VALID carried
by one day); PR4 fail (avg R); PR5 fail (trades/session 76.5 > 25; avg R part passes).

## Reading for the owner

- If one of these goes to an exploratory account anyway, **PR5** is the only one whose 2-year record is near flat
  after costs and above the random entry in both splits. It needs a throttle before it can run at a sane count: a
  higher ADV floor, a later start or a first-N-per-session cap. Any of those is a new configuration and would be
  scored first (not done here). **PR1** is the next (-0.04 / -0.05R) but only on up days.
- PR2 / PR4 are the quiet-day attempts and they fail on quiet days. PR3 is a 5-days-a-year day bet.
- The family's real idea — MH4 named peer groups — needs a per-symbol peer context column (e.g. the median residual
  move of each name's 10 correlation peers at the bar) added to `mcf/strategies/lab_context.py` with a peer table
  refreshed monthly. That is a lead / owner decision; until then it cannot be live-tested.

Rule-change context: none of these setups ran live; no ledger change applies to these backtest numbers (fixed
lab_trades cost model, R = 0.25 x ATR, no per-setup stop, no sizing). Live R in a Testing-style account would also carry
the ledger's 10-27 GX1 lab clock and the 10-30 Testing cost filter.

Educational only — not financial advice.
