# l3_1022: early Primary review of Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD)

*Educational only - not financial advice. "Live" = paper journals (run 1) through 2026-10-22. "Backtest" = the open
two-year lab history (2024-10..2026-10-07); the locked block 2024-11-01..2025-02-28 was never read and no holdout was
scored. Costs are always in (production cost, time-of-day entry cost, x3 on the extended tier). TRAIN = to 2025-12-31,
VALID = 2026-01-01..10-07. `PLAN.md` was written before any variant was scored and was not changed. No config, setup
or exit was changed. Configurations scored: **22** (study bar 2.49; L3 lineage N 12,302 -> bar 4.34).*

## Verdict
**Demote it to Testing 1 (reply "L3-1 demote").** It is losing money in Primary (23 paper trades, -0.31R each,
-$192.05 in its 2 Primary sessions), it loses on two years in both periods (-0.031R per trade; without its single
best day, 2025-04-07, -1,647R), and the +0.15R it showed live in Testing 1 came from one day (10-20: +33.6R; every
other live day together: 71 trades, -0.22R each). None of the 22 variants fixes it: 0 pass, and none is even a
near-miss. Back in Testing 1 it keeps collecting a record at no cost to Primary.

## Failures first
- **0 of 22 variants pass; 0 are near-misses.** Only one variant is positive after costs in both periods: X2, a stop
  twice as wide at the same $ risk (+0.003R train / +0.005R valid, n 11,706 / 8,756). It fails three other tests: it
  does not beat random same-minute shorts in train (+0.007R), one day (2025-04-07, +524R) is 7x its whole two-year
  total (+75R; -449R without that day), and its gain over the parent is t 1.70 (bars 2.49 / 4.34).
- **Gates on the market (SPY / QQQ above VWAP) wreck it**: V1 / V2 train -0.24R / -0.22R per trade and they keep only
  28-34% of trades. Shorting these names only when SPY is already below VWAP catches the rebound (same as regime1022).
- **The backtest is one day.** The parent's 2-year total is -767R; 2025-04-07 alone is +880R (the tariff crash bounce
  day), so the other 394 days lose -1,647R. Every "improvement" below keeps that dependence.
- **The replay store is not in this container** (`data/replay/` missing), so `python -m mcf.replay` was not re-run
  for 10-22. Part 2 uses the replay results already on file (research/replay/VALIDATION.md, results/gap.json,
  broad.json, sessions to 10-21).
- **Frames stop at 15:00.** The lab outcome holds lots to 15:55, so the scan rebuilt the 15:05-15:55 bars from the
  1-minute history cache (locked months filtered out inside the read). With them, the scan reproduces the lab outcome
  on every signal (parity 1,199 / 1,199 in 2026-09) and the parent as-run to the trade (25,123 vs 25,124; -0.0321 /
  -0.0285R; Bear / Bull / Choppy / Quiet +272 / -622 / -252 / -146R, identical to regime1022).
- **The lot-cap simulation models this setup alone**: no other setups' lots, slots, ETB / spread skips or halts.

## 1. Live record (paper), through 2026-10-22 (`live_out.md`, `live_trades.csv`, `live_summary.json`)
| scope | trades | sessions | win % vs break-even | avg R after costs | t | P/L adjusted | last 4 sessions |
|---|---|---|---|---|---|---|---|
| **Primary only** (10-21, 10-22) | 23 | 2 | 39.1% vs 55.4% | **-0.308** | -1.19 | **-$192.05** | -0.308R |
| Testing 1 (10-13..10-20) | 128 | 6 | 64.1% vs 51.1% | +0.197 | 1.04 | +$527.11 | +0.237R |
| **All accounts merged** | 151 | 8 | 60.3% vs 52.7% | **+0.120** | 0.62 | +$335.06 | +0.268R |
| all accounts **without 10-20** | 71 | 7 | - | **-0.217** | - | -$319.91 | - |

By day (regime per regime1022 rules; 10-22 = SPY -0.31% open-to-close, range 0.85% vs 20-day median 0.77% -> **Choppy**,
from a read-only SIP fetch):
| day | acct | regime | trades | R | P/L |
|---|---|---|---|---|---|
| 10-13 | T1 | Quiet | 15 | -0.5 | +$13.90 |
| 10-14 | T1 | Bear | 6 | +0.4 | +$2.51 |
| 10-15 | T1 | Bull | 12 | -13.5 | -$188.31 |
| 10-16 | T1 | Bear | 8 | +2.4 | +$10.44 |
| 10-19 | T1 | Quiet | 7 | +2.9 | +$33.60 |
| **10-20** | T1 | Choppy | 80 | **+33.6** | **+$654.97** |
| 10-21 | P | Choppy | 5 | -5.7 | -$176.93 |
| 10-22 | P | Choppy | 18 | -1.3 | -$15.12 |

- **By regime (all accounts):** Bear 14 trades +0.198R; Bull 12, -1.127R (all lost); Choppy 103, +0.258R (10-20
  alone is 80 of them); Quiet 22, +0.109R.
- **Stacking.** Primary: all 7 symbol-days were stacked (2-7 lots): FTNT x3 -3.2R and TKNO x2 -2.5R (10-21), JBS x3
  -4.0R, SNAP x7 (3 stopped, then 4 targets: +1.9R), FMC x3 +0.8R (10-22). Testing 1: 31 of 55 symbol-days stacked,
  +29.7R, nearly all on 10-20 (CLSK, CORZ, APLD, WULF, ALM ... one crypto-miner / AI-infrastructure fade). Lot 3+ was
  the best live lot (+0.349R, 51 trades) - again 10-20.
- **Time of day (all accounts):** 09:50-10:30 +0.118R (11), 10:30-11:30 +0.091R (68), 11:30-13:00 +0.172R (63),
  13:00-15:00 -0.014R (9). All Primary losses came from entries 10:40-12:06.

## 2. Why live (+0.15R in Testing 1) differs from the two-year backtest (-0.031R)
1. **It is one day, not a different setup.** 10-20 gave +33.6R on 80 trades (25 symbols, a sector fade that worked).
   Remove it and live is -0.22R per trade over 71 trades - worse than the backtest. A single day producing more than
   the whole record is exactly what the backtest looks like too (2025-04-07 = +880R of a -767R total).
2. **Regime mix does not explain it.** Re-weighting the backtest's per-regime avg R (Bear +0.078, Bull -0.051, Choppy
   -0.066, Quiet -0.027) to the live mix predicts **-0.042R** (Testing 1) / -0.046R (all accounts). The live weeks were
   not "its" weather: only 2 of 8 sessions were Bear.
3. **The live runner sees a different slice of signals.** The backtest takes ~64 trades per traded day; live took
   ~21 (Testing 1) and ~12 (Primary). VALIDATION.md: the 5-bar gate drops 30-41% of lab signals; caps, ETB, spread
   and the account halts block more. In the Testing 1 replay (10-07..10-21) this setup gave 998 signals at -0.51R
   each, of which the replayed runner took 105-106 at **-0.016R (costs) / +0.007R (paper fills)**; live paper took 128
   at +0.213R. So selection (mostly the account halt on bad days) turned a very bad signal pool into break-even, and
   the last +0.2R is live-vs-replay noise in a handful of sessions (fills, timing, 10-20).
4. **The longer replay is negative.** The broad replay with Primary's current config over 27 sessions
   (2026-09-01..10-21, costs in, same execution as live): **591 trades, -0.198R per trade, t -0.9, -117R** (up days
   -0.217, flat -0.062, down -0.304 on the replay's universe-median labels). The Primary replay of its first session
   reproduced the live loss (4 trades -1.02R vs live 5 trades -1.08R).
5. **Fills are not the story.** Paper vs cost-model fills differ by ~0.01-0.03R per trade (VALIDATION.md).

## 3. Variant grid (22 pre-declared; `variants.csv`, `variants_days.csv`; train / valid avg R after costs)
Parent P0: -0.032 / -0.028 (n 14,253 / 10,870), random same-minute shorts -0.054 / -0.069 (the stock pick is a bit
better than random, the trade still loses). Bear +0.078 vs non-Bear -0.048.

| id | variant | train avg R | valid avg R | kept % (tr / va) | random tr / va | Bear / non-Bear | gain t | fails |
|---|---|---|---|---|---|---|---|---|
| S1 | one lot per symbol | -0.051 | -0.035 | 49 / 43 | -0.052 / -0.068 | +0.047 / -0.061 | 0.36 | 1,3,4,5 |
| S2 | refire off | -0.108 | -0.044 | 17 / 22 | -0.118 / -0.060 | +0.112 / -0.106 | 0.39 | 1,3,4,5 |
| S3 | refire cooldown 3 | -0.027 | -0.021 | 72 / 80 | -0.044 / -0.070 | +0.085 / -0.041 | 0.89 | 1,3 |
| S4 | refire cooldown 6 | -0.027 | -0.019 | 52 / 62 | -0.034 / -0.058 | +0.090 / -0.040 | 0.81 | 1,3 |
| W1 | from 10:30 | -0.022 | -0.023 | 93 / 93 | -0.039 / -0.066 | +0.079 / -0.039 | 2.02 | 1,3 |
| W2 | from 11:00 | -0.006 | -0.033 | 87 / 86 | -0.020 / -0.067 | +0.060 / -0.030 | 1.39 | 1,3,4 |
| W3 | until 14:00 | -0.087 | -0.040 | 79 / 90 | -0.112 / -0.068 | +0.092 / -0.093 | -0.84 | 1,3,4,5 |
| X1 | stop 1.5x, same $ | +0.002 | -0.003 | 89 / 87 | -0.006 / -0.041 | +0.096 / -0.015 | 2.49 | 1,3 |
| **X2** | **stop 2x, same $** | **+0.003** | **+0.005** | 82 / 81 | **+0.007** / -0.024 | +0.093 / -0.011 | 1.70 | 2,3 (bar) |
| X3 | time stop 60 min | -0.056 | -0.031 | 114 / 128 | -0.062 / -0.059 | -0.000 / -0.051 | -1.57 | 1,3,4 |
| X4 | time stop 120 min | -0.043 | -0.030 | 101 / 104 | -0.052 / -0.062 | +0.042 / -0.050 | -0.88 | 1,3,4 |
| X5 | scale-out half at +0.5R | -0.083 | -0.031 | 110 / 112 | -0.084 / -0.068 | -0.006 / -0.069 | -1.50 | 1,3,4 |
| G1 | gap >= -10% | -0.023 | -0.023 | 92 / 90 | -0.052 / -0.063 | +0.111 / -0.044 | 2.23 | 1,3 |
| G2 | gap >= -6% | -0.026 | -0.018 | 74 / 75 | -0.056 / -0.069 | +0.134 / -0.046 | 1.61 | 1,3 |
| G3 | gap <= -4% | -0.024 | -0.027 | 57 / 54 | -0.027 / -0.060 | +0.054 / -0.039 | 0.67 | 1,3 |
| R1 | skip stock-SPY from open > 8 | -0.007 | -0.024 | 75 / 73 | -0.048 / -0.066 | +0.160 / -0.037 | 2.17 | 1,3 |
| R2 | only stock-SPY from open >= 4.5 | -0.099 | -0.017 | 62 / 73 | -0.096 / -0.067 | +0.041 / -0.083 | -0.24 | 1-5 |
| V1 | skip SPY above VWAP | -0.239 | -0.031 | 28 / 30 | -0.134 / -0.079 | +0.003 / -0.226 | -0.18 | 1-5 |
| V2 | skip SPY & QQQ above VWAP | -0.225 | -0.029 | 30 / 34 | -0.129 / -0.073 | +0.000 / -0.203 | -0.18 | 1-5 |
| C1 | one lot + from 10:30 | -0.043 | -0.028 | 45 / 39 | -0.031 / -0.057 | +0.049 / -0.052 | 0.59 | 1-5 |
| C2 | cooldown 3 + skip SPY > VWAP | -0.226 | -0.023 | 18 / 21 | -0.130 / -0.077 | -0.022 / -0.193 | 0.08 | 1-5 |

Tests (PLAN): 1 positive in both periods with >= 30 / 20 trades; 2 beats random in both; 3 no day > 25% of total R;
4 better than the parent in both periods and gain t >= bar; 5 keeps >= 50% and drops only losing trades. Kept % above
100 = shorter holds free the 3-lot cap, so more lots run. The "fails" column lists tests 1-5 by number; in
addition, **no variant reaches the gain-t bar** (closest X1 2.485 vs study bar 2.486; lineage bar 4.34).

- **What helps a little, on both periods:** a wider stop at the same $ risk (X1, X2), skipping the first 40 minutes
  (W1, the gates1021 finding again), dropping gaps worse than -10% (G1) and runaway recoveries (R1), and slower refire
  (S3, S4). Each keeps the Bear strength (+0.08..+0.16R) and trims the non-Bear loss, but none turns it positive except
  X2, and X2 only to break-even.
- **What does not:** one lot per symbol and refire off (they remove the re-entries, which are not worse than first
  entries), time stops and scale-out (they cut winners: the target needs time), and market-direction gates.
- **No module was written**: no variant passed.

## 4. Recommendation (pre-declared rule in PLAN.md)
No variant passes; the two-year as-run is negative in both periods; the live Primary record (-0.31R, -$192) and the
27-session replay (-0.20R) are below break-even. -> **Demote Gap-Down Recovery Fade (all day)
(L3-gap-slope-fromopen-FD) from Primary to Testing 1** (promotion = move: switch it off in Primary, back on in
Testing 1 with the same settings, regenerate `docs/live/assignments.json` in the same commit; after the close).
This replaces the 10-27 review (PROMO-1021). If you prefer to wait, "L3-1 keep" leaves it in Primary until 10-27 with
the same rule (back to Testing if still below break-even). X2 (2x stop, same $ risk) is the only rework worth a note,
and it is only break-even; I do not propose it.

## Files
`PLAN.md` (pre-declared), `scripts/` (live.py, fetch_idx.py, tail.py, scan.py, score.py, l3c.py), `live_out.md`,
`live_trades.csv`, `live_summary.json`, `variants.csv`, `variants_days.csv`, `counts.json`.
Reproduce: `python research/bdi/l3_1022/scripts/fetch_idx.py && python research/bdi/l3_1022/scripts/live.py &&
python research/bdi/l3_1022/scripts/tail.py && python research/bdi/l3_1022/scripts/scan.py 4 &&
python research/bdi/l3_1022/scripts/score.py`.
