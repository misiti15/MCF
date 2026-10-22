# regime1022 PLAN (written 2026-10-22 02:50 UTC, before anything was scored; not edited after scoring)

*Educational only - not financial advice.*

Owner (2026-10-21 night): short setups lost on two up days. Find what each setup is good at, decide which setups get a
market-condition gate (and how we choose), check whether Primary's big losses were an anomaly or need a daily stop,
and add a "Best market conditions" column to the leaderboard.

Data rules: open two-year history (lab frames 2024-10..2026-10-07), locked block 2024-11-01..2025-02-28 never read,
costs always in (production + time-of-day + x3 extended tier, as gates1021 `prod_r_tier`), TRAIN <= 2025-12-31,
VALID 2026-01-01+. Live = paper journals (run 1) of mcf-data* branches, labelled paper. Every configuration counted.

Reuse (not redone): gates1021 scan/setup code, its U7 results and finalists; direction1020 predictability numbers;
ll1020 / nightly1021 loss-limit replays.

## Regime labels (hindsight, one per session, SPY regular session)
- o2c = SPY close / open - 1; range = (high - low) / open; med20 = median range of the previous 20 sessions.
- **Bull** o2c >= +0.5%; **Bear** o2c <= -0.5%; **Choppy** |o2c| < 0.5% and range >= med20; **Quiet** |o2c| < 0.5% and
  range < med20.
- Cut-off sensitivity (descriptive only, not used for any decision): +-0.3% and +-0.75%.

## Part A - Primary big losers (descriptive)
Setups in Primary (assignments.json) whose live paper P/L since start is <= -$100 or whose 10-20 + 10-21 P/L is
<= -$100. For each: live record (Primary only, and all accounts merged), 2-year as-run backtest (refire chain + per-setup
lot cap 3), R by regime, distribution of setup-day R: share of days at or below the 10-21 live setup-day R, their
regimes, and streaks (P(bad day | previous day bad) vs base rate).

## Part B - protection rules (pre-declared, counted)
Books: Primary covered setups (as-run), Testing 1, Testing 2, Graveyard covered setups. Book simulation in time order:
lots exit at their 5-minute-path exit bar; account-wide max 3 lots per symbol (same side only), the account's own
per-strategy and concurrent caps, the account's existing realized stops (Primary account -20R; T1/T2/GY per-setup -2R
realized + -120R account) as the baseline P0 "as-run".
Variants (each per book):
1. per-setup open lots per symbol cap 1 (B1a), 2 (B1b); per-setup total open lots cap 5 (B1c), 10 (B1d)
2. per-setup realized + open-risk stop (open lots counted at -1R): -3R (B2a), -4R (B2b)
3. account-level realized + open-risk stop for the whole book: -10R (B3a), -15R (B3b), -20R (B3c)
4. correlated-cluster cap: block a new lot when >= K same-side open lots (any setup) are in names whose 20-day daily-return
   correlation with the new name is > 0.7: K = 3 (B4a), 5 (B4b)
5. none beyond as-run (B5 = P0)
= 11 variants + P0 per book x 4 books = 48 configurations (plus P0 reference rows).
Judging: total R, avg R, trades kept, worst day, mean of the worst 5% of days, days <= -10R; train and valid apart;
total R compared with random thinning (parent total x kept share).
**Recommend** a variant only if, on Primary: total R >= P0 in train AND valid, beats random thinning in both, keeps
>= 80% of trades, and improves the mean of the worst 5% days by >= 20%. If none passes: the variant with the largest
worst-5% improvement whose total R is no more than 3% below P0 in both splits and keeps >= 90% is offered as
"insurance"; otherwise the answer is "none, it was an anomaly".

## Part C - regime framework and "who gets a gate"
Per covered live setup (Primary, T1, T2, Graveyard): as-run avg R / trades / day-clustered t by regime, train and valid.
Class (pooled train+valid, decided in this order):
- **all-weather**: avg R >= -0.02 in every regime (>= 30 trades) and pooled avg R >= 0.
- **regime specialist**: best regime avg R >= +0.03 with day-clustered t >= 2.0 and > 0 in train and in valid.
- **loser**: everything else (no regime where it reliably earns).
(i) net expectancy over the real regime mix (pooled, per calendar year) for each specialist.
(ii) at-entry detectability: for proxies spy_prev, spy_fo, qqq_fo (10:00 / 10:30 / 11:00 / 12:00), SPY VWAP side,
breadth level, breadth slope: hit rate / precision / recall for "Bull" and "Bear" sessions, train vs valid.
(iii) selection rule - a setup gets a gate only if ALL hold:
  S1 regime split real and stable: unfavourable regime avg R below the rest with t >= 2 (train) and >= 1 (valid);
  S2 a pre-declared at-entry gate captures it (gate delta > 0 in train and valid);
  S3 gated variant keeps >= 80% of trades in both splits and blocks <= 20% of winners;
  S4 gated avg R > parent in train and valid AND total R >= parent total R in both;
  S5 the parent is not all-weather / not profitable in both splits (unless S4 total R rises in both);
  S6 pooled gate-delta t >= the lineage bar max(1.5, sqrt(2 ln N)), N = gates1021 718 + bdi1021 196 + this Part C.
Gates (shorts; longs get the mirror):
  R1 skip if prior SPY session >= +0.5%
  R2 skip if prior SPY >= +0.5% and SPY >= 0 from open
  R3 skip if SPY above its VWAP and SPY >= +0.25% from open
  R4 entries at/after 10:30 only: skip if SPY's 09:30-10:30 move >= +0.25%
  R5 skip if breadth >= 0.60 and breadth rising (d2 > 0)
  U7 (gates1021, re-scored for setups gates1021 did not cover, e.g. Graveyard; counted)
= 6 gates x covered setups (counted exactly in counts.json).
Passing variants -> modules/<setup>-r<k>.py (gates1021 module format) + backlog_proposals.jsonl.

## Part D - leaderboard column
docs/live/regimes.json from Part C (best / worst label, by-regime trades + avg R, class); schema test; dashboard column
"Best conditions" + drill-down table + glossary; Playwright check at 1366 and 390 px.
