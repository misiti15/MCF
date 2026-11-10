# SZBAND — how far SPY usually moves from time T (size, not direction), prior-60-day percentile band (Scout, FROZEN 2026-11-10 15:20 ET)

*Educational only — not financial advice. Display research for the owner's COMPASS task (Lead lead-20261110-1500-3). ONE counted
look. Not a trade signal and not a direction call.*

- **Data:** SPY 5-min SIP RTH bars 2024-10-01..2026-11-06 (research/scout-qp1 fetch), **locked block 2024-11-01..2025-02-28
  dropped at load**; sessions with the full 09:30-15:55 set only.
- **Marks T:** 09:45, 10:00, ..., 15:15 (bar closes; a mark's value uses bars that END at or before T).
- **Move:** |SPY close at T+h / close at T - 1| in %, h = 30, 60, 90 min, and 'close' = the 15:55 bar close.
- **Band (method M1-size, point-in-time):** for day i and mark T, take the same move on the PRIOR 60 sessions (i-60 .. i-1; fewer
  than 40 -> skip): median and 80th percentile. Window restarts after the locked gap (no 60-day window spans it).
- **Calibration (the one look):** coverage = share of (day, T) with today's move <= the prior-60 80th pct (target 0.80) and <= the
  median (target 0.50); by horizon; TRAIN (<= 2025-09-30) / VALID (2025-10-01..2026-10-05) / FWD (>= 2026-10-06); by mark;
  day-clustered standard error. Reported, not chosen from: coverage by today's volatility tercile (range so far / prior-60 median
  range at T) - Skeptic's point that a fixed band is too narrow on high-vol days.
- **Owner line (if calibrated within +-3 pt on VALID and FWD):** 'From 13:40, SPY usually moves about 0.25% in the next hour
  (half the days less); on 4 of 5 days less than 0.45%. Size only, not direction.'

## Result (2026-11-10 15:30 ET; the one look)
448 sessions. Coverage of the prior-60-day 80th-pct band (target 0.80) / median (target 0.50):
- **VALID (254 days): calibrated** - 0.787-0.794 / 0.500-0.507 at 30m, 60m, 90m and to the close (se ~0.012-0.018). Flat across
  marks (0.80-0.83 at every mark, 60m).
- **TRAIN (107 days): band too wide** (0.885-0.896 / 0.64-0.66): the window after the locked gap sat in calmer markets than its
  prior 60 days.
- **FWD (24 days, 10-06..11-06): band too narrow** (0.694-0.715 / 0.44; se 0.04-0.07) - recent sessions moved more than the prior
  60 (11-05 -4.2% day inside). Fails the +-3 pt line on FWD.
- **Today's volatility explains the misses, predictably:** in80 on low-vol days 0.91-1.00, high-vol days 0.57-0.68, in every split
  and horizon. A fixed prior-60 band is a base-rate, not a today-rate.
**Verdict:** M1-size is right on average (VALID) but drifts with the vol regime; not card-ready as is. The obvious fix (scale the
prior-60 moves by today's range-so-far ratio, Skeptic's idea for direction) would be a SECOND counted look - proposed, not run.
