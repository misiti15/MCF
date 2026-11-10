# Skeptic pre-score audit of GATE2 (research/gate2/PLAN.md + gate2.py), 2026-11-09 ~08:50 ET

*Educational only — not financial advice.* Read before any score; nothing run (no data in this container).
Clean: closed-bar reading, next-bar entry, stop-first, gap fills at open, adv20 point-in-time (build_frames shift(1)),
locked block asserted at both reads, C1/C2 paired, day-clustered t. Issues, most serious first:

1. **Sizing configs (lines 186-197) pass on volume cut.** Score = weighted − unweighted = 0.5·Σr(fav) − 0.5·Σr(unfav).
   The lab book is negative (~−0.06R/trade VALID). If ~80% of trades are "unfav" (no reading or wrong side), halving
   them adds +0.5·0.8·0.06 ≈ +0.024R/trade for free, with no timing at all. Fix: score on r minus the setup's own mean
   (TRAIN mean for TRAIN rows, VALID mean for VALID rows), or against 200 random relabelings with the same fav share
   (pass if real delta > 95th pct and day-clustered t on the demeaned delta >= 2.79). Also report r(fav) − r(unfav).
2. **Time lookup can leak (line 191).** `I.get(int(tod), 999)`: any lab tod that is not a 5-minute bar end (e.g. an
   entry minute 1032) maps to 999, so `icx < tix` is always true and a trade entered BEFORE the reading confirmed gets
   x1.5 whenever the day's reading later agrees. Fix: tix = index of the last bar closed at or before the entry minute
   (searchsorted on END_MIN), and assert no tod maps to the default.
3. **Gap artifact after the locked block (lines 37-47).** Daily rows are dropped for 2024-11..2025-02, then shift(1)
   runs across the hole: the first March 2025 row gets a 4-month "daily" return and true range. That single return
   dominates the 60-row beta for ~60 sessions (Mar-May 2025) and inflates ATR for ~14 sessions. With FIRST = 2024-10-01
   and min_periods 40, I-HB has no beta in Oct 2024, so I-HB TRAIN is mostly Mar-Sep 2025 and its first ~3 months pick
   "beta >= 1.2" from one 4-month co-move. Not look-ahead, but a distorted universe. Fix: NaN ret / tr on the first row
   after a gap > 5 calendar days; report I-HB TRAIN sessions actually traded.
4. **Up/down split is nearly automatic here.** Longs come from UP readings (89% close up), shorts from DOWN, so "up
   days positive AND down days positive" is mostly "held days positive". The risk is the ~11% failed-hold days. Add:
   avg R and total R on held vs failed days (close vs open, reporting only), R by side x day type, and the break-even
   hold rate (hold share at which avg R = 0). If break-even is above ~85% the edge is thin vs 89% TRAIN/VALID.
5. **Costs, small:** exit leg pays no spread and no tod multiplier and uses the entry price; tod mult is taken at the
   signal bar. Conservative overall, but state the round-trip cost in R (median cost/R) per config — R can be as small
   as 0.10 ATR, where costs bite.
6. **C1 conditions on a trigger existing that instrument-day** (good: isolates timing). Report n of C1/C2 pairs.

Would convince me: items 1-2 fixed before the score; then the plan's bar with excess-over-C1 t >= 2.79, held- AND
failed-day R reported, break-even hold rate well below the observed rate, avg R w/o best day > 0, forward 20 sessions.
