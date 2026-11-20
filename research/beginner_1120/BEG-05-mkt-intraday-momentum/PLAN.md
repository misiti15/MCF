Educational only — not financial advice

# BEG-05 Market intraday momentum (last 25 min): pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg05.py`, DESIGN.md B05 implemented as written. Plainest readings (module docstring [R]):
  - "price at 10:00" = the close of the 09:59 bar (the end of the first half hour, as in Gao et al. 2018);
  - VWAP = session typical-price VWAP from 09:30, evaluated through the 15:29 bar;
  - entry = market at the 15:30 bar open (signal on the 15:29 close; global "next bar open" convention);
  - stop = fill -/+ 0.15 x ATR (daily ATR(14) as of the prior close); no target; time exit at the 15:55 bar open
    (the engine's flat time). One trade per symbol per day, at most 4 per day.
- Engine: `run.py`, 1-minute bars (the setup is defined on them), with bench10's cost function (`add_r`: LR8 + 1.2 bp
  borrow on shorts), book (`book` with TESTING_RULES: cap 100, <= 3 lots/symbol, price >= $5, ETB >= 90%, 0.15R
  stop-cost filter) and `stats` imported unchanged from `research/ultimate_1119/top10/bench10.py`.
  - Expected issue noted in advance: 0.15 x ATR is a tight $ stop on $400-$600 ETFs, so the 0.15R stop-cost filter
    ((2 x (1c + 1 bp) + 2c) / risk) may remove many trades, and costs alone are ~0.1-0.15R per trade. Both are part of
    the normal way and are reported, not waived.
- Daily context: T1 prev close (= 09:30 open / (1 + gap)) and ATR (`atr_d`) from the lab frames (point in time, so the
  locked block is never read); T2 from `data/cache_fresh` 1-minute bars (RTH daily OHLC, `mcf.features.atr`, shift 1).

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30. CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the
  FIT-picked tweak. T2 = 2023-01-03..2024-09-13 (seen data; reference only). Locked 2024-11-01..2025-02-28 never read.

## Control
- Random side: on the same symbol-days the setup trades, same entry, same stop distance, same exit, side drawn by a
  fair coin; 200 seeds. Reported as the mean avg R of the seeds and the setup's percentile among them.
- Also reported (information): the "no VWAP filter" and "always trade both sides" readings are NOT run as separate
  configs unless pre-registered as a tweak below.

## Verdict
- research/ultimate_1119/top10/PLAN.md Tier A thresholds on T1 combined / T1 check / T2 (avg R, avg R w/o best day,
  total R / session, >= 20 trades on check and T2). MEETS = all hold; NEAR = every failed avg-R / w/o-best-day /
  total-R/session threshold missed by <= 0.02R; else FAIL. REALLY BAD rule reported.

## Tweaks
- At most 3 one-part tweaks, chosen from a FIT-only diagnosis of the base's worst losers, appended below BEFORE they
  are scored. The best on FIT (avg R, tie -> w/o best day) is scored once on CHECK. Config count = 1 + number of tweaks.

## Tweaks: pre-registered 2026-11-20 after the FIT diagnosis (`diag.py`), BEFORE any tweak was scored
FIT base: 137 booked trades, avg R −0.307 (gross −0.204, costs 0.104R/trade), 38 stop-outs carry −42.7R of −42.1R;
shorts −0.595 (64) vs longs −0.055 (73); setup below 99% of random-side seeds (random mean −0.173).
Diagnosis (raw signals, no cost filter): held to 15:55 without a stop the direction is worth ~0 (+0.004R gross, +0.0006
ATR); the 0.15 x ATR stop costs ~0.07R gross (median adverse excursion 0.077 ATR, 25% of signals go 0.147 ATR against);
signals whose 10:00 -> 15:29 move disagrees with the side lose most (−0.259 vs −0.027 gross); the losers are shorts in
the 2025-03..05 sell-off/rebound, squeezed into the close.
One-part tweaks (config count 1 + 3 = 4):
1. `stop2x` (stop): stop 0.30 x ATR instead of 0.15 (fewer noise stop-outs, half the cost in R, more trades pass the
   0.15R cost filter).
2. `agree` (filter): trade only if the 10:00 -> 15:29 move agrees with the side by >= 0.01% (side x r2 >= 0.01%).
3. `longonly` (filter): drop the short side.
Pick: best FIT avg R (tie -> avg R w/o best day); scored once on CHECK and on T2 (reference).
