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
