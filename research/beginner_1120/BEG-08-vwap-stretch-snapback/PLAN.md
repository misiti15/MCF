Educational only — not financial advice

# BEG-08 Stretched-from-VWAP snap-back: pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg08.py`, DESIGN.md B08 implemented as written. Plainest readings are marked [R] in the module docstring:
  - price >= $20 on the prior close, ADV20 >= $100M point-in-time, rank_rvol20 > 30 (BEG-02 day table, read only;
    a day with no rank is not traded);
  - 5-minute RSI(14) = Wilder RSI on 5-minute RTH closes, continuous from the prior session(s) (restarts after a
    > 5-calendar-day gap, i.e. after the locked block); the value at a 1-minute bar is the last completed 5-minute bar;
  - setup active at bar i: (short) close - VWAP >= 0.8 x ATR and RSI5 > 80; (long) VWAP - close >= 0.8 x ATR and
    RSI5 < 20; ATR = daily ATR(14) at the prior close;
  - trigger on the close of bar k (10:00..14:29) with the setup active at bar k-1: short close_k < low_{k-1}, long
    close_k > high_{k-1}; fill at the next bar's open;
  - stop = extreme from the start of the current setup run through bar k, +/- 0.05 x ATR;
  - target = VWAP at bar k; skip if it is < 1.0R from the decision close (a later trigger may still trade);
  - one open position per symbol at a time; re-entry allowed after the exit;
  - time stop: the open of the first bar >= 45 min after the entry bar;
  - shorts: ETB only (bench10 E90 proxy) and never an inverse / volatility fund.
- Engine: `run.py`. Costs, book and `stats()` imported unchanged from `research/ultimate_1119/top10/bench10.py`: LR8
  costs (+1.2 bp borrow on shorts), stop first (gap-through at the worse of open/stop), target only when traded through
  by $0.01, testing-arena book (TESTING_RULES: cap 100, <= 3 lots/symbol, price >= $5, stop-cost filter 0.15R).

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30. CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the
  FIT-picked tweak. T2 = 2023-01-03..2024-09-13 (seen data, reference only). The locked block 2024-11-01..2025-02-28
  is never read.

## Controls (fit nothing)
- `same`: the setup's booked symbol-days and sides, a random decision bar in 10:00..14:29, the same $ stop distance,
  target VWAP at that bar when on the profit side (no 1R test), 45-min time stop. 2 seeds.
- `univ`: every universe day, a random decision bar, side = fade of the close vs VWAP, stop = the setup's median
  stop/ATR on that test x ATR, target VWAP, 45-min time stop, no setup / trigger / 1R test. 2 seeds.

## Tweaks (step 3)
- At most 3 one-part tweaks chosen after a FIT-only diagnosis of the base's worst losers, written below before they
  are scored. Pick = best FIT avg R with >= 20 booked FIT trades (ties: higher FIT avg R w/o best day). The pick is
  scored once on CHECK and on T2.

## Verdict (research/ultimate_1119/top10/PLAN.md, testing-arena book)
- MEETS: every Tier A leg holds (T1 combined avg R >= -0.0383; T1 check >= -0.0464; avg R w/o best day >= -0.0674 /
  -0.0781; total R/session >= -0.4862 / -0.5218; T2 avg R >= -0.1048; >= 20 trades on check and T2).
- NEAR: not MEETS, but each failing avg-R leg is within 0.02R of its threshold (R/session legs judged the same way).
- FAIL: everything else. REALLY BAD reported as defined there.
- Configurations: base 1, controls 0 fitted, tweaks <= 3.

## Tweaks (pre-registered 2026-11-20, after the FIT-only diagnosis and before any tweak was scored)
FIT diagnosis of the base (1,570 booked of 3,860 raw, avg R −0.076, gross +0.004, avg R w/o best day −0.180):
- One day decides FIT: 2025-04-09 (the tariff-pause rally, from ~13:18) gave **−238.6R from 368 shorts** at the 100-lot
  cap. 2025-04-04 (crash day) gave +138.9R. Without the 5 worst days the rest averages +0.167. The setup fires on
  hundreds of names at once on market-wide trend days.
- Exits: 913 stops −1,010R, 124 targets +346R (only 8% reach VWAP), 533 45-min time exits +545R (+1.02 each).
- The 30 worst losers are all full stops (−1.2..−2.6R incl. gap-through); 13 of them are 2025-04-09 shorts.
- Entry timing: a setup run that started 1-3 bars before the trigger: +0.10 (607); 4-30 bars: −0.21 (879). A stale,
  grinding stretch keeps going.
- Target: the planned target is > 5R away on 633 trades (−0.17 avg); most never get there and leave at the time stop.
- Stop: stops are hit on 58% of trades within a median 21-min hold; no stop-size bucket is clean.
- Tried and not chosen: a SPY-tape filter (trades in the SPY-stretch direction −0.21 vs against +0.05, the wrong way
  round for a filter) and a SPY RSI5 filter (keeping SPY RSI5 < 70: −0.12, worse than base). The window split
  (13:00-14:30 −0.30) is the 04-09 day itself (+0.24 without the 5 worst days), so no window tweak.

The three one-part tweaks:
- **T1 `fresh3`** (entry timing): trigger only if the setup run started at most 3 bars before the trigger bar
  (k − run start <= 3).
- **T2 `tgthalf`** (target): target = halfway from the decision close to VWAP (the 1.0R skip test stays on the full
  VWAP distance, so the trade set is unchanged; only the exit moves).
- **T3 `stop125`** (stop): stop distance x1.25.
Pick = best FIT avg R with >= 20 booked FIT trades (ties: higher FIT avg R w/o best day); scored once on CHECK and T2.
Configurations: 1 base + 3 = 4.
