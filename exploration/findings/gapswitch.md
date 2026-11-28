# GAPSWITCH: skip Primary shorts on SPY gap-up days? (post-11-30 roster)

Educational only — not financial advice.

Pre-registration: [gapswitch_prereg.md](gapswitch_prereg.md) (commit 10dc6e9b54, pushed before any score). Scripts and raw output: `exploration/sandbox/gapswitch/` (`score.py` → `score_out.txt`, `results.csv`, `per_setup.csv`; `live.py` → `live_out.txt`).

## Verdict in one line
**Fail as a rule. Not proposal-worthy.** On the 2-year bench, every switch adds R, but **random day-skips of the same size add as much or more** (p = 0.42-0.999). Gap-up days are not worse days for RW3/RW5/L3. They lose on every kind of day, so taking any days away helps. The live gap-up pattern is mostly one session (11-11). Keep it only as the read-out already planned in the running GAP-U shadow. Do not switch anything on Monday.

## What was tested (5 configs, counted; plus 2 no-switch baselines)
- **Rosters:** A = RW3 + RW5 + NM-ETF (L3 out); B = A + L3-gap-slope-fromopen-FD.
- **Rule:** decided at 09:30 from SPY's open gap (open vs prior close; no lookahead):
  - G25 = no short entries all day if the gap is ≥ +0.25%;
  - G50 = the same at ≥ +0.50%;
  - H25 = shorts at half size at ≥ +0.25%.
- **Engine:**
  - bench10 candidate lots (regsteer_1126 `cand.parquet`), run through the Primary book (primshorts_1126 `booksim.sim_day`: cap 30 per setup, ≤ 3 lots per symbol, −2R closed latch, −20R halt).
  - Costs: **LIVE-L on shorts**, LR8 research on NM-ETF.
  - Splits: FIT / CHECK / T2. **The locked block was never read** (asserted on every load).
- **Control:** 1,000 random draws per config and split. Each draw skips the same number of random sessions from the same split.
- No new data was built. Every input already existed in the scratch cache.

## Results (book R per session; gain = switch − no switch)
| Config | Split | Days fired | R/day before → after | Gain/day (day t) | **p vs random** | Red days | Worst-5 | Best-day share |
|---|---|---|---|---|---|---|---|---|
| A-G25 | CHECK | 91/276 | −2.10 → −1.33 | +0.76 (3.6) | **0.42** | 169 → 124 | −150.9 (same) | 11% |
| A-G25 | T2 | 134/427 | −1.36 → −1.25 | +0.11 (1.4) | **0.999** | 251 → 208 | −104.8 (same) | 26% |
| A-G25 | FIT | 49/170 | −3.07 → −2.63 | +0.44 (2.4) | 0.94 | 105 → 77 | same | 17% |
| A-G50 | CHECK | 48 | −2.10 → −1.69 | +0.40 (2.6) | **0.43** | 169 → 148 | same | 20% |
| A-G50 | T2 | 64 | −1.36 → −1.34 | +0.02 (0.5) | **0.99** | 251 → 238 | same | 68% (`1 day`) |
| B-G25 | CHECK | 91 | −3.20 → −2.25 | +0.94 (3.5) | **0.65** | 172 → 131 | −197.0 (same) | 9% |
| B-G25 | T2 | 134 | −1.75 → −1.58 | +0.17 (1.6) | **0.997** | 249 → 204 | −119.7 (same) | 18% |
| B-G50 | CHECK | 48 | −3.20 → −2.80 | +0.39 (2.0) | **0.71** | 172 → 155 | same | 21% |
| B-G50 | T2 | 64 | −1.75 → −1.75 | −0.00 (0.0) | **0.998** | 249 → 235 | same | — |
| A-H25 | CHECK | 91 | −2.10 → −1.72 | +0.38 (3.6) | **0.46** | 169 → 171 | same | 11% |
| A-H25 | T2 | 134 | −1.36 → −1.31 | +0.06 (1.4) | **0.997** | 251 → 252 | same | 26% |

FIT rows for G50/B/H25 are in `score_out.txt`. They show the same pattern: gain +0.06 to +0.68, p 0.92-0.97.

**Pass bar check.** The bar needed p ≤ 0.05 on both CHECK and T2. **0 of 5 configs pass; the best p is 0.42.** T2's day t is below 2 in every config. **None reaches the forward-shadow bar** either, which was p ≤ 0.20 on both splits.

**How to read it:**
- **The day t is misleading here.** The no-switch book loses on most days (CHECK R/day −2.1 to −3.2 with LIVE-L). So removing any short-heavy day looks "significant". The random control shows that is all the switch does.
- **Red days fall** (e.g. 169 → 124) only because switched days become NM-ETF-only days near 0R. Half size (H25) leaves red days unchanged.
- **Worst-5 does not change in any config or split.** The book's worst days are not gap-up days.
- **One-big-day check (bench):** best-day share of the gain is 9-26% for G25 (spread out), but 68% for A-G50 on T2.

**Per setup (CHECK; the T2 gains are 3-10x smaller):**
| Setup | Effect of A-G25 / B-G25 | R it makes on non-gap-up days |
|---|---|---|
| RW3 | +103R | −197R |
| RW5 | +107R | −178R |
| L3 | +50R | −255R |
| NM-ETF | 0 | 0 |
- In B-G50, L3 is worse in all three splits (−2 to −9R).
- Better/worse count: 2 better / 0 worse / 1 unchanged in every A config; 3 / 0 / 1 for B-G25; 2 / 1 / 1 for B-G50.

**Shorts by SPY gap bucket (bench, roster A, R/day per setup):**
- **RW3 and RW5 lose in every bucket in every split.**
- On T2 the gap ≥ +0.5% bucket is their *least bad* (−0.03 / −0.10 vs −0.85 / −1.05 on flat days).
- On CHECK it is middling (−0.89 / −1.42).
- L3 is about flat to slightly positive on gap ≥ +0.5% days in all three splits (+0.04 to +0.13). So the bench says the opposite of the live story for L3.

## Live readout (descriptive, in-sample, LR8; Primary, 10-06..11-25, 29 sessions)
| | Gap ≥ +0.25% (10 days) | Gap ≥ +0.5% (6 days) | Other days |
|---|---|---|---|
| RW3 + RW5 shorts | −23.4R | −27.1R | +49 to +53R |
| + L3 | −45.0R | −38.8R | — |
- **One-big-day check:**
  - 11-11 alone (RW5 −15.5R) carries **95-110% of roster A's** gap-up loss (`1 day`). Roster B's share is 65-76%, also `1 day`.
  - On the other gap-up days RW3/RW5 were mixed: 10-19 +1.6, 10-27 +2.1, 11-04 −1.0, 11-09 −0.5 (RW5).
- So live, this is roughly "one bad gap-up day plus L3's open-gap days". The bench, with 64-134 gap-up days per split, does not back it.
- The GAP-U shadow's +42.7R over 11 live sessions is the same in-sample pattern, so it is not independent evidence.
- **Rule changes inside the live window** (ledger effective dates): 10-28 Primary size about $4k, 10-29 −2R latch (closed R), 11-12 LR8 costs and restructure, 11-17 TSZ1, 11-19 Epoch 1 / U9-TGT, 11-20 stop rounding / FOOTRACE-EXIT, 11-21 cost-basis fix, 11-23 ST7 out / BRAKE-BURST. Of the 10 gap-up sessions, 4 fall before 10-28/10-29 and 6 after. **Upcoming:** 11-30 AV50 for NM-ETF exits (bench NM-ETF lots use the old stop; the switch never touches NM-ETF entries).

## Honest read
- The live pain on gap-up days is real money, but on the bench it is a **size effect**. These shorts lose after LIVE-L costs on most days of every type (shorts_autopsy: about +0.03R gross vs about 0.11R cost per lot). Any rule that trades them less "helps", and random days help just as much.
- This repeats shorts_autopsy R1 (26th / 12th percentile, family level, no book). Here it is now tested on the exact Monday roster, inside the Primary book, at two thresholds and at half size.
- The useful part, in the optimistic sense:
  - The lever for Primary's short losses is **exposure** (L3-OUT, LATCH-OPEN, roster size, already in the Monday plan), not the day's gap direction.
  - L3 on gap-up days is, if anything, its better bench bucket. Do not build an L3 gap rule.

## Experiment spec (forward read-out only; no trading effect)
- **Where:** fold it into the running GAP-U regime-switch shadow (scored about 12-10) and the 12-04 / 12-11 readouts. No new job.
- **What:**
  - For the live Primary roster (RW3, RW5, plus L3 if it stays), report each day's SPY gap, the short R on G25 / G50 days, and the R of a **same-day-count random switch** (1,000 draws).
  - Run it on the post-11-30 roster only, with no reuse of the 10-06..11-25 sessions.
- **Success bar (fixed now):**
  - Over ≥ 20 forward sessions with ≥ 6 gap-up days, the gain beats the random control at p ≤ 0.05, and it is positive without the best day.
  - Even then, it must clear the bench result above before it can become a rule. Two independent agreements are needed, because the bench currently says no.
- **Stop rule:** if p > 0.5 at 20 sessions, drop the read-out.

## Configurations tried
- This study: 5 (A-G25, A-G50, B-G25, B-G50, A-H25), scored on 3 splits, with 2 baselines.
- Related earlier tries, counted for multiplicity: shorts_autopsy R1/R4 (2), loss_anatomy gap-up thresholds 0.3 / 0.5 (2), regime_filters SPY-gap cells.
- None of them passes a matched-random control.

Educational only — not financial advice.
