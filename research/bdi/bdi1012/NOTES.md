# BDI 2026-10-12: index confirmation for longs and a same-side crowding cap

*Educational only - not financial advice. These are backtests on the open two-year history (426 sessions, 2024-10..2026-10-07). The rule-19 locked block (2024-11-01..2025-02-28) was never loaded. Nothing here is a paper or live result.*

**Verdict: both ideas FAILED.**
- 803 configurations were scored, as pre-declared in `PLAN.md`, which was committed in 55091e1 before any result existed.
- 0 pass the primary gate and 0 pass the Testing near-miss gate.
- No configuration with n >= 150 has a positive open-history expectancy.
- **Nothing goes to the lead for a locked-block score, and nothing goes to Testing.**

Inputs:
- Trade lists: CWT package B (`research/bdi/cwt/test_b/data/trades.npz`). Costs are already in: `gates.prod_r` with the time-of-day entry multiplier, x3 slippage on the extended tier, and R = 0.25 x daily ATR.
- Index state at the entry bar: SPY and QQQ rows of the lab frames.
- Splits: train runs to 2025-12-31 and valid runs 2026-01-02..2026-10-07 (the indexlink convention).

## Failures first

### Study A: index confirmation (lineage `bdi1012-ixconf`, 800 configurations)
**Grid.** 160 long lists (B2 CWT13 all-universe 16, B3 CWT14 48, B4 CWT12 32, B5 CWT05 64) x 5 filters:
- X1: SPY from open > 0
- X2: SPY above VWAP
- X3: QQQ from open > 0
- X4: QQQ above VWAP
- X5: SPY and QQQ both >= 0.10 ATR off their session low

**Results.**
- **Primary gate: 0 / 800 pass. Near-miss gate: 0 / 800 pass.**
  - Positive open-history expectancy: 62 configurations, all with n <= 60 (B5 ret5 cells with n of 2-60).
  - Positive in both train and valid with n >= 30: 0.
  - Regime gate passed: 0. WF >= 0.6: 7.
  - None reaches its bar: t >= 4.00 for B2/B4, 4.55 for B5 and 4.84 for B3. Lineage N = the test_b lineage + regime1009 1,052 + ix-gate 912 + 800.
- **The filter barely moves CWT14 longs.** Across the 240 B3 configurations, the mean change versus the unfiltered list is:

  | filter | change, open history | train | valid |
  |---|---|---|---|
  | X1 | +0.011R | +0.019R | +0.002R |
  | X3 | +0.016R | +0.016R | +0.015R |
  | X5 | +0.010R | +0.018R | +0.001R |

  The lists stay at about -0.08R (t -5 to -10). Trades the filter dropped run about -0.08 to -0.12R, and trades it kept about -0.07 to -0.10R.
- **Why it fails.** The unfiltered CWT14 longs are mildly positive in up sessions (+0.02..+0.05R) and lose heavily in down sessions (about -0.20R).
  - Requiring the index to be green at the entry bar does not pick the up sessions. X1-X4 cut up-session expectancy to about 0 (-0.03..+0.03R) and make down-session trades worse (-0.20..-0.28R). These are the trades bought on an intraday index bounce in a down day.
  - This is the same result as regime1009 G3 and ix-gate F1-F3: index state at entry does not tell you the session's direction.
- **The SPY-hedged expectancy stays at -0.12..-0.13R for every filter.** There is no stock-specific edge left.
- **The primary and Testing-1 long setups were not re-scored.** ix-gate (research/bdi/indexlink, 2026-10-11) already scored F1 spy_vwap, F2 qqq_vwap and F3 spy_fo on NS1, NS5 and heat_fade_long (current and -FD), and 0 of 912 passed. For example, NS5 + F3 gave n 389 at -0.004R. Running them again would only add tries.

### Study B: same-side crowding cap (lineage `bdi1012-crowd`, 3 configurations)
**Setup.**
- The book is the 17 Testing-2 long sources in package B, merged with one position per symbol.
- K = the cap on concurrent open longs.
- "Random-skip control" removes the same number of trades per session at random (mean of 20 draws).

| cap K | n | exp train | exp valid | exp all (t) | total R | worst 5% session R | worst session R | random-skip control exp (tr / va / all) |
|---|---|---|---|---|---|---|---|---|
| none | 246,611 | -0.0884 | -0.0855 | -0.0870 (-11.65) | -21,457 | -231.8 | -469.2 | - |
| 10 | 28,172 | -0.0976 | -0.0883 | -0.0934 (-13.22) | -2,632 | -22.2 | -54.2 | -0.0717 / -0.0765 / -0.0739 |
| 20 | 54,468 | -0.0953 | -0.0874 | -0.0917 (-13.85) | -4,996 | -41.3 | -90.2 | -0.0746 / -0.0749 / -0.0748 |
| 40 | 100,066 | -0.0897 | -0.0878 | -0.0897 (-13.89) | -8,980 | -80.7 | -183.4 | -0.0793 / -0.0784 / -0.0789 |

- **FAILED.**
  - Per trade, the cap is *worse* than uncapped in train and in valid at every K.
  - It is also worse than the random-skip control by about 0.015-0.02R.
  - The smaller tail comes only from trading 60-89% less.
  - A cap cannot turn a book that loses on every trade into a positive one. It should be revisited only on a book that is positive to begin with.
- **What it does show (descriptive, not tested):**
  - The random-skip control beats the uncapped book (-0.074 vs -0.087R) because it removes more trades from crowded sessions, and crowded sessions are the bad ones.
  - Within a session, the first K signals (which a cap keeps) are worse than a random K.
  - So the crowding is a *symptom* of a down day (many failed-breakdown longs firing at once), not a cause that a cap can remove. This is new backlog idea 1 below.

## Finalists (every finalist reported; none passes)
The two best configurations by open-history t per family (n >= 150) are in the first table. The 8 live CWT14 Testing-2 longs follow, with their unfiltered list and the best filter X3. Full rows for all 800 + 160 base lists are in `results_a.csv`.

| config | filter | train n / exp / t | valid n / exp / t | open history n / exp / t | up / down | WF | hedged | gate |
|---|---|---|---|---|---|---|---|---|
| B5-m0.75-v5-Dnone-t05s1-full | X1 | 143 / -0.102 / -1.13 | 122 / +0.104 / 1.59 | 265 / -0.007 / -0.11 | -0.102 / +0.072 | 0.56 | -0.025 | fail |
| B5-m0.75-v3-Dnone-S-guest | X3 | 121 / -0.232 / -1.48 | 118 / +0.184 / 2.08 | 239 / -0.027 / -0.27 | -0.090 / -0.044 | 0.64 | -0.110 | fail |
| B4-partb-k1-S-full | X3 | 511 / +0.054 / 0.19 | 367 / -0.186 / -1.49 | 878 / -0.047 / -0.26 | +0.157 / -0.893 | 0.35 | -0.194 | fail |
| B4-partb-k1-S-full | X4 | 566 / +0.088 / 0.35 | 402 / -0.258 / -2.27 | 968 / -0.055 / -0.33 | +0.141 / -0.778 | 0.35 | -0.179 | fail |
| B2-z0.75-Uall-long-t1s1-full | X1 | 433 / -0.019 / -0.26 | 450 / -0.041 / -0.60 | 883 / -0.030 / -0.60 | +0.064 / -0.261 | 0.59 | -0.136 | fail |
| B2-z0.75-Uall-long-t1s1-guest | X1 | 383 / -0.033 / -0.40 | 413 / -0.046 / -0.65 | 796 / -0.040 / -0.73 | +0.054 / -0.307 | 0.53 | -0.152 | fail |
| B3-LOR-p0.1-Vany-long-S-guest | X3 | 8,566 / -0.112 / -2.36 | 9,419 / -0.047 / -1.38 | 17,985 / -0.078 / -2.69 | +0.139 / -0.358 | 0.24 | -0.149 | fail |
| B3-LOR-p0.1-Vlowvol-long-S-guest | X3 | 5,892 / -0.107 / -2.11 | 6,450 / -0.074 / -2.12 | 12,342 / -0.090 / -2.96 | +0.150 / -0.378 | 0.24 | -0.160 | fail |

Live CWT14 longs in Testing 2 (t05s1). Each cell is open-history n / exp / t.

| list | base | X3 qqq_fo | best filter exp (which) |
|---|---|---|---|
| ORL p05 any (full) | 105,023 / -0.094 / -10.1 | 47,299 / -0.086 / -7.4 | -0.086 (X3) |
| ORL p05 lowvol (full) | 74,014 / -0.091 / -9.4 | 33,720 / -0.082 / -6.8 | -0.082 (X3) |
| ORL p10 any (guest) | 39,989 / -0.091 / -7.1 | 17,985 / -0.076 / -4.9 | -0.076 (X3) |
| ORL p10 lowvol (full) | 31,676 / -0.089 / -7.8 | 14,227 / -0.082 / -5.5 | -0.082 (X3) |
| PDL p05 any (full) | 66,875 / -0.088 / -10.1 | 32,989 / -0.077 / -7.1 | -0.075 (X4) |
| PDL p05 lowvol (full) | 44,026 / -0.096 / -10.0 | 22,122 / -0.081 / -6.7 | -0.081 (X3) |
| PDL p10 any (full) | 37,499 / -0.086 / -8.8 | 18,289 / -0.075 / -6.3 | -0.071 (X2) |
| PDL p10 lowvol (full) | 20,080 / -0.095 / -8.9 | 9,976 / -0.084 / -6.1 | -0.083 (X4) |

## Routing
- **Primary / locked-block score:** none.
- **Testing near-miss:** none.
  - Do not add an index filter to the Testing-2 CWT14 longs. It would halve their count and leave them at about -0.08R.
  - The existing evidence (every CWT14 long at -0.086..-0.096R, t -7 to -10) argues for reviewing those 8 setups at their 4-session scorecard. Per rule 20, the owner must be prompted before any removal.
- **Backlog:**
  - `nightly-1012-cwt14-long-index-confirm` -> failed (800).
  - `nightly-1012-same-side-crowding-cap` -> failed (3).
  - New idea 1: `bdi1012-signal-breadth-gate`. It treats the running count of same-side book signals as an intraday day-type signal. It is untested, and a sibling of the regime1009 breadth gates (failed), so it must clear that lineage's bar.
- **Drop:** nothing is dropped outright. Both lineages stay in the backlog with their numbers (rule 18: a rework comes first).

## Day-over-day (charter)
- **10-11:** ix-gate scored 912 configurations of market-aware gates on the live lists, and 0 passed.
- **10-12:** the same idea on the new CWT package-B longs (800) plus the book crowding cap (3), and 0 passed.
- **What was learned:** the market's direction at the entry bar does not rescue failed-breakdown longs. Their loss comes from down sessions, and a filter that knows only the entry bar's state cannot tell those sessions apart. Crowding is the symptom of such a day, not its cause.
- **Next:** test whether a causal day-type signal (new idea 1) separates those sessions, against the regime1009 bar.

## Count
- **This round:** 803 configurations (800 + 3).
- **Lineage bars:**
  - ixconf: B2 N = 2,956 -> t >= 4.00; B3 N = 123,363 -> t >= 4.84; B4 N = 2,924 -> t >= 4.00; B5 N = 30,970 -> t >= 4.55.
  - crowd: N = 3 -> floor 1.5. The window-open-cluster and exhaustion-cluster counts are unknown, so the floor is used.
- **Expected false positives at p 0.05:** about 40. The best t observed with n >= 150 is -0.11.

## Files
- `PLAN.md` (pre-declaration)
- `score.py` (one process; it builds `data/index_state.parquet`, which is git-ignored, about 7 min, then scores in about 10 min)
- `results_a.csv` (960 rows: 160 base lists + 800 filtered)
- `results_b.csv` (4 rows)
- Patterns: today's 223 classified losers (primary 5, Testing 1 79, Testing 2 139) were merged from `../nightly1012/patterns_1012.csv` into `../patterns.csv`, with no duplicates. Testing-1/2 losses are understated by the ~65 unreconciled orders (restated tomorrow).
