Educational only — not financial advice.

# RWOUT-1127 pre-registration (written 2026-11-27 ~05:30 UTC, before any configuration below was simulated or scored)

Source: inspector_1127 finding #12 (L3-OUT card reads primshorts_1126 selectively: RW3 and RW5 are as negative per trade
on the bench, and their removal was never scored). Question: on Primary's book, is removing L3-gap-slope-fromopen-FD
(L3) better than removing RW3 or RW5, a pair, or all three shorts, and does any removal beat a size-matched random
removal of the same number of lots? Research only: no config, ledger, decisions.json, backlog or live change.

## Configurations (N = 7: every non-empty subset of the three Primary shorts removed; reference = keep)
| id | removed from Primary's P4 lineup (L3, RW3, RW5, NM-ETF-late-dip-di-long) |
|---|---|
| L3-out | L3 (primshorts option b, re-scored here with the random control it never had) |
| RW3-out | RW3-gapdn-rsi5pop-flowsell-short-FD |
| RW5-out | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD |
| L3+RW3-out | L3 and RW3 |
| L3+RW5-out | L3 and RW5 (added for symmetry, disclosed) |
| RW3+RW5-out | RW3 and RW5 (added for symmetry, disclosed) |
| all-three-out | L3, RW3 and RW5 (NM-ETF alone) |
Counted: N ≈ 8,945 (residmap_1127 PREREG lineage: regsteer_1126 8,891 + stopx, cfprimary, taileff, residmap) + 7 = **≈ 8,952**.
Family bar sqrt(2 ln 8,952) ≈ 4.27 shown descriptively; the pass bar uses paired t >= 2.8 (as CF-PRIMARY).

## Engine, lots, costs, contexts
- Engine E4 = research/cfprimary_1127/e4nb.py (numba port of the primshorts_1126 / squeeze_1125 / hedgeb_1126 minute book;
  parity with the Python engine re-checked here on 80 days per context, |dR| < 0.01R/day, before any score). Primary rules:
  77 slots, 30 per setup, <= 3 per symbol per setup, burst brake 30 / 10 min, -2R realised latch, -20R closed+open halt.
- Lots: bench10 regenerated tonight by squeeze_1125/gen.py + hedgeb_1126/build.py (unchanged): **LIVE-L costs on shorts**
  (primshorts_1126 cells_live.json), LR8 research cost on NM-ETF. Expected 52,544 candidates (as cfprimary/taileff).
- Contexts: **BASE** (realised -2R latch = live today) and **LO** (LATCH-OPEN: closed + open <= -2R). A removal = the
  setup's candidates deleted before the engine, so freed slots are refilled as live would.
- Splits: FIT 2024-10 + 2025-03..09 (confirmation only); **CHECK** 2025-10-01..2026-11-04; **T2** 2023-01-03..2024-09-13.
  Locked block 2024-11-01..2025-02-28 filtered at load and asserted absent in every script.

## Control: size-matched random removal (500 draws per config x context, seed 1127)
Per period, n = the number of lots the removed setup(s) took in the keep run. Each draw removes n lots chosen uniformly
from the keep run's taken lots of the three shorts (L3, RW3, RW5 pooled; NM-ETF never removed) and re-simulates (freed
slots refill, as in the config). Reported: random mean and 95th percentile of dR/day, the config's percentile, and the
config's selection value = dR minus random mean. (all-three-out vs its random draw is near-degenerate: noted.)
Descriptive reference: constant cut (every lot scaled by 1 - s, s = removed share of keep lots, per period).

## Live replay (descriptive; primshorts_1126 live_book.py lineup basis)
Primary journal lots (LR8 cost-R) on the 18 sessions L3 traded in Primary (10-21, 10-22, 10-30..11-25), lineup = P4;
the replay only drops lots. Each config, LO off/on: dR/session vs keep, paired t, worst-5; plus 200 size-matched random
removals of the same number of short lots (pooled over the 18 days). Live window rule changes are listed in the report.

## Metrics (per config x context x period)
Avg R/day and dR/day vs keep, paired day t, random p95 / percentile; **red days per month** (x 21); **worst-5 days**
(mean); days <= -10R; **rolling 20-session floor** (min 20-session sum); best-day share of the improvement (largest
single-day delta / total delta) and avg dR/day without the best day; per setup: each remaining setup's dR per month
(21 sessions) and the removed setup(s)' own keep-run R per month, avg R w/o best day and best-day share; lots per session.

## Pass bar (each item on CHECK and on T2 separately, in BASE and in LO)
1. dR/day > 0. 2. dR/day above the random-removal 95th percentile and paired t >= 2.8. 3. Red days per month down by
>= 0.5. 4. Worst-5 no more than 5% worse (cfg worst-5 mean >= 1.05 x keep's). 5. 20-session floor not worse than keep's.
6. Best-day share of the improvement < 25%. 7. No remaining Primary setup worse than -2R per month vs keep.
A config **passes** if all 7 hold on CHECK and T2 in BASE and LO. If it passes but its live replay (LO on) has dR < 0
with t <= -2, the verdict is INCONCLUSIVE. Verdict: PASS if >= 1 config passes; every config reported. If a config
passes: DECISION draft text in REPORT.md (owner decides; a Primary move needs PRIME-RULES / probation handling, outside
09:30-16:00 ET); decisions.json not edited. Caveats carried: survivorship / ETB look-ahead in the bench (primshorts
bench_build.py:103-105) biases absolute levels; the relative comparisons and the random control carry the verdict.
Educational only — not financial advice.
