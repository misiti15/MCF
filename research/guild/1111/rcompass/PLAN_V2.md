Educational only — not financial advice.

# RCOMPASS v2 — midday-flip standby with no future label (Observer; plan FROZEN 2026-11-11 ~10:00 ET, before any v2 score)

Owner task item 3 (owner-20261111-0821-1), Lead lead-20261111-0900-3. **3 new counted looks (F1, F2, F3), definitions unchanged from v1.**
Lineage for calling a 'lead': REGSW 104 + RCOMPASS v1 3 + v2 3 = N 110 -> full bar sqrt(2 ln 110) = 3.07, BAR90 2.76.
Any Testing move must also clear the market-state family N 2,605 (BAR90 3.57). Skeptic's checklist walked (items on whole-day labels,
shared-day nulls, family N, ex-market, gross first, best-day share).

## What changes vs v1 (the flaw)
v1 compared post-flip trades with 'held_day' = days with NO flip ALL day, which uses the rest of the day (future label).
v2 compares, within family x side x 30-min entry bucket, POST-FLIP trades (the flip mark T < entry minute) with NOT-YET-FLIPPED trades
(no flip mark before the entry minute that day, whether or not the day flips later). Both labels are known at entry.

## Inputs
trades file with columns setup, side, date, tod (entry bar end HHMM), xtod, gross, r, spy_move (Builder's trades_tagged.parquet);
compass rows research/compassbf/compass_2y.csv.gz. Morning reading M and flip times F1/F2/F3 from rcompass.day_flips (imported, unchanged).
Afternoon trades only (tod >= 1200) on reading days. Locked block asserted absent. TRAIN <= 2025-09-30 < VALID.

## Measures
- ex = gross - beta x (side x spy_move), beta fitted per setup on TRAIN only. Gross and net reported beside ex.
- Contrast per (look, family, side, alignment): within each 30-min entry bucket, day-level mean ex of post-flip trades minus day-level
  mean ex of not-yet-flipped trades (Welch day-t), combined across buckets weighted by post-flip days. ALIGNED (trade side = M) is the
  standby target; COUNTER is reported only.
- Book statistic S = post-flip-trade-weighted mean of the aligned contrasts over all family-sides.
- **Shared-day permutation null (Skeptic 11-11):** 500 draws; each draw permutes the vector of day-level flip times across reading days
  of the same M (one permutation shared by every family-side), re-labels trades post / not-yet, recomputes S. p = share of draws with
  S_draw <= S_obs (a standby helps when S_obs is very negative).

## Pass rule (fixed now) — a look is a 'standby candidate' only if ALL hold
1. Aligned S_obs < 0 in TRAIN and in VALID (gross first: the gross contrast is also < 0 in both).
2. S_obs below the 5th percentile of the shared-day null in TRAIN and in VALID.
3. Aligned family-sides with contrast < 0: >= 60% in both periods (Remedies rule: better/worse counts per family-side printed).
4. Combined day-t of the book contrast <= -2.76 (BAR90 at N 110) in VALID; without the best (most negative) day still < 0.
Otherwise the look is closed. A candidate goes to a journal-only forward shadow (XA-EPROC monitor) before anything else.
