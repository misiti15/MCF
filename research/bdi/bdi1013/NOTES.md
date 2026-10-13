# BDI 2026-10-13: passive-limit entry for the 09:45 dip (A) and a split-tape gate for shorts (B)

*Educational only - not financial advice. These are backtests on the open two-year history (426 sessions,
2024-10..2026-10-07), with production costs in. Nothing here is paper or live, except the labelled 2026-10-13
replay. The rule-19 locked block was never loaded, and no holdout was scored.*

`PLAN.md` was written before any scoring. Two deviations from it, both stated here:
- The Part A full-cost sensitivity was not run, because no finalist is positive even at the fee-only charge.
- Two Part B lists with both sides (orb20_a, intraday_momentum) were left out, as PLAN's 35-list definition says.

**Configurations scored: 1,327**, which is exactly the declared N.

| part | configurations | try-count bar |
|---|---|---|
| A | 882 + 75 controls = 957 | lineage dips1013-B + A = 102,978, so t >= **4.80** (study-only bar 3.70) |
| B | 370 | lineage ix-gate 912 + regime1009 1,052 + B = 2,334, so t >= **3.94** |

## 1. patterns.csv
- Added **432 loser rows for 2026-10-13**, using the nightly1012 `ltype.py` classifier unchanged (`patterns_1013.py`).
  The merge can be re-run without duplicating rows.
- By account: Primary 9, Testing 1 210, Testing 2 213.
- Testing 1's loss types:

  | loss type | rows |
  |---|---|
  | gave_back_gains | 61 |
  | late_hold | 53 |
  | never_worked | 48 |
  | small MFE then failed | 38 |
  | stopped_then_reversed | 5 |
  | wrong_side_after_big_swing | 5 |

- Testing 2 is dominated by stopped_then_reversed (50) and small-MFE fails (49): the tight t05 targets again.
- 13 setup x loss-type patterns have now been seen on 3 or more days. All are on heat_fade, exhaustion or MF2, which
  are already in the backlog or under review.

## 2. Part A: passive limit entry for the 09:45 dip. FAILED (0 of 957)
**Failures first**
- **Only 1 of 864 limit and chase configurations has open expectancy > 0:**
  - S6-PC-p0.75-flat-qqqmid | LIM-a10-v1 | t1s1: n 1,784, +0.008R, t 0.16.
  - The best limit t among configurations with n >= 150 is 0.16, against a bar of 4.80.
- **0 of 36 finalists meet the research gate or the Testing-1 bar.**
- **Adverse selection eats the price improvement.** Each row below is the median over the 6 signals and 3 exits,
  with v = minutes the order stays valid:

  | limit (v = 1 / 10 min) | fill rate | gain on filled vs market | market R of filled signals | market R of unfilled signals |
  |---|---|---|---|---|
  | at last price (b0) | 74% / 90% | +0.058R | -0.14R | **+0.15 / +0.63R** |
  | -5 bps | 62% / 85% | +0.11R | -0.18R | +0.13 / +0.59R |
  | -10 bps | 50% / 78% | +0.15R | -0.22R | +0.09 / +0.54R |
  | -20 bps | 32% / 67% | +0.23R | -0.29 / -0.31R | +0.04 / +0.44R |
  | -0.05 ATR | 31% / 67% | +0.26R | -0.31R | +0.05 / +0.46R |
  | -0.10 ATR | 11% / 47% | +0.45R | -0.51R | -0.01 / +0.33R |

  - The limit fills on the dips that keep falling. The bounces never come back to the order.
  - The deeper or longer the order, the better the fill price, but the worse the trades that fill.
  - Net expectancy moves from about -0.07R (market) to about -0.06R (limit). Costs are not the binding constraint.
- **Chasing unfilled signals with a market order** (CHASE) is never positive: the maximum t is -0.62.
- **The market baselines reproduce dips1013.** S4 = B-B-p0.75-capd at t1s05: -0.050R here against -0.048R there.
  None of the 18 is positive.

**What remains real.**
- The relative edge over a same-minute random market long is still there: excess_mkt +0.03 to +0.08R, t 3-5.5.
- Against the fair control, a random stock with the same limit order, the limit lines' excess shrinks to +0.01 to
  +0.07R, mostly with t < 2.
- The edge is relative only, and a passive limit cannot harvest it.

**Finalists.** For each signal x exit, the best limit configuration on train, next to its market baseline. All 36
rows are in `limit_finalists.csv`. Every row: research_pass False, testing_pass False.

| finalist | train n / exp / t | valid n / exp / t | open n / exp / t | excess vs limit control (t) | up / down |
|---|---|---|---|---|---|
| S1 O-p0.75 LIM-b20-v1 t1s05 | 9,530 / -0.039 / -1.0 | 13,850 / -0.079 / -3.7 | 23,382 / -0.063 / -3.1 | +0.006 (0.8) | +0.08 / -0.15 |
| S2 O-p0.75-capd LIM-a05-v1 t1s05 | 4,743 / -0.040 / -1.1 | 6,382 / -0.089 / -4.5 | 11,125 / -0.068 / -3.5 | +0.016 (1.7) | +0.04 / -0.14 |
| S3 O-p0.75-qqqmid LIM-a05-v10 t1s1 | 11,700 / -0.075 / -2.4 | 18,290 / -0.070 / -2.2 | 29,994 / -0.072 / -3.2 | +0.028 (2.4) | +0.09 / -0.23 |
| S4 B-p0.75-capd LIM-a05-v1 t1s1 | 2,928 / -0.007 / -0.1 | 4,084 / -0.035 / -1.0 | 7,012 / -0.023 / -0.7 | +0.040 (2.4) | +0.18 / -0.18 |
| S5 B-p1.0-capd LIM-a05-v1 t1s05 | 1,984 / +0.024 / 0.4 | 2,938 / -0.063 / -2.5 | 4,922 / -0.028 / -0.9 | +0.045 (3.2) | +0.11 / -0.11 |
| S5 B-p1.0-capd LIM-b10-v1 t1s1 | 3,167 / +0.010 / 0.2 | 4,882 / -0.057 / -1.6 | 8,049 / -0.030 / -0.9 | +0.032 (1.9) | +0.21 / -0.21 |
| S6 PC-flat-qqqmid LIM-a10-v10 t1s1 | 3,420 / -0.002 / -0.0 | 4,512 / -0.019 / -0.5 | 7,932 / -0.012 / -0.4 | +0.072 (4.5) | +0.15 / -0.18 |

**Verdict:** failed. **Routing:** backlog, as failed. The 09:45 dip edge is closed for single-name long entries,
whether the entry is a market order or a passive limit. The only open route left is the hedged version (long the
dip, short beta), which pays a second spread.

## 3. Part B: split-tape / divergence gate for SHORT setups
Method:
- 35 live short lists from indexlink: 9 Primary `-cur` and 26 Testing 1. Lab R is already re-costed with the
  time-of-day entry cost.
- 10 gates, each scored on every list plus 2 pools.
- The 1-minute context reproduces the frames: QQQ fromOpen p99 |diff| is 1e-5%.

**Failures first**
- **No gate makes any list pass the Primary bar** (0 of 370). Kept expectancy stays negative on every pool.
  - The best primary list is RW6G1-cur + G10: n 409, +0.28R, t 2.69, but its busiest session holds 55% of its trades.
- **The owner-described gate G1 does not meet the Testing bar on the history.** G1 skips a short when QQQ is above its
  open and VWAP while IWM is below its open. On 14% of shorts:
  - Testing 1 pool: kept-minus-blocked +0.045R, t 1.88. Train +0.004 / valid +0.010.
  - Primary pool: +0.024R, t 0.50, and it makes valid slightly worse (-0.0005).
  - It improves both halves on 18 of 35 lists. The portfolio rule needs 75%.
- QQQ up (G3/G4) and SPY up (G5), with no small-cap leg, do nothing. Kept-minus-blocked t is -0.3 to 1.1, as in
  ix-gate.
- **On 2026-10-13 G1 would not have helped** (replay, descriptive). It blocks 185 of Testing 1's 275 shorts
  (-$395), but the kept ones were worse: -$365, -0.26R against -0.16R blocked.

**What passed: G7 `div0.50`. It meets the pre-declared Testing-1 bar only.** G7 skips a new short while QQQ's
fromOpen minus IWM's fromOpen is 0.50% or more.

| book | blocked | base exp | kept exp | blocked exp | kept-blocked (t) | change train / valid | kept up / down |
|---|---|---|---|---|---|---|---|
| Testing 1 pool (281,267) | 20.9% | -0.046 | -0.035 | -0.087 | **+0.052 (2.23)** | +0.006 / +0.017 | -0.18 / +0.14 |
| Primary pool (23,807) | 15.6% | -0.049 | -0.040 | -0.098 | +0.059 (1.13) | +0.014 / +0.007 | -0.17 / +0.13 |

- The neighbours have the same sign on the Testing 1 pool:
  - div 0.25: +0.038, t 1.85;
  - div 0.75: +0.063, t 1.96;
  - G9 split+div: +0.055, t 1.84.
- Biggest per-list effects: RW3 (t 3.44), RW2 (2.12), RW7 (1.97), exhaustion_short-FD (1.94) and heat_fade_short-FD
  (1.96).
- Weak lists (Primary): MF1-cur is worse (t -0.89), MF2-cur is worse (-1.07), and NS3-cur is worse (-0.83).
- **Caveats.**
  - t 2.23 is far below the lineage bar of 3.94, and G7 is one of 10 gates tried.
  - It cuts losses but does not make shorts profitable: the kept Testing 1 shorts still lose -0.035R, and WF is 0.35.
  - On 2026-10-13 QQQ - IWM was at or above 0.75% all day, so G7 would have blocked **every** short in every account:
    T1 -$760, Primary -$99, T2 -$171 avoided (a one-day anecdote).

**Verdict:**
- Primary: no change.
- **Testing 1: G7 qualifies as an experimental tag** ("skip new shorts while QQQ fo - IWM fo >= 0.50%").
- It needs an mcf/ hook: the runner has no intraday QQQ/IWM context for lab setups. Only `fo-` and `gap+` gates
  exist in `mcf/strategies/setups.py`. That hook is the lead's decision, so no config is edited here.
- Backlog: G7 as a finalist, G1 as failed.

## Files
- `PLAN.md`: the pre-declaration.
- `patterns_1013.py`: the patterns.csv merge.
- `limit945.py`: Part A prep. Its output stays in scratch and has been deleted.
- `score_limit.py` writes `limit_results.csv` (all 957 configurations plus the chase controls), `limit_finalists.csv`
  and `limit_summary.json`.
- `splitgate.py` writes `splitgate_results.csv` and `splitgate_summary.json`.
- `replay1013.py` writes `replay1013.csv`.
