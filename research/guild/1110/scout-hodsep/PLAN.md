# HODSEP — what separates near-HOD names that go on to move up from those that don't (Scout, 2026-11-09 19:20 ET)

*Educational only — not financial advice. DESCRIPTIVE, 0 configs (Lead lead-20261109-1910-3). Declared before the data
was downloaded. Hindsight labels are used only to describe; nothing here is a tradable rule.*

- **Data:** Alpaca SIP 5-min RTH bars 2026-09-24..2026-11-09 and daily bars from 2026-06-01, lab universe + 11 SPDR sectors +
  SPY (open data; the locked block is far outside this window).
- **Candidates:** first 5-min bar close per symbol-day in 09:50..14:00 with HOD - close <= 0.25 ATR14 and close >= open;
  adv20 >= $60M; ETPs (SC1 `ETP_RE`) and index ETFs out; >= 5 prior sessions of same-bar volume.
- **Label (hindsight, descriptive):** max high over the next 60 min - close >= 0.75 ATR ("up-mover"). Also the continuous
  forward 60-min close-to-close move in ATR.
- **Features at the bar close (known then):** rvol15 / rvol30 (last 3 / 6 bars' volume vs the same bars' mean over the prior
  <= 20 sessions); sector_ret30 (assigned SPDR sector's last-30-min % return; sector = highest daily-return correlation over
  2026-06-01..2026-09-23, fixed before the sample); sector_minus_stock30; pdcl (prior-day close location in its range);
  gap_vs_sector (stock gap % - sector gap %); plus reference: day range so far / ATR, fromOpen / ATR.
- **Separation:** AUC per feature, label rate in the top vs bottom quintile (lift), mean forward 60-min ATR move by quintile;
  first-half vs second-half dates for stability; days counted. Move Hunt check: each long mover's (non-blackout, decision
  >= 09:50) feature percentile among that day's candidates.
- Output: the one feature with the clearest, stable separation, then its family N before any plan.

## v1 bug and v2 result (2026-11-09 21:30 ET) — CLOSED
- **Bug (found by Skeptic):** candidates started at the 09:50 bar (b = 4); `c[b-6]` / `sa[b-6]` wrapped to the same day's
  15:50 / 15:55 closes, so for 66% of v1 candidates "own 30-min return" was minus the rest-of-day move. v1 numbers are void.
- **v2 (b >= 6 asserted, `win()` refuses negative starts, entry at the b+1 / b+2 open, day-demeaned):** own 30-min return
  Q5-Q1 day-t -1.19 / -0.83 (10-11 of 28 days) -> gone. Sector 30-min return day-t -2.2 (small, wrong sign for 'sector leads').
  Only rvol15 keeps a sign: Q5-Q1 +0.02 ATR in 60 min, day-t 2.8 / 3.7 - a real-looking but tiny selector, below one round
  trip (same scale as GATE2's timing). Volume and day range still predict move SIZE, not direction.
- **Verdict:** HODSEP closed as an angle; nothing to plan. Lesson: guard every look-back window against negative indices.
