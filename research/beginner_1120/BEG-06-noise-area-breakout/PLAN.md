Educational only — not financial advice

# BEG-06 Noise-area breakout on index ETFs: pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg06.py`, the BEG-06 spec implemented as written. Plainest readings (module docstring [R]):
  - m_t = average |close/open − 1| at the same minute of session over the last 14 prior sessions, built exactly as the
    live priors build (`mcf/data/priors.py::_move_profile`: sessions fetched within 24 calendar days, >= 5 needed).
  - Bounds: upper = max(open, prev_close) × (1 + m_t), lower = min(open, prev_close) × (1 − m_t). The spec's gap clause
    is a no-op if read literally (on a gap-up day max(open, pc) is the open); the cited paper and MCF's
    noise_band_momentum anchor both bounds this way on every day, so that reading is used.
  - Checks = the close of the 09:59, 10:29, ..., 14:59 bars (10:00 ... 15:00, 11 checks). Entry = next bar's open.
  - One position at a time per symbol; after an exit, re-entry only at a later check; no reversal at the same check.
  - Hard stop fill ∓ 0.25 × ATR (daily ATR(14) as of the prior close), intrabar, stop first; 1R = 0.25 × ATR.
    Trailing exit at a check: long if close < max(upper, VWAP), short if close > min(lower, VWAP); fill next bar open.
    Otherwise the 15:55 bar open.
- Engine: `run.py`, 1-minute bars, with bench10's `add_r` (LR8 + 1.2 bp borrow on shorts), `book` (TESTING_RULES:
  cap 100, <= 3 lots/symbol, price >= $5, ETB >= 90%, 0.15R stop-cost filter) and `stats` imported unchanged from
  `research/ultimate_1119/top10/bench10.py`. Trailing exits are costed as market exits (1c + 1 bp, no stop surcharge).
- Daily context: T1 prev close (= open / (1 + gap)) and ATR (`atr_d`) from the lab frames; T2 from `data/cache_fresh`.
- Known gap, stated in advance: T1 sessions in early March 2025 have fewer than 5 prior non-locked sessions within 24
  days, so they get no m_t profile and no trade (the locked block is never read to fill them).

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30. CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the
  FIT-picked tweak. T2 = 2023-01-03..2024-09-13 (seen data; reference only). Locked 2024-11-01..2025-02-28 never read.

## Control
- Random side: the setup's own entries (same bar, same fill, same stop distance), side from a fair coin, held to the
  setup's exit time unless the flipped side's hard stop hits first; 200 seeds. Reported as the mean and the setup's
  percentile.

## Verdict
- research/ultimate_1119/top10/PLAN.md Tier A thresholds: T1 combined avg R >= −0.0383, T1 check >= −0.0464; w/o best
  day >= −0.0674 / −0.0781; total R/session >= −0.4862 / −0.5218; T2 avg R >= −0.1048; >= 20 trades on check and T2.
  MEETS = all hold; NEAR = every failed threshold missed by <= 0.02R; else FAIL. The REALLY BAD rule is reported.

## Tweaks
- At most 3 one-part tweaks, chosen from a FIT-only diagnosis of the base's worst losers, appended below BEFORE they
  are scored. Best on FIT (avg R; tie -> w/o best day) is scored once on CHECK and on T2. Config count = 1 + tweaks.

## Tweaks: pre-registered 2026-11-20 after the FIT diagnosis (`diag.py`), BEFORE any tweak was scored
FIT base: 265 booked trades, avg R −0.095 (gross +0.011, costs 0.106R/trade), t −0.99; random-side mean −0.121 (setup
at the 69th percentile). Exits by kind: 15:55 time exits 83 at +0.945R, hard stops 63 at −1.136R (−71.6R), check-time
trailing exits 119 at −0.270R (−32.1R). Shorts −0.298 (124) vs longs +0.083 (141).
Diagnosis (gross R, FIT trades only):
- Exits leak most. Held to 15:55 with no stops at all the same entries are worth +0.227R gross against the setup's
  +0.011. The trailing exits average −0.175R gross, but held they would be +0.080R (53% end on the right side): the
  trail exits on noise around VWAP / the band. Hard stop only (no trail) = +0.073R gross.
- Hard stop: 63 stops; held, they would average −0.571R and only 29% end on the right side, so most stops are right.
  MAE median 0.21 ATR (25% of trades go > 0.46 ATR against). A wider hard stop alone (x1.25, no trail) = +0.050R.
- Entry timing: the 10:00 check is the worst bucket (72 trades, −0.166R, −12.0R); the first entry of a symbol-day
  loses (−0.184, 171) while second/third entries are positive. The worst 15 losers are mostly 10:00 shorts in
  2025-07..09 (a rising market) stopped out within minutes.
One-part tweaks (config count 1 + 3 = 4):
1. `notrail` (exit): drop the check-time trailing exit; exits are the 0.25 × ATR hard stop or 15:55.
2. `stop125` (stop): hard stop 0.3125 × ATR (x1.25) instead of 0.25; trailing exit unchanged.
3. `late1030` (window): first check 10:30 instead of 10:00 (checks 10:30 ... 15:00) for entries and trailing exits.
Pick: best FIT avg R (tie -> avg R w/o best day); scored once on CHECK and on T2 (reference).
