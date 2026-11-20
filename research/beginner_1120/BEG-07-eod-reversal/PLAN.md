Educational only — not financial advice

# BEG-07 End-of-day reversal — pre-registered plan (written 2026-11-20 before any score)

## Setup (DESIGN.md B07, implemented as written in `beg07.py`)
Universe U0 + price >= $10 (15:24 close), ADV20 >= $30M (prior close), stocks only (assets_meta is_etf + study extras
removed). One universe pass on the 15:24 bar close: r = close / prev_close - 1. Long the 10 lowest r with r <= -3% and
close > day low + 0.1 ATR; short the 10 highest r with r >= +3% and close < day high - 0.1 ATR, ETB (>= 0.9 of
snapshots) only. Entry at the 15:25 bar open. Stop 0.20 x daily ATR(14) from the fill. Time exit at the 15:55 open.

Plainest readings chosen: pin and ETB filters apply before the top-10 ranking; day high/low = RTH 09:30..15:24; entry at
the next bar open (DESIGN convention) rather than the decision-bar close; missing 15:24 bar -> last close before it.

## Engine (the "normal way")
bench10.py add_r (LR8 costs, x tod multiplier, +2c on stops, 1.2 bp borrow on shorts) + book(TESTING_RULES: cap 100,
3 lots/symbol, price >= $5, ETB, 0.15R stop-cost filter, no latch) + stats (avg R, w/o best day + share, day-clustered
t, SPY day type). Universe: the lab symbols in data/cache_hist (T1) and data/cache_fresh (T2), ETFs removed.

## Tests
- FIT = 2024-10 + 2025-03-01..2025-09-30. CHECK = 2025-10-01..2026-11-04, scored ONCE for the base and ONCE for the
  fit-picked tweak. T2 = 2023-01-03..2024-09-13 (seen data, reference only). Locked 2024-11-01..2025-02-28 never read.
- Random-entry controls (100 draws each): random side on the same picks; random eligible names with the same count
  per day and side.
- Verdict vs research/ultimate_1119/top10/PLAN.md Tier A thresholds (testing-rules book): T1 combined avg R >= −0.0383,
  check >= −0.0464; w/o best day >= −0.0674 / −0.0781; R/session >= −0.4862 / −0.5218; T2 avg R >= −0.1048; >= 20
  trades on check and T2. MEETS = all hold; NEAR = every failed avg-R threshold missed by <= 0.02R (other legs hold);
  else FAIL. REALLY BAD flag per that PLAN.

## Tweaks
At most 3 one-part tweaks, chosen from the FIT diagnosis of the base's worst losers only, appended below before they are
scored. Pick = best FIT avg R (ties: higher w/o-best-day). Only the pick is scored on CHECK, once.
Configurations counted: base (1) + tweaks (<= 3).

## Tweaks pre-registered 2026-11-20 after the FIT diagnosis (diag.py), before any tweak was scored
Base FIT: 2,223 trades, avg R −0.088 (gross −0.025), t −4.65. Diagnosis (FIT only):
- the worst 10% of trades are 100% stop-outs (avg −1.13R); 23% of trades stop out, median 18 min after entry, while time
  exits average +0.22R. The 0.20 ATR stop over the last 30 minutes is the main loss source (stop part);
- the most extreme movers (|r| > 10%) are the worst bucket on both sides (−0.18 / −0.10R, stop rate ~35%): news-day
  movers continue rather than revert (filter part);
- low-volatility names (daily ATR < 4% of price) are the worst ATR buckets (−0.15..−0.17R), where 0.20 ATR is only a few
  ticks of last-half-hour noise (filter part).
| id | one part changed | params |
|---|---|---|
| stop30 | stop 0.20 -> 0.30 x ATR (x1.5) | stop_atr 0.30 |
| rcap10 | filter: skip |r| > 10% | max_r 10 |
| atr4 | filter: daily ATR >= 4% of prev close | min_atr_pct 4 |
Configurations counted: 4 (base + 3).
