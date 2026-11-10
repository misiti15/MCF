# SIZEBKT — use predictable move SIZE without direction: a symmetric stop bracket on predicted-big names (Scout, 2026-11-10 05:20 ET)

*Educational only — not financial advice. DESCRIPTIVE gross check, 0 configs scored as rules (Lead lead-20261110-0500-2).
Declared before computing. Data: the HODSEP download (5-min SIP RTH, 2026-09-24..2026-11-09, lab universe; open data).*

- **Decision bars:** 10:00, 10:30, 11:00, ..., 14:00 closes (one row per symbol x bar; >= 6 prior sessions for volume norms;
  adv20 >= $60M; ETPs / index ETFs out; every look-back via a guarded slice).
- **Size predictors (known at the bar close):** rvol15 (last 3 bars' volume / same bars' mean over the prior <= 20 sessions)
  and range_atr (day range so far / ATR14). Quintiles of each, and of their rank-average ("size score").
- **Bracket (no direction):** from the bar close c, buy-stop at c + k ATR and sell-stop at c - k ATR, k = 0.15 and 0.25; the
  first leg touched in bars b+1 .. b+12 enters (both touched in one bar = the worse of the two, counted as a -1R stop: conservative);
  stop at c (risk k ATR), target entry +/- 2k ATR, else exit at the bar b+12 close. Gross R; also the cost in R at production
  costs (1c + 1bp + 4.4bp spread on entry, 1c + 1bp exit, +2c on stops) for reference.
- **Report:** per size-score quintile x k: trigger rate, gross R per trigger, day-clustered t of Q5 minus Q1, per-day sign count,
  first-half vs second-half dates; plus 'size' sanity (mean |60-min move| / ATR by quintile).
- **Reading:** a direction-free bracket earns gross only if moves past +/- k continue more than they whipsaw. If Q5 gross > 0 and
  > Q1 in both halves, it is a lead (then count the family and plan on the 2-year cache); if not, the size signal cannot be
  monetised this way and the angle is closed with numbers.

## Result (2026-11-10 05:40 ET) — CLOSED as a direction-free bracket
246,285 decision rows (1,021 names, 27 days). Size is predicted (|60-min move| / ATR 0.126 -> 0.189 Q1 -> Q5 of the size score),
but the symmetric bracket LOSES before costs and loses MORE where size is predicted: k 0.15 gross R/trigger Q1 -0.066 -> Q5
-0.214 (Q5-Q1 day-t -8.8, 1/27 days +; both halves -0.20 / -0.22); k 0.25 Q1 -0.007 -> Q5 -0.074 (day-t -4.6). Same for rvol15
and range alone. Ambiguous both-touch bars are <= 0.5% (sensitivity excluding them: unchanged). Costs would add 0.12-0.21R.
Reading: at the 5-60 min horizon, predicted size is noise amplitude - price crosses +/- k and comes back through the centre.
A fade of the first excursion is the mirror, but it sits in the heavily tried fade family (and MarcoFlow lesson 5); not proposed.
