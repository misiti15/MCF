# SC1 — event-day gap-and-hold (LONG first, short mirror) (Scout plan, FROZEN 2026-11-09 09:55 ET, before any score)

*Educational only — not financial advice. Pre-registration; nothing scored. Script to follow (research/sc1/sc1.py);
queued after SC2 / C3FR per Lead.*

## Hypothesis
On quiet days the big movers are event names (Move Hunt 10-29 / 11-03: 86% of long and 94% of short top movers were in
the earnings blackout). An event gap that still holds its open, VWAP and half the gap 30-60 minutes in shows persistent
informed demand and keeps going into the close. Daily-horizon earnings studies (er-react-*) are parked; this intraday
event-day entry has never been scored on 2 years (no historical calendar) — the opening-volume proxy sidesteps that.

## Data
1-minute SIP cache (`data/cache_hist/1Min`, open / high / low / close / volume) -> 5-minute RTH bars as gate2 `bars()`
plus a volume column; `lib.daily()` for prior close, ATR14 (prior days) and adv20. **Locked block 2024-11-01..2025-02-28
filtered at read and asserted absent;** rolling windows restart after a > 5-day gap.

## Rule
- Universe: lab names, adv20 >= $60M, not SPY / QQQ / IWM / DIA, no leveraged / inverse ETPs (lab ETP list).
- gap = open / prior close - 1. **Event proxy:** |gap| >= G and 09:30-09:55 volume >= 4 x the name's mean 09:30-09:55
  volume over its prior 20 sessions (>= 15 needed). Earnings blackout is **not** applied (that is the point); the
  report splits blackout-calendar days (`_blackout`, where the calendar covers them) vs other events.
- **Long (gap >= +G), checked once at bar close T:** close > session open, close > session VWAP (from 09:30, typical
  price x volume), close >= prior close + 0.5 x (open - prior close). Enter next bar open. Stop = low of day so far
  - 0.05 ATR_d; skip if entry - stop > 0.6 ATR_d or < 0.10 ATR_d. Exit 15:55 close; once +1R is reached (bar close),
  stop trails to the lowest low of the last 6 five-minute bars (never lowered).
- **Short (gap <= -G):** mirror (below open and VWAP, close <= prior close + 0.5 x gap move, stop = HOD so far + 0.05 ATR_d,
  trail on the highest high of the last 6 bars).
- Costs: production as gate2 `trade()` (tod multiplier, + 4.4bp spread on entry, 2c extra on stops), and 3x slippage on
  names the lab marks as extended-tier (RESEARCH_RULES rule 1).

## Grid (8 configs, all reported)
G {4%, 6%} x T {10:00, 10:30} x side {long, short}. **Lineage N = 8** (new): full bar max(1.5, sqrt(2 ln 8)) = 2.04,
**BAR90 = 1.84**.

## Controls and reports (no extra configs)
- **C1 failed hold (same names, same day, same T):** event gaps that FAIL the hold test, entered the same side at the same
  bar with the same stop rule. Excess = r - mean r_C1 that day (paired by day).
- **C2 same-minute random name** (adv20 >= $60M, no event that day), same side and stop geometry. Excess r - r_C2.
- Day type (SPY o-c +-0.25%), TRAIN (<= 2025-09-30) / VALID / live window (>= 2026-10-06), walk-forward share, avg R
  without the best day and its share, trades per session, blackout vs non-blackout events, gap bucket 4-6 / 6-10 / > 10%.

## Pass (Testing, BAR90) — all required
day-clustered t >= 1.84 and C2-excess t >= 1.84; TRAIN > 0 and VALID > 0; up-day and down-day avg R > 0 (and quiet
reported); walk-forward positive months >= 54%; avg R w/o best day > 0 (flag best-day share >= 50%).
Live use would also need an owner decision to exempt this one setup from the earnings blackout.
