Educational only — not financial advice

# eu1103 / edge — pre-declaration for the two 2-year tests (written before any 2-year scoring)

Q1 decomposition (live, `decompose.py`, `extra.py`) ran first and motivates these two tests:
the profitable live setups' R is ~88% SPY-beta (short beta in a falling window), and the book's largest loss line is the
stock's own (idiosyncratic) day drift against our side (-1,327R of -1,695R), i.e. we fade names that keep trending,
while short-term entry timing adds +567R. Both tests are therefore **beta-hedged and cross-sectional**, built on one idea
from the literature (volume-conditioned returns: Campbell, Grossman & Wang 1993; Llorente, Michaely, Saar & Wang 2002):
an extreme move on NORMAL volume is a liquidity shock that reverts; an extreme move on HEAVY volume carries information
and continues.

## Common harness (fixed)
- Data: SIP 1-minute RTH bars `data/cache_hist/1Min` (lab universe, 1,226 names), read with a pyarrow filter that drops
  2024-11-01..2025-02-28 at read time (the locked block is never loaded; asserted in code).
- TRAIN = 2024-09-16..2024-10-31 + 2025-03-01..2025-12-31; VALID = 2026-01-01..2026-10-05 (the live window is excluded).
- Eligible name-day: prior close >= $5, prior-20-day ADV >= $20M, ATR14 >= 1% of price (prior days only).
- Signal at decision time t (bar close): idio = (P_t / open - 1) - beta x (SPY_t / SPY_open - 1); z = idio / ATR14%.
  beta = prior-20-session 5-minute-return beta vs SPY (10:00-15:55), shrunk 0.7 b + 0.3, clipped 0..3.
  RVOL = volume 09:30..t / mean of the same window over the prior 14 sessions.
- Entry: open of the next 1-minute bar. Stop 0.5 x ATR14 from entry (stop-first in a bar, a gap through fills at the
  open). R unit = 0.5 x ATR14 (the stop distance). Exit at the pre-declared time at that bar's open.
- Costs (production): entry 1c + 1 bps x time-of-day multiplier (gates.TOD_COST: 3.8 before 09:35, 2.1 to 09:50, 1.4 to
  10:30), exit 1c + 1 bps, +2c on stop fills. Hedge leg (SPY, beta x notional, opened and closed with the stock leg):
  1c + 1 bps per side on SPY notional.
- Selection per day: the 10 eligible names with the largest |z| (|z| >= 0.5) inside the test's RVOL bucket.
- Baseline (rule 6): same day, same t, same side, all OTHER eligible names in the same RVOL bucket (day-matched random entry).
- Reported: n, sessions, avg R, day-clustered t, avg R w/o best day and its share, up / flat / down (lib.regimes), walk-forward
  share of positive months, vs-baseline difference and its t.

## Test A — "quiet extreme" reversal (fade)
Bucket RVOL < 1.5 (normal volume). Side = -sign(z) (fade). Primary: t = 09:50, exit 10:30, SPY-hedged.
Grid: t in {09:40, 09:45, 09:50} x exit {10:30, 15:55} x hedge {none, SPY} = 12 configs.

## Test B — "in play" continuation (ride)
Bucket RVOL >= 3. Side = +sign(z) (ride). Primary: t = 09:45, exit 15:55, SPY-hedged.
Grid: t in {09:40, 09:45, 09:50} x exit {10:30, 15:55} x hedge {none, SPY} = 12 configs.

Total 24 configurations. Bar (pre-declared, research only, nothing is proposed for live from this): a primary is a
candidate for the backlog only if TRAIN and VALID avg R > 0, VALID day-clustered t >= max(1.5, sqrt(2 ln 24)) = 2.52,
it beats its baseline in both splits, avg R w/o best day > 0, and up and down regimes are both > 0. Neighbours are reported
as the plateau check. The locked block is not scored here (the lead scores a finalist once, if any).
