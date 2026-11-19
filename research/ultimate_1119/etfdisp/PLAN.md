# ETF late dip after high-dispersion days (ETFDISP): build plan, written before scoring (2026-11-19)

*Educational only — not financial advice. Owner decision (2026-11-19 ~07:50 ET): "Added to testing as a new setup for
live sessions. We have the slots available currently." This is a build, not a research pass: deployment is the
owner's, whatever the scores. Nothing here takes effect intraday; earliest effective session 2026-11-20, merged only
after the 16:00 ET close by the Deploy stage.*

## The setup (frozen, no tuning)
- **Leg E of ULT-32, exactly as frozen in round5/frozen/book_module__ULT-32.py**: WB4 ETF list (124), ADV20 >= $95M,
  bar close 14:00-15:00, ret3 <= -0.75%, di_diff7 >= -5, ret12 >= -1.0%, daily ATR >= 3.5967583179473883% of price,
  cost_r <= 0.10, price >= $10, |gap| < 20%, skip while SPY is -0.30..-0.75% from its open and falling over 30 min
  (`context: [spy_fo]`), thin = max 2 per symbol-session, the 2nd >= 6 decision bars after the 1st. Exit t05s1
  (+0.5R / -1R, R = 0.25 x daily ATR) with the frozen 45-minute time cap (YAML `time_stop_min: 45`,
  `time_stop_min_r: 99`).
- **+ the round-6 dispersion gate**: trade only when `disp_prev >= DISP_MIN`.
  `disp_prev` = cross-sectional standard deviation (ddof 1, in %) of the PRIOR session's close-to-close returns
  (each clipped to +-50%) over every universe name whose ADV20 through the prior session is >= $95M; NaN (= no trade,
  fail safe) when fewer than 100 names qualify. Same definition as round6/gates.py `disp`.

## Threshold rule (declared now, before any score of this setup)
**DISP_MIN = the median of the three round-6 rotation thresholds** (round6/gates.json, BOOK-EM, disp, keep high):
3.1274 (W1 held out), 2.5790 (W2 held out), 2.6438 (W3 held out) -> **DISP_MIN = 2.6438%**. Never tuned further.
Honest caveat, stated now: each rotation threshold was chosen on two of the three windows, so the frozen value has
seen all three windows; the backtests below are in-sample for the gate. Only live forward sessions are out-of-sample.

## Live data path (before the open)
- `mcf.data.priors` already pulls ~30 daily bars per universe name before the open; it now also records `prev_ret`
  (the prior session's close / the close before it - 1).
- `mcf.strategies.lab_context`: new opt-in daily market column `disp_prev` (by name only), computed once per session
  from the universe priors (runner) or the per-symbol daily history (backtester); carried to `add_context` inside
  `index_priors` under the reserved key `__market__` (the channel every live / replay / backtest path already passes).
- Universe parity: the live liquid set (ADV >= $95M, 1,204 names in data/universe.csv) is inside the history2y symbol
  list (1,203 of 1,204), so the live value and the history value use the same names.

## Scoring ("normal filter way", research/ultimate_1119/top10/bench10.py engine, unchanged)
Booked as a testing-arena setup (cap 100, 0.15R cost filter, no latch, <= 3 lots per symbol). T1 fit / check /
combined, T2 (2023-01-03..2024-09-13, cache_fresh; coverage reported), T3 replay where it exists. Compared with the
top-10 standard (top10/PLAN.md Tier A thresholds) and with the ungated leg E on the same engine. Note: the bench10
walk has no 45-minute cap; the setup is scored both with the cap (as it will run) and without (engine as is), both
reported. Configs counted: 1 frozen setup scored (+1 ungated reference, not a candidate). Locked block
2024-11-01..2025-02-28 never read.
