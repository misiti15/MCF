# BDI direction1020: how much of the day's direction is knowable at 30 / 45 / 60 minutes, and does tilting the book help?

*Educational only — not financial advice. These are backtest results on the open two-year history (rule 7: not paper or
live). Costs are in: production + time-of-day entry costs on every entry. The locked block (2024-11-01..2025-02-28) was
never read: rows are dropped on load, every script asserts none survive, and `MCF_HIST_ALLOW_LOCKED` is asserted unset.
No holdout was scored. `PLAN.md` was written before anything was computed and was not changed.*

**Configurations: Part A 312 descriptive measurements (bar 3.39); Part B 76 policies (38 x 2 books), bar
max(1.5, sqrt(2 ln 76)) = 2.94; market-context-gate lineage N 2,549 -> 3.96.**
Train = open sessions <= 2025-12-31 (245 days with full index data); valid = 2026-01-01..2026-10-16 (199 days; Part B
entries end 2026-10-07, 192 days).

## Plain-English answer to the owner
- **Very little of the rest of the day is knowable at 10:00-11:00.** Across SPY, QQQ and IWM, the from-open move
  predicts the sign of the rest of the day 54-55% of the time in train and **49-52% in valid**. In valid that is no
  better than "always guess up" (51-52%). Correlations are about +0.1 to +0.17 in train and **about 0 in valid**
  (-0.06..+0.00 for the 10:00-11:00 checkpoints). The train numbers are inflated by a handful of extreme days
  (April 2025): on ranks (Spearman) train is +0.03..+0.10.
- **The 45- and 60-minute marks are not better than the 30-minute mark.** Waiting longer leaves less day to predict,
  and the signal does not get stronger.
- **Asymmetry: up-opens tend to continue, down-opens do not.**
  - When the index is up at the checkpoint, the rest of the day is also up 56-60% (train) and 51-54% (valid).
  - When it is down, the rest of the day is down only 47-51% of the time.
  - When it is down 0.5% or more by 10:15-11:00 in valid, the rest of the day *rose* 59-63% of the time (n 81-108 per checkpoint, pooled over the 3 indices).
  - That is the market's upward drift plus dip-buying, not a signal to go short-heavy after a weak open.
- **Tilting the book by the early call does not help. 0 of 76 policies pass.**
  - A pure direction tilt (with-trend side x1.5, against-trend side x0.5) adds about 0 R per trade in valid.
  - Skipping the against-trend side shows small positive deltas: best on Primary valid is +0.011..+0.015 R per trade, t 2.1-2.3, below 2.94.
  - That gain is only exposure reduction. Primary's history book loses -0.040 R per trade in valid and is 97% short, so trading less loses less.
  - A random coin-flip direction with the same switching frequency does as well or better: excess is -0.001..-0.006 R.
  - Those policies also lose in down sessions.
- **The setups *do* care about the true direction.** With hindsight (the actual session direction, from 10:00), the same x1.5 / x0.5 tilt would add +0.033 R per trade in valid (t 5.4) and +0.060 in train. The bottleneck is the early call, not the book's sensitivity.
  - Measured against bdi1016 ("the setups do not care enough"), this refines the picture. The setups care about the *true* day direction. bdi1016 could not see that because its early classifier is mostly wrong about the rest of the day.
- **"Start neutral and shift as the day goes on"** was tested directly: the direction is re-read at 10:00, 10:30, 11:00, 12:00 and 13:00 from QQQ's move or from breadth. Valid delta on Primary is -0.004 R (x1.5/x0.5) and +0.004..+0.013 R (skip against), t ≤ 1.81. Excess over random is negative. It fails.

## Failures first
- **Part B: 0 / 76 pass.** No policy has positive excess over a random tilt on both train and valid with valid excess t >= 1.65.
- **Best near-misses (Primary book, valid):**
  - S-Q50-1030-M2 (from 10:30, skip the side against QQQ's from-open move when |move| >= 0.50%): +0.0114 R per trade, t 2.27.
    - Train: +0.0135, t 1.52.
    - Excess vs random: -0.0010.
    - Down sessions: -0.0078.
  - S-Q25-1015-M2: +0.0154, t 2.11. Train +0.0271, t 2.42. Excess -0.0040. Down sessions -0.0119.
- **Best on direction information alone (pooled P+T1, excess):** S-Q25-1000-M1 (x1.5 with / x0.5 against QQQ's sign at 10:00 when |fo| >= 0.25%).
  - Valid +0.0059 R, t 0.94. Train +0.0045, t 0.57.
  - Positive in up and down sessions, but nowhere near the bar.
  - On the Primary book the same policy is -0.0003 R in valid.
- **The contrarian (fade) checks are about 0:** Primary valid +0.000 / +0.001 R; train -0.007 / +0.000.
- **Part A: no feature clears its bar (|t| >= 3.39) in valid.**
  - Train cells that clear it are driven by outliers: SPY from-open at 10:00 has r 0.21, but its Spearman is 0.11; the opening-drive cells have r 0.22-0.27.
  - Every one of those flips to about 0 or a negative value in valid.
  - Breadth reverses sign between splits: breadth-above-open has r +0.06..+0.18 in train and -0.11..-0.17 in valid.
- **Caveats:**
  - Survivorship in the lab universe, which feeds breadth and the entries.
  - Primary history entries include windowed and -FD twins of the same signal (as in bdi1019): day-clustering absorbs the correlation but not the duplication.
  - LIQ (structural exit) and RW6G1 (0 entries) are not covered.
  - The heat_fade setups are now disabled in config, so they are not in the pooled book (unlike bdi1019).
  - Entries use frame outcomes (fixed target and stop): a tilt is a size multiplier and cannot change exits.

## A. Predictability (`predict.py`, `summary_a.py`; `predict_cells.csv`, `predict_terciles.csv`, `predict_asym.csv`, `predict_summary.*`)
Mean over SPY / QQQ / IWM, one observation per day (so statistics are day-clustered by construction). ROD = checkpoint ->
close; AFT = 12:00 -> close. Hit = sign agreement. Always-long baseline = share of up targets.

| checkpoint | feature | ROD train: hit / r / Spearman | ROD valid: hit / r / Spearman | AFT train hit / r | AFT valid hit / r | always-long (ROD valid) |
|---|---|---|---|---|---|---|
| 10:00 (30m) | from open | 0.554 / +0.166 / +0.095 | **0.506 / +0.000 / +0.033** | 0.558 / +0.179 | 0.518 / +0.090 | 0.514 |
| 10:15 (45m) | from open | 0.540 / -0.007 / +0.105 | **0.516 / -0.060 / +0.011** | 0.539 / +0.120 | 0.514 / -0.012 | 0.521 |
| 10:30 (60m) | from open | 0.535 / +0.101 / +0.065 | **0.520 / -0.031 / +0.012** | 0.519 / +0.106 | 0.513 / -0.001 | 0.518 |
| 11:00 (90m) | from open | 0.520 / +0.030 / +0.033 | **0.490 / -0.006 / +0.007** | 0.519 / +0.064 | 0.507 / -0.029 | 0.516 |
| 10:00 | composite (fo, VWAP, breadth, range sign vote) | 0.539 / +0.077 | 0.508 / -0.012 | 0.515 / +0.062 | 0.529 / +0.037 | |
| 10:30 | composite | 0.519 / -0.029 | 0.481 / -0.034 | 0.502 / -0.033 | 0.478 / -0.021 | |
| 10:00 | breadth (share above VWAP) | 0.547 / +0.125 | 0.489 / -0.022 | 0.481 / +0.121 | 0.482 / +0.044 | |
| 10:00 | VXX from open (sign flipped) | 0.555 / +0.110 | 0.485 / +0.009 | 0.550 / +0.131 | 0.524 / +0.105 | |
| 10:30 | gap state (unfilled = gap dir, filled = fade) | 0.541 / +0.051 | 0.528 / +0.046 | 0.547 / +0.061 | 0.529 / +0.064 | |
| 11:00 | gap state | 0.557 / +0.065 | 0.526 / +0.094 | 0.546 / +0.065 | 0.533 / +0.061 | |

- **Same sign in both splits with t >= 2 (of 312 cells):**
  - IWM previous-day and previous-5-day return → afternoon is *negative*: t -2.0 / -2.1 and -2.8 / -2.3. That is mean reversion.
  - QQQ from-open at 10:00 → afternoon: t 2.27 / 2.01.
  - None clears 3.39.
- **Gap state is the only feature positive on ranks in all 48 index × checkpoint × target × split cells:** Spearman +0.005..+0.165, hit 53-55%. It is still weak and is queued as an idea only.
- **Opening drive (09:30-09:45), continued vs reversed by the checkpoint:**
  - Train: the rest of the day follows the from-open sign 55.8% of the time when the drive continued, 51.5% when it reversed.
  - Valid: 50.0% / 51.4%. No usable asymmetry.
- **Continuation by side** (rest of day has the same sign as from-open; pooled over 3 indices, train / valid):

  | checkpoint | from-open > 0 | from-open < 0 | from-open ≤ -0.5% | from-open ≥ +0.5% |
  |---|---|---|---|---|
  | 10:00 | 0.60 / 0.52 | 0.51 / 0.49 | 0.50 / 0.47 | 0.59 / 0.60 |
  | 10:30 | 0.58 / 0.54 | 0.49 / 0.50 | 0.48 / 0.39 | 0.62 / 0.56 |
  | 11:00 | 0.56 / 0.51 | 0.47 / 0.47 | 0.51 / 0.41 | 0.54 / 0.56 |

- **By session class (hindsight; the class uses the whole day):**
  - Up days: from-open and rest of day agree 67% (train) / 61% (valid).
  - Down days: 58% / 48%.
  - Flat days: 36% / 43%.
  - So even on days that end down, the early move points down no better than chance in valid.

## B. Book tilt (`entries.py` copied unchanged from bdi1019; `tilt.py`; `tilt_results.csv`, `tilt_by_setup.csv`, `tilt_out.txt`; `diag_b.py`, `diag_b_out.txt`)
- **Primary book:**
  - The 12 Primary setups enabled in config/default.yaml that have history entries.
  - 53,683 entries: 25,965 train and 27,718 valid. 97% short.
  - Parent expectancy -0.040 R per trade in valid.
- **Pooled book:** 34 Primary + Testing 1 setups, 178,512 entries, 93% short. Parent expectancy -0.029 R per trade in valid.
- **Metrics:** delta = total R change per parent trade; t = day-clustered; random = coin-flip direction on the same active days (analytic mean); excess = delta - random.

| book | policy | train Δ (t) | valid Δ (t) | valid excess (t) | valid Δ up / down | verdict |
|---|---|---|---|---|---|---|
| Primary | S-Q50-1030-M2 skip-against | +0.0135 (1.52) | +0.0114 (2.27) | -0.0010 (-0.19) | +0.040 / -0.008 | fail: t, excess, down |
| Primary | S-Q25-1015-M2 skip-against | +0.0271 (2.42) | +0.0154 (2.11) | -0.0040 (-0.61) | +0.068 / -0.012 | fail: t, excess, down |
| Primary | S-Q25-1000-M1 tilt 1.5/0.5 | +0.0084 (1.08) | -0.0003 (-0.04) | -0.0003 | +0.024 / -0.001 | fail |
| Primary | D-Q25-dyn-M1 (neutral → shift through 13:00) | +0.0058 (0.77) | -0.0040 (-0.55) | -0.0040 | +0.017 / -0.005 | fail |
| Primary | D-Q25-dyn-M2 | +0.0262 (2.36) | +0.0126 (1.81) | -0.0040 (-0.55) | +0.074 / -0.024 | fail |
| Primary | F-Q50-1030-M1 fade | +0.0001 (0.01) | +0.0010 (0.19) | +0.0010 (0.19) | -0.005 / +0.001 | fail |
| Pooled | S-Q25-1000-M1 | +0.0045 (0.57) | +0.0059 (0.94) | +0.0059 (0.94) | +0.023 / +0.011 | fail: t, excess t, plateau |
| Pooled | S-Q25-1000-M2 | +0.0282 (2.79) | +0.0131 (1.65) | +0.0059 (0.94) | +0.056 / -0.015 | fail |

All 76 rows are in `tilt_results.csv`.
- **All M1 policies:** valid |Δ| ≤ 0.010 R and |t| ≤ 1.41.
- **All M2 policies:**
  - Valid Δ is +0.000..+0.015 R, but none has t ≥ 2.94.
  - Every one is negative in valid down sessions.
  - Its gain matches what skipping a random side on the same days gives.

**Why it fails (`diag_b_out.txt`).** Primary shorts entered after 10:00 by the 10:00 QQQ call (valid, mean R):
- QQQ down ≥ 0.25%: -0.051 (8,333).
- Neutral: -0.026 (10,206).
- QQQ up: -0.058 (7,073).

The shorts are not better on days that *start* down. With hindsight, the true direction would be worth +0.033 R per trade in valid (M1 from 10:00, t 5.4; +0.042 from 10:30 using QQQ's actual 10:30 → close sign). That is the ceiling, and the early call captures about 0% of it.

## C. Verdict
- **Direction at 30 / 45 / 60 minutes is close to unknowable for the rest of the day.** On 2026 data, hit rates are 49-52% against a 51-52% always-long baseline, and correlations are about 0. In 2025 they were 52-55% and r ≈ 0.1, driven by a few big days.
- **No tilt policy clears the bar on train and valid. No proposal is made.**
- **Best near-miss:** S-Q50-1030-M2 on Primary (valid +0.011 R, t 2.27, train t 1.52). It is not a direction edge: it loses to a random tilt and loses in down sessions.
- **What would help instead:**
  - The book's dependence on true direction is large (hindsight +0.03..+0.06 R).
  - A *balanced* book (long and short setups that each pay in their own regime) would not need the forecast that early data cannot give.
  - Primary is 97% short on history, so it is a one-way regime bet whatever the morning says.
  - This points to adding regime-robust long setups rather than a direction switch. It is noted here only and not tested tonight.

Files:
- `PLAN.md`
- `predict.py`, `summary_a.py`
- `entries.py`, `setups_used.csv`
- `tilt.py`, `diag_b.py`
- CSVs and txt outputs as listed above
- `backlog_proposals.jsonl`:
  - the failed lineage record
  - one low-priority idea (gap-state input)

Scratch data (entries, features; 7.7 MB) lives in the session scratchpad, not in git.

Educational only — not financial advice.
