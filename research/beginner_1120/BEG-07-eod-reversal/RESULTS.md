Educational only — not financial advice

# BEG-07 End-of-day reversal of intraday extremes: results (2026-11-20)

Research only. No setup, exit, config, account or ledger change. **Configurations tried: 4** (base + 3 pre-registered
tweaks). All are reported below. Costs are included (LR8 + 1.2 bp borrow on shorts). The locked block
2024-11-01..2025-02-28 was never read. CHECK was scored once for the base and once for the tweak picked on FIT.
Files in this folder: `beg07.py` (module), `smoke_test.py`, `run.py` (normal-way backtest), `diag.py` (FIT diagnosis),
`combine.py`, `rnd.py`, `PLAN.md` (written before scoring; the tweaks were added before they were scored),
`variants.json`, `results.json`. Trade books are in the scratchpad (`beg07w/`, ~115 MB) and can be rebuilt.

## Verdict
| | T1 combined avg R | T1 check avg R | w/o best day (comb / check) | R/session (comb / check) | T2 avg R | tier |
|---|---|---|---|---|---|---|
| standard (top-10 median, Tier A threshold) | >= −0.0383 | >= −0.0464 | >= −0.0674 / −0.0781 | >= −0.4862 / −0.5218 | >= −0.1048 | |
| **base** | **−0.0542** ✗ | −0.0369 ✓ | −0.0560 ✓ / −0.0394 ✓ | **−0.796** ✗ / **−0.579** ✗ | −0.0337 ✓ | **FAIL** (REALLY BAD, both legs) |
| **atr4** (tweak: daily ATR >= 4% of price) | −0.0367 ✓ | −0.0351 ✓ | −0.0383 ✓ / −0.0373 ✓ | **−0.517** ✗ / **−0.550** ✗ | −0.0476 ✓ | **NEAR** (REALLY BAD, leg 2) |

- **base: FAIL.** T1 combined avg R misses the bar by 0.016R, and R/session is far below it, because the setup takes
  about 15 trades a session that lose. The pre-registered REALLY BAD rule flags it on both legs: (1) T1 combined −0.054
  with day-clustered t −4.48; (2) below −0.03 on fit (−0.088), check (−0.037) and T2 (−0.034).
- **atr4: NEAR.** It passes every avg-R and w/o-best-day leg and T2. It misses only the R/session leg: −0.517 against
  −0.486, and −0.550 against −0.522. Per trade that is about 0.002R (14-16 trades a session), well inside 0.02R.
  - The task defines NEAR as "within 0.02R", and I applied that definition. PLAN.md had worded NEAR more narrowly
    ("every failed avg-R threshold within 0.02R, other legs hold"). Under that wording atr4 would be FAIL. Both
    readings are stated here.
  - It is still flagged **REALLY BAD on leg 2**: fit −0.040, check −0.035 and T2 −0.048 are all below −0.03. Under
    top10/PLAN.md it would not be admitted. Note that the same rule also flags 4 of the current live top 10.
- **Not profitable in any test, after costs.** "Meets the standard" would only mean "no worse than the live leaders'
  backtests", and every one of those medians is negative.

## Implementation (as written; plainest readings)
- **Universe:** the lab symbols in data/cache_hist (T1: 1,023 stocks after removing ETFs) or data/cache_fresh (T2: 361
  stocks). ETFs are removed using assets_meta is_etf plus the study's extra ETFs. Price at the 15:24 close >= $10.
  ADV20 (as of the prior close) >= $30M.
- **Signal:** one universe pass on the 15:24 close, r = close / prev_close − 1.
  - Long: the 10 lowest r with r <= −3% and close > day low + 0.1 ATR.
  - Short: the 10 highest r with r >= +3% and close < day high − 0.1 ATR, easy to borrow only.
  - The pin and ETB filters are applied *before* the top-10 cut. Day high/low is taken over RTH 09:30..15:24.
- **Entry, stop, exit:** entry at the 15:25 bar open, the next-bar-open convention from DESIGN.md. Stop 0.20 × daily
  ATR(14) from the fill. Time exit at the 15:55 open. Stop first; a gap-through fills at the worse of open and stop.
- **Data:** prev_close comes from the frames' gap (T1) or the prior RTH close (T2). ATR comes from the frames' atr_d (T1)
  or ATR(14) on daily bars built from 1-minute bars (T2).
- **Live interface:** `BEG07.universe_pass(date, snapshot)` must be called by the runner at 15:24. `generate(ctx)` then
  emits the picked symbol. DayContext is per symbol, so the ranking cannot run inside it. The smoke test passes,
  including `mcf.backtest.engine.simulate`.
- **Book:** bench10 TESTING_RULES. Cap 100, 3 lots/symbol, price >= $5, ETB >= 0.9, and a 0.15R stop-cost filter. The
  filter removes 31% of raw signals on FIT, 20% on CHECK and 37% on T2, mostly low-ATR, high-priced names.

## Base results (testing-rules book, R after costs)
| test | sessions | trades | /session | win | avg R | gross avg R | w/o best day | R/session | worst day | day-t | stop rate | long / short avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FIT | 170 | 2,223 | 13.1 | 0.433 | −0.0879 | −0.0246 | −0.0935 | −1.150 | −9.5 | −4.65 | 23% | −0.101 / −0.074 |
| CHECK (once) | 276 | 4,326 | 15.7 | 0.457 | −0.0369 | +0.0163 | −0.0394 | −0.579 | −13.0 | −2.39 | 21% | −0.040 / −0.034 |
| T1 combined | 446 | 6,549 | 14.7 | | −0.0542 | | −0.0560 | −0.796 | | −4.48 | | |
| T2 2023-24 (ref) | 427 | 3,698 | 8.7 | 0.465 | −0.0337 | +0.0351 | −0.0373 | −0.292 | −11.5 | −2.23 | 16% | −0.043 / −0.025 |

- Total R is negative in every test, so the best-day share is n/a. No single day drives the result: w/o-best-day sits
  within 0.006R of the average.
- By SPY day type (up / flat / down):
  - FIT: −0.097 / −0.148 / −0.005
  - CHECK: −0.050 / −0.031 / −0.031
  - T2: −0.059 / −0.007 / −0.040
- **The paper's effect shows up gross on CHECK (+0.016R) and T2 (+0.035R), but not on FIT (−0.025R).** Costs run about
  0.05-0.07R per trade, which is larger than the gross edge in every test. The cost check flagged in the spec decides
  the result.

## Diagnosis of the worst losers (FIT only) → 3 tweaks, pre-registered before scoring
- **Stop:** the worst 10% of trades are all stop-outs (average −1.13R, median 18 minutes after entry). 23% of trades
  stop out, and time exits average +0.22R. A 0.20 ATR stop is inside normal last-half-hour noise.
- **Filter:** extreme movers (|r| > 10%) are the worst bucket on both sides (−0.18R long, −0.10R short, about 35%
  stopped). These are news-day moves that keep going rather than revert.
- **Filter:** names with daily ATR below 4% of price are the worst ATR buckets (−0.15..−0.17R, 32-41% stopped). For
  them 0.20 ATR is only a few ticks.

| tweak (one part) | FIT trades | FIT avg R | gross | w/o best day | R/session | day-t | stop rate | long / short |
|---|---|---|---|---|---|---|---|---|
| base | 2,223 | −0.0879 | −0.025 | −0.0935 | −1.150 | −4.65 | 23% | −0.101 / −0.074 |
| stop30: stop 0.30 ATR | 2,750 | −0.0598 | −0.012 | −0.0639 | −0.968 | −4.67 | 10% | −0.069 / −0.050 |
| rcap10: skip abs(r) > 10% | 2,163 | −0.0716 | −0.009 | −0.0760 | −0.911 | −3.90 | 20% | −0.085 / −0.057 |
| **atr4: daily ATR >= 4% (pick)** | 1,966 | **−0.0401** | +0.014 | −0.0454 | −0.464 | −2.32 | 16% | −0.058 / −0.023 |

atr4 was picked on FIT (best avg R and best w/o-best-day) and scored once on CHECK.

| atr4 | sessions | trades | /session | win | avg R | gross | w/o best day | R/session | worst day | day-t | long / short avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FIT | 170 | 1,966 | 11.6 | | −0.0401 | +0.014 | −0.0454 | −0.464 | | −2.32 | −0.058 / −0.023 |
| CHECK (once) | 276 | 4,318 | 15.6 | 0.468 | −0.0351 | +0.011 | −0.0373 | −0.550 | −10.3 | −2.67 | −0.023 / −0.048 |
| T1 combined | 446 | 6,284 | 14.1 | | −0.0367 | | −0.0383 | −0.517 | | −3.48 | |
| T2 (ref) | 427 | 2,511 | 5.9 | 0.462 | −0.0476 | +0.009 | −0.0511 | −0.280 | −8.7 | −2.99 | −0.079 / −0.020 |

**Effect on each side (remedy rule):**

| test | long avg R (base → atr4) | short avg R (base → atr4) |
|---|---|---|
| FIT | −0.101 → −0.058, better | −0.074 → −0.023, better |
| CHECK | −0.040 → −0.023, better | −0.034 → −0.048, worse by 0.014 |
| T2 | −0.043 → −0.079, worse by 0.036 | −0.025 → −0.020, better |

**The improvement does not carry out of sample:** CHECK gains only +0.002R overall, and T2 falls by 0.014R.

## Random-entry controls (50 draws each; percentile = share of draws worse than the setup)
| test | setup avg R | random side, same picks: mean (p05..p95), pctile | random eligible names, same count: mean, pctile |
|---|---|---|---|
| base FIT | −0.0879 | −0.0731 (−0.095..−0.048), 24 | −0.0707, 8 |
| base CHECK | −0.0369 | −0.0493 (−0.069..−0.028), 84 | −0.0589, 98 |
| base T2 | −0.0337 | −0.0645 (−0.083..−0.049), 100 | −0.0614, 100 |
| atr4 FIT | −0.0401 | −0.0612 (−0.086..−0.033), 86 | −0.0698, 98 |
| atr4 CHECK | −0.0351 | −0.0467 (−0.063..−0.030), 88 | −0.0605, 100 |
| atr4 T2 | −0.0476 | −0.0583 (−0.079..−0.040), 78 | −0.0484, 54 |

- The reversal direction beats a coin flip on CHECK and T2 for the base. On FIT it does not.
- About 0.01-0.03R of the edge over random is real, but it sits under a cost floor of about 0.05-0.06R. Random entries
  lose roughly that much on their own.
- The random-names pool is the candidate table: |r| >= 2% at some minute. It is slightly more volatile than the whole
  universe.

## Reading it (optimistic, honest)
- **What works:** the sign of the effect. Big intraday movers do tend to give back a little in the last half hour (gross
  +0.016R on CHECK and +0.035R on T2, above random). That is the published finding.
- **What fails:** the edge per trade is smaller than the cost of one round trip with a 0.20 ATR stop. A tight stop
  turns noise into −1R losses.
- **What could be salvaged (next step, not tested here):** cut the cost per R rather than add filters. Two options:
  - enter on a limit or at the 15:50 closing-auction proxy;
  - use a wider stop on high-ATR names only.

  The stop30 and atr4 FIT results both point that way: fewer stop-outs and a smaller cost share. A backlog entry would
  go through research/backlog.jsonl. Nothing here is a candidate for a testing arena.
- **Rule-change context:** none. Backtests apply today's book (TESTING_RULES) to every session, so no ledger change
  (sizing, latch, cost filter, ETB) falls inside the windows.
- **Known biases:**
  - the lab universe is about 1,000 stocks against about 4,000 live (survivorship), and T2 has 361 stocks;
  - ETB uses today's flags;
  - no earnings blackout;
  - no spread model beyond LR8;
  - prev_close is the RTH close (T2) or the frames' gap (T1), not the official closing auction.

Educational only — not financial advice.
