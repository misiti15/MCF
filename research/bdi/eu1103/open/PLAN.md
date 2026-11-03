Educational only — not financial advice

# eu1103 / open — pre-declaration (Q2b: earlier starts + the 09:50-09:55 reversal)

Written 2026-11-03 before any two-year scoring in this folder. Live latency (latency.py) was read first; it does not
touch any rule below. Research only: nothing in config/, setups, exits or the live path changes.

## Common harness (fixed)
- Two-year SIP history, lab universe (1,226 names). TRAIN = 2024-10 + 2025-03..12, VALID = 2026-01..03 +
  2026-07-01..09-15 (as ex30 / universe). The rule-19 locked block 2024-11-01..2025-02-28 is never loaded: the 1-minute
  cache is read with a pyarrow filter that drops it at read time, and lab frames only via lib.load_month (asserted).
- Early rows (bar closes 09:35 / 09:40 / 09:45) are rebuilt with the SAME pipeline as the lab frames
  (heat_frame + extra_features + _outcomes_asym on continuous 5-minute RTH bars; outcomes from the entry bar's close,
  exits from the next bar, flat 15:55). Parity: the rebuilt 09:50 rows must equal the lab frame's 09:50 rows.
- Costs: gates.prod_r (1c + 1 bps per side, +2c on stops) with the time-of-day entry multiplier
  (2.1x for bar closes 09:35-09:49, 1.4x 09:50-10:29, 1.0x from 10:30). Sensitivity: the live entry friction
  measured on 12k live fills (night1102: 0.041R) is subtracted as a second line, not as a new config.
- Day type: SPY open-to-close beyond +-0.25% = up / down, else quiet. One trade per symbol-day (first signal).

## Part 2 — window start 09:40 / 09:45 vs 09:50 (8 configs)
Setups (busiest live, logic defined before 09:50; the OR-based CWT14-orl and CWT12-coil cannot fire before 10:05 /
10:20 by construction and are excluded): CWT14-failbrk-pdl-p05-long, CWT14-failbrk-pdh-p10-short,
RW7-gapdn-bounce-early-short-FD, L3-gap-slope-fromopen-FD. Each at window start 09:40 and 09:45 (end unchanged);
the 09:50 start is the baseline (not counted). Live min_adv per setup, adv20 >= $20M floor.
Reported per split: trades/session, avg R, total R/session, day-t; the trades that move earlier (same symbol-day entered
at >= 09:50 in the baseline) and the trades that are new; their avg R.
"Earlier is better" needs: total R per session up vs baseline on TRAIN AND VALID, and the moved+new trades' avg R > 0
on both splits.

## Part 3 — the 09:50-09:55 dip / spike and the opposite swing (8 configs)
m = 09:30-09:50 move = close(09:50 bar) / day open - 1; b = (close(09:55 bar) - close(09:50 bar)) / daily ATR.
Entry at the 09:55 bar close, t1s1 (R = 0.25 x daily ATR), flat 15:55; adv20 >= $95M, price >= $5.
- O1 long: m > 0 and b <= -0.20   (dip inside an up morning, buy the swing back)          PRIMARY
- O2 long: m > 0 and b <= -0.35
- O3 short: m < 0 and b >= +0.20  (spike inside a down morning, sell the swing back)       PRIMARY
- O4 short: m < 0 and b >= +0.35
- O5 long: m < 0 and b <= -0.20   (dip extends a down morning: capitulation reversal)
- O6 short: m > 0 and b >= +0.20  (spike extends an up morning: blow-off reversal)
- O7 = O1 and SPY above its open at the 09:55 close (market filter)
- O8 = O3 and SPY below its open at the 09:55 close (market filter)
Controls: same-time control = every eligible name entered the same side at the same 09:55 close that day;
day-matched random = mean R of every 09:50-15:00 bar of the same symbol-day, same side.
Pass bar (research only; nothing is proposed for live from this study): avg R > 0 on TRAIN and VALID; pooled day-t >=
0.9 x max(1.5, sqrt(2 ln 16)) = 2.12 (BAR90); positive on up AND down days; beats the same-time control on both splits;
avg R without the best day > 0 with the best day < 50% of total R.

## Part 1 — feasibility (no configs)
Live journals (run_id 1, 5 accounts): seconds from 5-minute bar close to signal, signal to fill, spread and slippage by
entry minute. Alpaca historical quotes (SIP NBBO) on a sample of live-traded names: median spread at 09:35..10:30 marks,
to check the 2.1x / 1.4x multipliers before 09:50. Warm-up: what each feature needs before 09:40.

Total pre-declared configurations: 16.
