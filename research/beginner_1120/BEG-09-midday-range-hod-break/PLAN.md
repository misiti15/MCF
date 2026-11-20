Educational only — not financial advice

# BEG-09 Midday range -> high/low-of-day break: pre-registered plan (written 2026-11-20 before any scoring)

Research only. No setup, exit, config, account or ledger change.

## What is scored
- Setup: `beg09.py`, DESIGN.md B09 implemented as written. Where the spec is ambiguous, the module docstring marks the
  plainest reading with [R]. The main readings:
  - price >= $10 is checked on the prior close; U0 = prior close >= $5 and ADV20 >= $20M;
  - "day return at 11:30" = the close of the 11:29 bar vs the prior close; this fixes the side for the day;
  - the consolidation is the FIRST run of 30 consecutive 1-minute bars (contiguous timestamps), all starting inside
    11:30..14:29, whose high-low range is <= 0.35 x ATR(14 daily, prior close) and whose every close is above session
    VWAP (short: below). "At least 30" is met by the first 30-bar window; it is not extended;
  - the stop order is armed from the bar after the window completes, at the day's high so far + $0.01 (short: day's
    low - $0.01), and works until the 14:59 bar (valid until 15:00). It is not cancelled if price leaves the range;
  - fill = max(bar open, trigger) for a buy-stop (min for a sell-stop); one trade per symbol-day;
  - stop = consolidation low - $0.02 (short: high + $0.02); target = trigger + 2 x (trigger - stop) (2R on the order
    price); the booked R uses the real fill. Flat at the 15:55 open;
  - the stop is checked first, including on the fill bar (conservative, as BEG-03).
- Engine: `run.py`, following the bench10 "normal way" (as BEG-02/03):
  - LR8 costs (entry (1c + 1 bp) x time-of-day multiplier; exit 1c + 1 bp except target limit fills; +2c on stops;
    x3 extended tier), plus 1.2 bp borrow on shorts;
  - a target fills only when traded through by $0.01; gap-through stops fill at the worse of open/stop;
  - the testing-arena book (TESTING_RULES): cap 100, <= 3 lots per symbol, price >= $5, ETB >= 90% for shorts,
    stop-cost filter 0.15R;
  - the same `stats()`: avg R, avg R w/o best day, best-day share, total R/session, day-clustered t, SPY day types.
- rank_rvol20 is reused unchanged from the BEG-02 day tables (session scratchpad `beg02w/days_t1|t2.parquet`, built by
  BEG-02 `run.py`): 09:30-09:49 volume / mean of the prior 14 sessions (min 5), ranked among the day's U0 names.
  T1 context (ATR, ADV20, prev close) is from the lab frames, point in time. T2 ranks among the 469 cache_fresh
  symbols (top-30 is a wider cut there); T2 is reference only.

## Windows
- FIT = 2024-10 + 2025-03-01..2025-09-30.
- CHECK = 2025-10-01..2026-11-04, scored once for the base and once for the fit-picked tweak.
- T2 = 2023-01-03..2024-09-13 (seen before; reference only).
- The locked block 2024-11-01..2025-02-28 is never read.

## Control
- Random entries on the same symbol-days, same side, same $ stop distance and 2R target as each setup trade; entry
  at the open of a bar drawn uniformly from 12:00..14:59 (the earliest a 30-bar window can arm is 12:00); same exits.
  5 seeds, booked the same way.

## Tweaks (step 3)
- At most 3 one-part tweaks, chosen after diagnosing the base's worst FIT losers, using FIT only, written into this
  file (section "Tweaks") before they are scored.
- Pick = best FIT avg R with >= 20 booked FIT trades. Scored once on CHECK and once on T2.

## Verdict (research/ultimate_1119/top10/PLAN.md, testing-arena book)
- MEETS: all Tier A legs hold (T1 combined avg R >= -0.0383; T1 check >= -0.0464; w/o best day >= -0.0674 / -0.0781;
  total R/session >= -0.4862 / -0.5218; T2 avg R >= -0.1048; >= 20 trades on check and on T2).
- NEAR: not MEETS, but each failing avg-R leg is within 0.02R of its threshold.
- FAIL: everything else. REALLY BAD reported as defined there.
- Configurations: base = 1, random control = 0 fitted, tweaks <= 3.

## Tweaks (pre-registered 2026-11-20, after the FIT-only diagnosis in diag.py and before any tweak was scored)
FIT diagnosis of the base (481 booked trades, avg R −0.024, gross +0.030, total −11.6R):
- **Stop-outs carry the loss.** 163 stops = −176.1R; 266 time exits at 15:55 = +62.3R (avg +0.23); 52 targets =
  +102.2R. All 40 worst trades are stop-outs (median hold 54 min, median risk 0.31 x ATR, median cost 0.12R).
- **Tight stops are worst.** Risk < 0.3 x ATR: 150 trades, −22.8R (avg −0.15); 0.3-0.5 x ATR: −0.0; > 0.5 x ATR:
  +0.14. Cost per trade falls from 0.07-0.08R to 0.04R as the stop widens.
- **Early windows are worst.** Windows that complete 11:59-12:15 (the first possible): 318 trades, −28.8R (avg −0.09);
  windows completing after 12:15: 163 trades, +17.2R.
- Time exits are positive, and only 11% of trades reach 2R, so the target cap may cut the "trend into the close".

The three one-part tweaks:
- **T1 `stopx15`** (stop part): the stop distance (trigger - consolidation low + $0.02) x 1.5. The 2R target scales with it.
- **T2 `win1200`** (window part): the consolidation window must start at 12:00 or later (11:30 -> 12:00; still ends
  by 14:29; order still valid until 15:00).
- **T3 `notgt`** (target part): no 2R target; hold to the 15:55 exit (stop unchanged).

Pick = best FIT avg R with >= 20 booked FIT trades; scored once on CHECK and once on T2. Configurations: 1 base +
3 tweaks = 4.

Control note (added before any tweak was scored): the pre-registered random control is look-ahead biased. It enters at
a random bar from 12:00 on a symbol-day that is known to break the HOD later, so it can buy before a known breakout
(it scored +0.13..+0.19 avg R on T1). A second control is added as the fair one (0 fitted configs). It uses every
ARMED symbol-day (filled or not), the same side, the same $ stop distance and the same 2R target, with entry at the
open of a bar drawn uniformly from the arming bar + 1 through 14:59. Both controls are reported.
