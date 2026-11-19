Educational only — not financial advice

# Round 5 volume-track hunt (H5V): results

Research only. No setup, exit, YAML, account or ledger change, and nothing is committed. Plan: `PLAN.md` (pre-declared,
including one grid amendment made on signal counts only). Module: `H5V.py` (live LabStrategy interface, one YAML entry
per leg). Smoke test: `test_module.py` (6 passed). Backtest: `hunt.py`. Freeze: `FREEZE_VOLUME.json`.

- **Data:** the 2-year cache only. FIT = 2024-10 + 2025-03..09 (170 sessions); CHECK = 2025-10-01..2026-11-04 (276
  sessions). The locked block 2024-11..2025-02 and the fresh window were never read.
- **Costs:** always in: LR8, plus borrow on shorts, which trade only easy-to-borrow names.
- **Configurations:** 40 (grid). The job's cumulative N goes from 996 (up to 1,012) to **1,036 (up to 1,052)**.
- **Timeline:** fitsel.json was frozen at 2026-11-19T10:07:21Z, before any check row was built. Check was scored once, and
  the freeze was written at 10:12:15Z. No fresh file existed at either time.

## FIT grid (170 sessions): each leg's pick by total R
| Leg | Pick | trades | /session | avg R | w/o best day | best-day share | t | vs random |
|---|---|---|---|---|---|---|---|---|
| F ETF RSI collapse (L) | r35, bp gate off, t1s1 | 92 | 0.54 | +0.103 | +0.056 | 49% | 1.09 | +0.266 |
| S heavyweight spike fade (S) | adv $1B, RSI >= 70, t05s1 | 21 | 0.12 | +0.124 | +0.086 | 38% | 1.28 | +0.297 |
| C collapse continuation (S) | adv $500M, SPY < open | 106 | 0.62 | +0.001 | -0.030 | 2547% **1 day** | 0.01 | +0.031 |
| X WB4-mirror ETF pop fade (S) | rise >= 0.75%, t05s1 | 70 | 0.41 | +0.095 | +0.048 | 55% **1 day** | 1.04 | +0.072 |
| K one-bar ETF shock snap (L) | EQB $300M, k 0.2, t1s1 | 133 | 0.78 | +0.116 | -0.008 | 106% **1 day** | 0.59 | +0.299 |
| V capitulation bar (L) | vol climax >= 3, t05s1 | 91 | 0.54 | +0.064 | +0.034 | 51% **1 day** | 0.90 | +0.058 |
| Q sector-ETF relative extreme (L) | k 0.5, t1s1 | 165 | 0.97 | +0.028 | +0.003 | 88% **1 day** | 0.40 | +0.219 |

- All 7 picks had FIT total R > 0 and >= 15 trades, so all 7 went to CHECK.
- Every FIT t is below 1.3, so the FIT picks are mostly noise-level. All 40 configs are in `fit_grid.json`.

## CHECK (276 sessions), scored once
| Leg | trades | /session | avg R | w/o best day | best-day share | t | worst day / trade-session | check halves | vs random | overlap with E/M | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F | 356 | 1.29 | +0.028 | -0.022 | 173% | 0.32 | -2.58 | +0.037 / +0.021 | +0.118 | 3% | drop |
| S | 59 | 0.21 | +0.011 | -0.022 | 284% | 0.13 | -1.72 | -0.006 / +0.027 | +0.123 | 0% | drop |
| C | 190 | 0.69 | -0.037 | -0.052 | n/a | -0.56 | -3.35 | +0.037 / -0.101 | -0.080 | 1% | drop |
| **X** | 159 | **0.58** | **+0.105** | **+0.078** | 32% | 1.77 | -2.29 | +0.098 / +0.113 | +0.086 | 12% | **KEPT (H-V1)** |
| **K** | 276 | **1.00** | **+0.187** | **+0.095** | **54% (1 day)** | 1.46 | -1.87 | +0.142 / +0.238 | +0.342 | 3% | **KEPT (H-V2), lumpy** |
| V | 180 | 0.65 | -0.053 | -0.062 | n/a | -1.18 | -1.80 | -0.047 / -0.059 | +0.065 | 2% | drop |
| Q | 538 | 1.95 | -0.038 | -0.047 | n/a | -0.92 | -2.59 | -0.099 / +0.018 | +0.163 | 0% | drop |

## The honest read
- **X (H-V1), the WB4 mirror (fading late-afternoon pops in volatile W-list ETFs, mostly leveraged)**
  - Check: +0.105R at 0.58/session, without the best day +0.078R, both check halves positive, t 1.77.
  - Fit: +0.095R, but 55% of it came on one day (2025-04-16), and fit's second half was -0.014.
  - SOXL is 35% of check trades, NUGT 17%, TECL 14%. That makes X a concentrated, leveraged-ETF book.
  - Shorting a leveraged-long ETF's pop is close to buying the dip in the inverse ETF, so X is close in spirit to E. Only
    12% of its symbol-sessions overlap E/M.
  - Borrow is a flat estimate and the ETB flag is as of today. Both favour X.
- **K (H-V2), a one-bar shock snap in liquid ETFs**
  - Check: +0.187R at 1.0/session.
  - **This is a 1-2 big-day record.** 2026-06-17 alone is 54% of check total R (28 trades: correlated ETFs fire
    together and the day cap binds). The top two days (2026-06-17, 2025-10-29) carry 90% of total R.
  - **Without those two days the avg R is +0.022.** Fit was the same: 106% of fit total R came on 2025-04-09, and fit
    w/o best day was -0.008.
  - K passes the pre-declared keep rule, but it is a shock-day edge, not a steady one. I expect it to miss the FRESH
    bar unless 2023-24 has similar flash-drop days.
  - It is frozen for FRESH because the rule says so; it is not recommended on its own.
- **K and X are correlated.** Daily R correlation is 0.43, and 2026-06-17 is the best day of both. Both lean on
  market-wide shock / snap-back days, as E does.
  - Pooled on check: 1.58/session at +0.157R.
  - Added to BOOK-EM (1.24/session, +0.115 check reference), they would roughly double the narrow book's trades per
    session without lowering its check avg R.
  - That combination was **not** frozen as its own rule (FRESH_PLAN sec. 4 would need it to be), so it is a reading,
    not evidence.
- **Dropped:**
  - F (the M trigger on ETFs), S (heavyweight spike-fade short), C (collapse-continuation short), V (capitulation bar)
    and Q (sector relative extreme).
  - Every one beats its random control except C. But F and S lose money once their best day is removed, and C, V and Q
    lose outright after costs.
  - Same lesson as rounds 1-4: beating random is not enough when the random base loses 0.1-0.2R per trade on these ETF
    names and windows.
- **Short side:** the only short that held is X, an ETF short. Neither stock short (S, C) held. A short-side fade of
  "index-heavyweight one-bar spikes" did not show an edge after costs and borrow.

## Rule-change context
- All figures are backtests on 1-minute bars with one rule set: LR8 costs, the borrow estimate, the round-4 chassis and
  today's ETB flag.
- No live-account window is quoted, so no `research/ledger.jsonl` change falls inside them.
- The 2026-11-19 ledger entries are process only.

Educational only — not financial advice.
