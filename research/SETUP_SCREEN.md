# Setup screen — 2026-10-06

*Educational only — not financial advice.*

SIP 1-minute bars, 1,226 most liquid symbols, 63 sessions (2026-07-08 to 2026-10-05). Each setup on its own book.
Conservative fills: market entries at the next bar's open, stop entries at max(open, trigger), stop first inside a bar,
gaps through stops fill at the open, 1c + 1 bps slippage per side plus 2c extra on stops (3c on extended-tier names).
R results are after those costs. Only entries at or after 09:50 count; pre-09:50 entries are shown separately.

**Paper screen** (decides what paper-trades, not what reaches funds): at least 30 trades, expectancy > 0R, profit factor > 1,
and still positive without the best day.

| Setup | Trades | /day | Success | Win rate | Exp R | PF | Exp R ex best day | Green days | Pre-09:50 trades | Pre-09:50 exp R | Screen |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gap_and_go | 27 | 0.43 | 0.333 | 0.63 | 0.215 | 3.39 | 0.145 | 0.619 | 238.0 | 0.011 | fail |
| orb20_a | 443 | 7.03 | 0.35 | 0.454 | 0.021 | 1.11 | 0.006 | 0.476 | 0.0 | – | pass |
| intraday_momentum | 174 | 2.76 | 0.057 | 0.408 | 0.013 | 1.0 | -0.021 | 0.397 | 0.0 | – | fail |
| vwap_pullback | 207 | 3.29 | 0.478 | 0.444 | -0.017 | 0.88 | -0.047 | 0.459 | 0.0 | – | fail |
| close_momentum | 60 | 0.95 | 0.017 | 0.35 | -0.048 | 0.53 | -0.066 | 0.359 | 0.0 | – | fail |
| eod_reversal | 11465 | 181.98 | 0.038 | 0.403 | -0.08 | 0.56 | -0.101 | 0.254 | 0.0 | – | fail |
| gap_sma20 | 1914 | 30.38 | 0.275 | 0.398 | -0.129 | 0.8 | -0.156 | 0.317 | 0.0 | – | fail |
| index_gap_fill | 43 | 0.68 | 0.14 | 0.419 | -0.152 | 0.51 | -0.192 | 0.355 | 0.0 | – | fail |
| vwap_reclaim | 1674 | 26.57 | 0.427 | 0.458 | -0.172 | 0.75 | -0.178 | 0.317 | 0.0 | – | fail |
| orb20_b | 443 | 7.03 | 0.467 | 0.181 | -0.206 | 0.78 | -0.255 | 0.349 | 0.0 | – | fail |
| vwap_reversion | 31475 | 499.6 | 0.444 | 0.454 | -0.267 | 0.72 | -0.267 | 0.079 | 0.0 | – | fail |
| gap_continuation | 91 | 1.44 | 0.319 | 0.341 | -0.298 | 0.6 | -0.325 | 0.35 | 0.0 | – | fail |
| orb | 200 | 3.17 | 0.365 | 0.375 | -0.326 | 0.56 | -0.36 | 0.258 | 713.0 | -0.593 | fail |
| noise_band_momentum | 60 | 0.95 | 0.3 | 0.333 | -0.491 | 0.64 | -0.574 | 0.216 | 0.0 | – | fail |

## What this means
- One setup passes: **orb20_a**, the 20-minute stocks-in-play breakout with a 0.5-range stop and a 0.75-range target. The edge is thin (+0.021R, PF 1.11) and it was negative in September and October. It paper-trades to gather live evidence.
- The setups enabled until now lose after realistic costs: 5-minute ORB −0.33R (its pre-09:50 entries −0.59R, consistent with the tick-level replication rather than the paper's headline), simplified noise-band −0.49R. Both are now off for paper.
- intraday_momentum is break-even (+0.013R) on index ETFs. It stays on for data because it is cheap and uncorrelated.
- The most popular retail setups (VWAP reversion, VWAP reclaim, gap continuation, end-of-day reversal) lose after costs over this window. This matches the research synthesis: setups with a high win rate rarely have net positive expectancy.
- gap_and_go after 09:50 was +0.22R on only 27 trades. It is a watch item and fails the screen's minimum sample.
- Limits: 63 sessions is one regime (Jul–Oct 2026), the largest names only, and no earnings calendar. A pass here is permission to collect paper evidence, not proof of an edge.
