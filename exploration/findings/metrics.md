# Track 4: alternative success metrics

Educational only — not financial advice.

**Data.** All 10 live journals (run 1, closed trades), from 10-23 to 11-27. R is LR8 after costs. A signal that appears in several accounts is counted once, using the same key as `footrace.live_trades`. This gives 177 setups with at least 20 trades, 83 long and 94 short, for 28,347 trades. Scripts and outputs are in `exploration/sandbox/metrics/`. The locked holdout was not read.

**Configurations tried tonight (this track):** about 69 in all.
- 12 ranking metrics, each checked for rank agreement and for H1 to H2 prediction.
- 10 metrics × 3 groups in rolling weekly folds.
- 12 risk-persistence pairs.
- 3 RISK-BUDGET replays. These 3 are the only edge claims; the rest are descriptive or validation tests.

Cumulative count is about 9,432.

**Rule changes inside the window (ledger):**

| Date | Change |
|---|---|
| 10-28 | Primary size about $4k |
| 10-29 | −2R latch on closed R |
| 10-30 | Testing cost filter |
| 11-11 | TEAM-6 |
| 11-12 | LR8 costs and account restructure. LR8 is applied to every row here, so the whole window is on one cost basis. |
| 11-17 | TSZ1 half lots in testing. This lowers dollar risk only; R is unaffected. |
| 11-19 | Epoch 1 and U9-TGT |
| 11-20 | Stop rounding and FOOTRACE-EXIT |
| 11-21 | Cost-basis fix |
| 11-23 | ST7 out of Primary, BRAKE-BURST |
| 11-27 | GYH V1+V3, ROT-B3, GEN seed |

The next change is 11-30: AV50 for NM-ETF plus the Friday-review moves. Accounts Testing D/E/F and Explore 1 / Live Lab have only 11-16 sessions.

## Headline (numbers first)

1. **No ranking metric predicts next week's result. Risk does persist.**
   - Rolling weekly folds (6 folds, 43-101 setups each) compared each metric measured on all earlier data with the setup's avg R the next week.
   - Mean Spearman rho for the leaderboard score was −0.056 (t −0.64). Every one of the 10 alternatives lies between −0.068 and +0.032, and none has |t| above 1.04 in the pooled set.
   - A setup's daily-R spread persists: rho +0.40, t 6.8.
   - Its worst day persists: rho +0.28, t 3.1.
   - Its lots per day persist: rho +0.73, t 25.
   - Lots per day predicts next week's worst day: rho −0.36, t −5.4.
   - **In short: what we can forecast is how much a setup can hurt, not how much it will make.**

2. **Every one of the 36 setups with a positive record carries the `1 day` tag** (best session at least 50% of its total R).
   - Only 15 of 177 stay positive without their best day, and only 5 without their best two days.
   - Only 1 setup has a day t above 2: NM-RWN5, with 3 sessions.
   - Ranked by "avg R without best 2 days", 4 of the 5 most-ranked On Deck candidates by score drop out of the top 25. Details are in the flip table.

3. **"Green every day" is out of reach by arithmetic, and adding lots does not help.**
   - Primary trades 37.7 lots a day. Lot sd is 0.89R, and the average within-day correlation between lots is **ρ = 0.185**.
   - With ρ above 0, the share of red days tends to Φ(−μ / (s√ρ)) = Φ(−μ / 0.38) as lots are added.
   - So 5% red days needs μ ≥ +0.63R per lot, and 1 red day a week (20%) needs μ ≥ +0.34. The best live edges are about +0.05.
   - At μ = +0.05, Primary would still be red on 45% of days and in 39% of weeks.
   - **With a negative edge, red-day count is a perverse target.** Lowering variance makes a losing book red more often, and only luck makes it green.

## 1. Metric table: how the metrics relate to the current leaderboard score

The current score is avg R × n/(n+20) (`mcf/report/scorecard.py`, SHRINK_N = 20).

| Metric | Median across 177 setups [p10, p90] | Spearman with score | Top-15 overlap |
|---|---|---|---|
| avg R per trade | −0.155 [−0.464, +0.119] | 0.98 | 14/15 |
| R per session | −1.28 [−7.07, +0.98] | 0.87 | 12/15 |
| median day | −0.78 [−3.78, +0.53] | 0.55 | 8/15 |
| worst day | −12.4 [−44.9, −2.5] | 0.56 | 8/15 |
| green-session share | 0.42 [0.19, 0.64] | 0.56 | 6/15 |
| day t | −0.89 [−2.19, +0.72] | 0.81 | 11/15 |
| ulcer (drawdown RMS, R) | 12.1 [1.8, 51.9] | 0.65 (negated) | 8/15 |
| avg R without best day | −0.256 [−0.634, −0.019] | 0.83 | 9/15 |
| avg R without best 2 days | −0.330 [−0.703, −0.112] | 0.75 | 7/15 |
| R per slot-hour | −0.081 [−0.399, +0.061] | 0.93 | 13/15 |
| R per $10k-hour of buying power | — | 0.88 | 12/15 |
| gross avg R (before LR8 fees) | −0.113 [−0.421, +0.161] | 0.97 | 14/15 |
| LR8 fee R per trade (on top of fill slippage) | 0.040 [0.022, 0.073] | — | — |

What the table shows:
- R per slot-hour and R per buying power rank almost exactly like the score. They add nothing.
- The metrics that really re-rank are the consistency and tail ones: median day, worst day, green share, ulcer, and avg R without the best day or two. Their top-15 overlap with the score is only 6-9 of 15.
- Fees booked by LR8 beyond fill prices average 0.04R per trade, about 5.6% of |gross R|. Earlier research put total cost at 0.10-0.12R per trade; that figure includes spread and slippage, which are already inside fill prices here.
- Across setups, the median short does slightly better than the median long: −0.126 vs −0.184 avg R, and −11.4 vs −14.2 worst day.

## 2. Which current decisions would flip

These are the setups on open On Deck / Primary cards in docs/live/decisions.json, plus the Primary four. Ranks are out of 177; rank 1 is best (for ulcer, the smallest drawdown).

| Setup (card) | Acct | n / sess | avg R | Score rank | w/o-2-days rank | day t rank | ulcer rank | Worst day | Best-day share | Flip? |
|---|---|---|---|---|---|---|---|---|---|---|
| GEN-261023-06 (ODB3, short) | gen | 32 / 10 | +0.746 | **1** | 37 | 5 | 19 | −2.0 | 64% | weaker; small n |
| GEN-261022-05 (ODB3, short) | explore1 | 223 / 7 | +0.445 | **2** | **93** | 17 | **134** | −19.4 | 122% | **yes: drops to no** |
| GEN-261023-07 (long, T2) | testing2 | 139 / 11 | +0.460 | **3** | **92** | 19 | 87 | −19.4 | 142% | **yes: drops** |
| GEN-261026-07 (ODB3, short) | testing2 | 238 / 8 | +0.416 | 4 | 6 | 9 | 26 | −2.7 | 95% | holds |
| GEN-261020-09 (ODB3, long) | gen | 259 / 12 | +0.293 | 5 | 25 | 11 | 99 | −10.4 | 96% | weaker on tail |
| GEN-261027-10 (long) | testingd | 176 / 6 | +0.146 | 12 | **118** | 22 | 110 | −15.5 | 224% | **yes: drops** |
| GEN-261027-01 (ODP2, long) | testinge | 42 / 10 | +0.185 | 13 | **3** | 4 | 5 | −1.9 | 62% | **rises** (80% green sessions) |
| GEN-261029-06 (ODB3, short) | testingd | 295 / 12 | +0.111 | 16 | **5** | 6 | 55 | −6.8 | 67% | **rises** |
| NM-RWR4-ns2-u (ODB3, short) | explore1 | 37 / 7 | +0.134 | 18 | 17 | 15 | 13 | −1.7 | 104% | holds |
| GEN-261021-04 (ODB3, short) | gen | 95 / 8 | +0.095 | 19 | **68** | 25 | 77 | −16.3 | 261% | **yes: drops** |
| L3-gap-slope-fromopen-FD (L3-OUT) | primary | 309 / 22 | +0.063 | 24 | 20 | 23 | 103 | **−35.0** | 160% | worse on tail |
| RW3 (Primary) | primary | 166 / 24 | −0.046 | 47 | 42 | 45 | 82 | −10.2 | — | negative on all |
| RW5 (Primary) | primary | 160 / 25 | −0.071 | 59 | 32 | 54 | 106 | −15.5 | — | negative on all |
| NM-ETF (Primary) | primary | 48 / 16 | −0.096 | 63 | 50 | 49 | 46 | −12.6 | — | negative on all; 81% green sessions |

What would change:
- **Four picks drop** under a consistency ranking: GEN-261022-05, GEN-261023-07, GEN-261027-10 and GEN-261021-04. All four have a best-day share above 120% and a worst day of −15R or worse.
- **Two rise:** GEN-261027-01 and GEN-261029-06.
- **L3's case for staying looks weaker on tail metrics.** It has the 3rd-worst worst day among positive-score setups (−35R) and ulcer rank 103.

However, section 3 shows that neither ordering predicts next week's avg R. The flip changes **tail exposure, not expected R**.

## 3. Does any metric predict? (the test that matters)

### H1 to H2 split
Metrics were measured on 10-23..11-11 (H1) and compared with avg R on 11-12..11-27 (H2). 101 setups qualified.
- Every return metric correlated **negatively** with H2 avg R:
  - score −0.33 [95% CI −0.52, −0.12]
  - avg R without best day −0.38
  - day t −0.23
- Picking the top 20% by score gave H2 avg R of −0.300, against a random-pick band of [−0.285, +0.009].
- Only worst day and ulcer were near zero: top 20% at −0.15, close to random.
- The split mixes regimes: the short-side drawdown came after 11-19, and Epoch 1 started 11-19. So the reversal is probably market regime, not a law.

### Rolling weekly folds (6 folds)
Pooled mean rho is about 0 for every metric (table in `predict_roll_out.txt`).
- Within shorts only, the consistency metrics picked slightly better weeks:
  - median day: top-20% excess +0.084 R/trade (t 2.19)
  - worst day: +0.101 (t 1.99)
  - green share: +0.103 (t 2.36)
- Within longs, nothing works: all excesses are ≤ +0.02 and most are negative.
- With 30 tests these short-side hints are within multiple-testing noise. They are a lead, not a result.

### Risk persistence (`risk_persist_out.txt`)

| Past measure → next-week measure | Mean rho | t |
|---|---|---|
| avg R → avg R | −0.07 | −0.88 |
| daily sd → daily sd | +0.40 | 6.83 |
| worst day → worst day | +0.28 | 3.05 |
| lots per day → lots per day | +0.73 | 25.1 |
| lots per day → worst day | −0.36 | −5.43 |
| ulcer → worst day | −0.29 | −2.88 |

### RISK-BUDGET replay (3 configurations)
Since risk persists, I tested sizing down by past daily-R sd. Each lot's size was set to min(1, K / past daily sd), walk-forward, size cuts only, with K = 2, 3 and 5.
- It beats random weight shuffles: 96-98th percentile on total R and on worst-5 days.
- **It does not beat a uniform size cut matched to the same exposure.**
  - All accounts at K = 2: −2,990R vs −2,850R for the uniform cut; worst-5 −507 vs −472.
- Red days go from 132 to 137.
- 68 setups do better and 107 worse than under the uniform cut.
- This repeats the standing result (table (a), tail levers): **an exposure-matched cut wins.** Do not adopt RISK-BUDGET.

## 4. What "green every day" requires (Primary, LR8)

Model: daily R = sum of N lots, each with mean μ and sd s, and in-day correlation ρ. Then sd_day = s·√(N(1+(N−1)ρ)).

Measured on Primary:
- N = 37.7, s = 0.89, ρ = 0.185
- day mean −5.9, day sd 17.4
- skew +0.32, excess kurtosis 1.5
- the 5 worst days carry 64% of all losing-day R

Other accounts: ρ is 0.02-0.27. Testing D/E, GEN, Graveyard and T2 sit at 0.02-0.06, so their daily noise does shrink with more lots.

| Lot edge μ | Red-day share | Red days per 21-session month | Red-week share | 20-session 5th-percentile floor |
|---|---|---|---|---|
| −0.16 (now) | 65% (actual 68%) | 13.7 | 81% | −233R |
| 0.00 | 50% | 10.5 | 50% | −112R |
| +0.05 | 45% | 9.5 | 39% | −75R |
| +0.10 | 40% | 8.5 | 29% | −37R |
| +0.15 | about 35% | about 7.5 | 20% (4 green weeks in 5) | about 0R |
| +0.20 | 31% | 6.5 | 13% | +39R |
| +0.50 | 11% | 2.3 | about 0% | +265R |

To be red on at most 1 day in 20 (5%) at ρ = 0.185 and N = 38, the book needs μ ≥ +0.67R per lot. The limit as N grows is +0.63R. For comparison, the best live setup without its best day earns about +0.12.

**Two levers exist, and only one helps right now:**
1. **Raise μ, the per-lot edge.** This is the only way to more green days.
2. **Lower ρ (decorrelate) or reduce the tail.** This helps green days only once μ > 0. While μ < 0 it makes red days *more* regular, though it does shrink the worst day and the drawdown.

Hence the order the owner set is right: green weeks first, then green days, then loss prevention. But at μ < 0, loss prevention (the tail and the floor) is the only part that can be measured as progress today.

### Proposed weekly-review metric set

Measured on Primary today. The bars are staged so that a negative-edge book cannot "win" by gambling.

| Metric | Primary 10-23..11-27 | Stage 1 bar (now, μ ≤ 0) | Stage 2 bar (μ > 0 shown) |
|---|---|---|---|
| R per lot (week and 20-session) with day t | −0.156, day t −1.69 | trend up; never judged alone | > +0.05 with day t > 2 over 20 sessions |
| Median day R | −4.1 (weekly −20.0..−2.5) | > −2 | > 0 |
| Worst day R | −42.3 (5 days ≤ −20R) | ≥ −20R (no day below) | ≥ −15R |
| 20-session rolling R floor | −142.7 (now −136.6) | ≥ −40R | ≥ 0 |
| Red days per week | 3.2 of 5 | report only (perverse while μ < 0) | ≤ 2.5 |
| Green weeks, rolling 5 | 1 of 6 | report only | ≥ 3 of 5 |
| In-day lot correlation ρ and lots per day | 0.185 / 37.7 | report (a persistent risk input) | ρ ≤ 0.10 |
| Per setup: avg R w/o best 2 days, worst day, best-day share | see table | gate: best-day share < 50% **or** worst day ≥ −10R | same |

## Confidence

- **High:**
  - The green-day arithmetic (a closed form, with ρ from 25 sessions × 38 lots).
  - Risk persistence (t 6.8, 3.1 and 25).
  - The fact that every positive setup is a `1 day` record (a direct count).
- **Medium:**
  - "No metric predicts next week": only 6 weekly folds, setups overlap across folds, and one regime break falls inside the window.
- **Low:**
  - The short-side consistency-metric hint (t about 2 among 30 tests).
  - Any claim that the flipped picks will do better. Nothing here shows that.

Sources:
- `exploration/sandbox/metrics/*_out.txt`
- `mcf/report/scorecard.py` (SHRINK_N)
- docs/live/decisions.json and assignments.json (asof 11-30)
- exploration/PRIOR_RESEARCH.md
- research/ledger.jsonl, via the PRIOR_RESEARCH rule table

## PROPOSAL candidates

### P1. WEEKLY-SCORECARD-S1: staged weekly review metrics (report only)
- **What:** add the table above to the weekly review. Red days and green weeks become report-only while 20-session R per lot is ≤ 0. Stage-1 bars: worst day ≥ −20R, 20-session floor ≥ −40R, median day > −2R.
- **Expected effect on weekly R:** 0R directly. Its value is that it stops reviews from rewarding a variance-driven green week; the last 6 weeks had 1 green week out of 6, with the green one carried by 11-12. Uncertainty: none on R.
- **Risk:** low. The main risk is a stalled stage 2.
- **Experiment:** compute the set on Primary and on each testing account every Friday from 11-30 to 12-18 (3 reviews). Success means the set is computed reproducibly from journals (a script under exploration/ or research/) and the owner finds it changes at least 1 decision or caveat.
- **Can start Monday 11-30 without touching Primary rules:** yes. It is reporting only.

### P2. CONSIST-SHADOW: score On Deck candidates two ways forward
- **What:** freeze two lists today from the live record. Primary and the Graveyard are excluded.
  - List A is the top 8 by leaderboard score: GEN-261023-06, -261022-05, -261023-07, -261026-07, -261020-09, NM-RWN5, GEN-261021-01, -261026-03. Its avg R is +0.418 and its mean worst day −5.7R.
  - List B is every setup passing the consistency gate (avg R w/o best 2 days > 0, or best-day share < 50% with worst day ≥ −10R). Only 5 pass: NM-RWN5, GEN-261021-01, GEN-261027-01, GEN-261023-09, GEN-261029-06. Its avg R is +0.185 and its mean worst day −1.9R.
  - Score both lists forward on the trades they already take in their current testing accounts.
- **Expected effect on weekly R:** about 0 ± 0.05 R/trade on expected R (section 3 shows no predictive difference). On the tail, list B's worst day should be about 30-60% smaller, because worst day persists (rho 0.28) and list B's worst day is now about one third of list A's.
- **Risk:** none. Nothing is moved; this is a shadow on existing trades.
- **Experiment:**
  - Accounts: whichever testing accounts the setups already run in.
  - Baseline: list A.
  - Duration: 15 sessions (11-30 .. 12-18).
  - Success: list B's worst day and 15-session floor at least 30% better than list A's, with R per trade no more than 0.05 worse, day-clustered and reported with avg R w/o best day.
  - If it passes, the promotion standard adds the consistency gate.
- **Can start Monday:** yes. It is pure scoring of trades that already happen.

### P3. EXPOSURE-FLOOR-CHECK: pair any "red days" lever with its exposure-matched size cut
- **What:** a standing review rule. Any lever claimed to improve red days or worst days is reported next to a uniform size cut with the same exposure, and is adopted only if it beats that cut.
- **Evidence:** RISK-BUDGET tonight is the newest example. It beat random weights at the 96-98th percentile but lost to the matched cut (−2,990R vs −2,850R; worst-5 −507 vs −472).
- **Expected effect on weekly R:** prevents adopting levers that are just disguised size cuts. Direct effect 0R.
- **Risk:** low.
- **Experiment:** apply it to the pending tail cards (LATCH-OPEN, B8, S8) in the 11-30 review. For LATCH-OPEN this is already reported (E = 1.00).
- **Can start Monday:** yes. It is review process only.

Educational only — not financial advice.
