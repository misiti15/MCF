# Hunch scale-up: 20 → 100 → 200 tickers

*Educational only — not financial advice. Replay (backtest) results; the live shadow scoreboard is on branch mcf-data-hunch and is never mixed in.*

Same code, features, learners and periods at every size; only the universe changes (20-set = SPY, QQQ, IWM + 19 most-traded live names = 22 tickers; 100 / 200 = the 20-set + the most liquid names by 20-day dollar ADV, lists in research/hunch/universe100.txt / universe200.txt). VALID = 2026-03-01..2026-10-07; locked block 2024-11-01..2025-02-28 never read. z = day-clustered z vs the best baseline; the bar grows with the number of tests at each size (per-ticker comparisons count).

## M1

| tickers | pooled:logreg | pooled:gbt | pooled:top8 | ticker:logreg (all Hunches) | best baseline | best z | bar | pooled:logreg on the 22 common tickers | tickers where own Hunch > its best baseline | best single ticker (own) | any 65% consistent | runtime | peak memory |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 22 | 50.98% | 51.56% | 51.17% | 51.47% | `base_rate` 51.37% | 1.54 | 3.14 | 50.98% | 10 / 22 (raw, no z) | MSTU 53.71% | no | 269 s | 1,219 MB |
| 100 | 50.87% | 51.14% | 51.04% | 51.12% | `base_rate` 50.72% | 3.39 | 3.47 | 51.05% | 63 / 100 (raw, no z) | MSTU 53.71% | no | 407 s | 4,328 MB |
| 200 | 51.23% | 51.44% | 51.28% | 51.36% | `base_rate` 50.93% | 4.34 | 3.66 | 51.04% | 120 / 200 (raw, no z) | RWM 57.39% | no | 470 s | 8,345 MB |

**M1 reading (replay of 2026-11-04):** next-bar direction is ~51% at every size. At 200 tickers the pooled GBT and the per-ticker Hunches clear the multiple-testing bar against the best baseline by about +0.4-0.5 pp — real but tiny, and nowhere near 65% (best 20-session VALID window ~52%).

## M3

| tickers | pooled:logreg | pooled:gbt | pooled:top8 | ticker:logreg (all Hunches) | best baseline | best z | bar | pooled:logreg on the 22 common tickers | tickers where own Hunch > its best baseline | best single ticker (own) | any 65% consistent | runtime | peak memory |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 22 | 66.78% | 67.66% | 66.82% | 66.80% | `base_rate` 51.01% | 163.39 | 3.14 | 66.78% | 22 / 22 (raw, no z) | MSTU 68.68% | YES | 271 s | 1,393 MB |
| 100 | 66.61% | 67.03% | 66.63% | 66.53% | `base_rate` 50.66% | 286.54 | 3.47 | 66.84% | 100 / 100 (raw, no z) | TMO 69.02% | YES | 422 s | 5,159 MB |
| 200 | 67.10% | 67.45% | 67.12% | 67.08% | `base_rate` 50.30% | 380.73 | 3.66 | 66.78% | 200 / 200 (raw, no z) | RWM 71.30% | YES | 485 s | 10,041 MB |

**M3 reading:** next-bar volume is predictable, but mostly by volume mean reversion: the single-indicator vol20 learner alone scores 65.43% on VALID (20-set); the combined Hunch adds ~2.2 pp. The ladder is not advanced automatically: the owner decides.

## Live cost estimate (one GitHub job polling 200 symbols every 3 min)

- One job a trading day, ~09:40-16:01 ET (~6.4 runner-hours; a hand-over to the queued hourly standby after ~5h40m because of the 6-hour job limit). Light: one Python process, < 1 GB RAM.
- Per tick (every 3 min, 121 a day): 3 Alpaca bars GETs (204 symbols in chunks of 100, incremental since the last tick), ~10 s to rebuild 200 tickers' features from 7 days of 1-min bars, < 1 s to walk the models. About 400 market-data requests a day — far under Alpaca's rate limit, and on the data key only (no orders).
- A push to mcf-data-hunch every ~15 minutes (~26 a day) plus the end-of-day model save. guesses/<day>.csv ≈ 24,000 rows (~2 MB) a day.

*Educational only — not financial advice.*
