Educational only — not financial advice

# BEG-05 Market intraday momentum, last 25 minutes (long and short): results

*Research only. No setup, exit, config, account or ledger change.*
- Configurations tried: **4** (the base plus 3 pre-registered one-part tweaks). The random control fits nothing.
- The locked block 2024-11-01..2025-02-28 was never read. CHECK was scored once for the base and once for the FIT pick.
- R is after LR8 costs, plus 1.2 bp borrow on shorts. Trades are booked under the testing-arena rules (cap 100, <= 3
  lots per symbol, price >= $5, ETB >= 90%, the 0.15R stop-cost filter), as bench10's "normal way".
- Rule-change context: the backtest uses one fixed rule set for the whole window, so no live rule change in
  `research/ledger.jsonl` is mixed into these figures.

**Verdict**
- **Base: FAIL, and REALLY BAD (on both legs).** T1 combined avg R is −0.199, with a day-clustered t of −3.79. FIT,
  CHECK and T2 are all below −0.03.
- **Tweak `longonly` (FIT pick): FAIL, and REALLY BAD (second leg).** T1 combined is −0.101 (t −1.56). FIT, CHECK and
  T2 are all below −0.03: −0.055 / −0.127 / −0.218.
- Neither version should go to a testing arena. With costs in, the published effect (Gao, Han, Li & Zhou 2018) does
  not survive in 2023-2026 on SPY/QQQ/IWM/DIA. Even before costs, the direction is worth about 0R.

## Scores (booked trades, testing-arena rules)
| | trades | avg R | gross | w/o best day | total R/session | t (day) | stop rate |
|---|---|---|---|---|---|---|---|
| base FIT (170 s) | 137 | −0.308 | −0.204 | −0.346 | −0.248 | −3.18 | 28% |
| base CHECK (276 s) | 226 | −0.134 | −0.012 | −0.153 | −0.109 | −2.27 | 10% |
| base T1 combined (446 s) | 363 | **−0.199** | −0.085 | −0.213 | −0.162 | −3.79 | |
| base T2 2023-24 (427 s, ref) | 237 | −0.167 | −0.048 | −0.184 | −0.093 | −2.78 | 18% |
| longonly FIT | 73 | −0.055 | +0.025 | −0.119 | −0.024 | −0.45 | 11% |
| longonly CHECK | 129 | −0.127 | −0.026 | −0.160 | −0.059 | −1.72 | 9% |
| longonly T1 combined | 202 | **−0.101** | −0.008 | −0.124 | −0.046 | −1.56 | |
| longonly T2 (ref) | 154 | −0.218 | −0.114 | −0.235 | −0.078 | −3.39 | 16% |
| stop2x FIT (not picked) | 265 | −0.107 | −0.037 | −0.116 | −0.167 | −2.58 | 7% |
| agree FIT (not picked) | 115 | −0.272 | −0.173 | −0.318 | −0.184 | −2.56 | 25% |

- Best-day share is not defined: the total R is negative in every test. The worst best day was 2025-04-09 (the tariff-
  pause rally). Removing it makes every figure worse, so no record here rests on one big day.
- **Cost filter.** 0.15 x ATR is a $0.6-$1.5 stop on a $200-$600 ETF, so the 0.15R stop-cost filter removes about
  half of the raw signals: 128 of 265 on FIT, 176 of 402 on CHECK, 367 of 604 on T2. Costs that survive average about
  0.10-0.12R per trade.
- **Without the filter it is still negative.** The raw average with no cost filter is −0.21 on FIT, −0.14 on CHECK and
  −0.21 on T2.

## Random-entry control (same symbol-days, entry, stop and exit; side from a fair coin; 200 seeds)
| | setup avg R | random mean | random 5-95% | setup percentile |
|---|---|---|---|---|
| base FIT | −0.308 | −0.173 | −0.251..−0.078 | 1 |
| base CHECK | −0.134 | −0.161 | −0.231..−0.090 | 72 |
| base T2 | −0.167 | −0.145 | −0.215..−0.065 | 31 |
| longonly FIT | −0.055 | −0.081 | −0.213..+0.050 | 63 |
| longonly CHECK | −0.127 | −0.137 | −0.234..−0.047 | 57 |
| longonly T2 | −0.218 | −0.131 | −0.207..−0.051 | 4 |

- Neither the base's direction nor the tweak's beats a coin flip consistently.
- Most of the loss is structural: costs plus a stop that is tight compared with last-half-hour noise. Random sides
  lose −0.13 to −0.17R as well.

## Comparison with the top-10 benchmark (research/ultimate_1119/top10/PLAN.md Tier A, home-account medians)
The benchmark medians are themselves negative. Meeting them means "no worse than the live winners in this engine". It
does not mean profitable.
| test / rule | threshold | base | longonly |
|---|---|---|---|
| T1 combined avg R | >= −0.0383 | −0.199 FAIL | −0.101 FAIL |
| T1 check avg R | >= −0.0464 | −0.134 FAIL | −0.127 FAIL |
| T1 combined w/o best day | >= −0.0674 | −0.213 FAIL | −0.124 FAIL |
| T1 check w/o best day | >= −0.0781 | −0.153 FAIL | −0.160 FAIL |
| T1 combined total R/session | >= −0.4862 | −0.162 pass | −0.046 pass |
| T1 check total R/session | >= −0.5218 | −0.109 pass | −0.059 pass |
| T2 avg R | >= −0.1048 | −0.167 FAIL | −0.218 FAIL |
| >= 20 trades check / T2 | | 226 / 237 | 129 / 154 |
| **Tier** | | **FAIL** (misses by up to 0.16R) | **FAIL** (misses by up to 0.11R) |
| REALLY BAD | | yes (t −3.79; all three < −0.03) | yes (all three < −0.03) |

Total R/session passes only because the setup trades rarely: at most 4 trades a day, against ~0.8 booked.

## FIT diagnosis of the worst losers (diag.py)
- **Stop.** 38 stop-outs carry −42.7R of the −42.1R FIT total. Time exits net +0.5R.
  - The 0.15 x ATR stop is inside normal last-half-hour noise: the median adverse excursion is 0.077 ATR, and 25% of
    signals go 0.147 ATR against.
  - The stopped trades were mostly wrong anyway: held to 15:55 they lose −0.69R gross, and only 15% would have finished
    on the right side.
- **Signal (entry direction).** Held to 15:55 without a stop, the raw signals earn +0.004R gross (+0.0006 ATR). That
  is no directional edge at all.
- **Side.** Shorts made −0.595 (64 trades) against −0.055 for longs (73). The short losers are the 2025-03..05 sell-off
  days, squeezed into the close.
- **Regime.** FIT gross by month: 2025-03..05 is −0.20..−0.29, and 2025-06..09 is +0.05..+0.26. This is a regime
  effect, not a stable property.
- Mid-day disagreement (10:00 -> 15:29 move against the side) loses most (−0.259 vs −0.027 gross). As a filter, though,
  it did not help after booking (`agree` −0.272).

## Tweaks (pre-registered in PLAN.md after the diagnosis, before scoring; one part each)
1. `stop2x`, stop 0.30 x ATR: FIT −0.107. Every signal passes the cost filter and stop-outs fall to 7%, but the
   direction still has no edge.
2. `agree`, mid-day move must agree with the side: FIT −0.272.
3. `longonly`, drop shorts: FIT −0.055. **This was the pick.** It held up poorly on CHECK (−0.127) and on T2 (−0.218,
   4th percentile of random). The FIT gain came from avoiding the 2025 spring short squeezes, not from a lasting edge.

## Next step (optimistic, honest)
- The idea is not dead. The paper's effect is strongest on high-volatility, high-volume days, and r1 over 1% showed
  +0.13R gross held without a stop on FIT (69 signals).
- A follow-up would go through the backlog. It would test a volatility-day gate with a wider stop (two parts, so a new
  pre-registered config), or trade the same signal through a lower-cost vehicle.
- As specified, this beginner rule does not earn its costs.

## Files
- `beg05.py`: the module. It uses the live `Strategy.generate(ctx)` interface, plus the pure functions `find_signal`
  and `walk` that the backtest uses.
- `smoke_test.py`: tests the module (passes). It runs a synthetic up day and its mirror through the module and through
  `mcf.backtest.engine.simulate`.
- `run.py`: the engine (`score VARIANT fit|check|t2`, `rand VARIANT PART`).
- `summarize.py`: T1 combined.
- `diag.py`: the FIT-only diagnosis.
- `PLAN.md`: the pre-registration.
- `variants.json`: the tweaks.
- `results.json`: every figure above.
- Trade lists (600 KB) are in the session scratchpad `beg05w/`, not in the repo.

## Implementation notes (plainest readings)
- "Price at 10:00" = the 09:59 bar close.
- VWAP = typical-price session VWAP through the 15:29 bar.
- Entry = market at the 15:30 bar open.
- Stop = fill −/+ 0.15 x ATR(14) daily, as of the prior close. The live Signal uses the 15:29 close as the reference,
  because the fill is unknown at decision time.
- Time exit at the 15:55 bar open, the engine's flat time.
- One trade per symbol per day. Half-day sessions have no 15:29 bar, so they have no trade.
- T1 prev close and ATR come from the lab frames (point in time). T2 computes them from cache_fresh RTH bars.
