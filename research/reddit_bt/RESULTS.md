# Reddit/web hypothesis backtests (2026-10-06)

*Educational only — not financial advice.*

**Source caveat.** Reddit post bodies could not be read. Reddit blocks this server, and the fetch and search tools refuse reddit.com. These five families were turned into rules from search snippets, papers and blogs. They are hypotheses, not the posters' exact methods.

**Method.** Harness: `research/reddit_bt/common.py`, with production fills and costs (1c + 1 bps per side, +2c on stops, 3c on extended-tier names), flat by 15:55 and no entries before 09:50.
- Train: 2026-07-15 to 08-25.
- Valid: 08-26 to 09-15.
- Holdouts (Sep 16 – Oct 5, Apr–Jun): untouched.
- Every family was compared against random entries at the same minutes.

**Result: 160 configurations tried, 0 finalists. Nothing goes to the holdouts and nothing changes in live trading.**

| Family | Configs | Best on valid | Verdict |
|---|---|---|---|
| T2 15-min ORB, 5-min close trigger | 32 | -0.049R | As posted, it does exactly as well as random entries (-0.057 vs -0.057R). |
| T3 relative-volume consolidation breakout | 38 | +0.28R (n 17, one day) | 37 of 38 are negative on valid. |
| T4 relative strength vs SPY | 30 | +0.187R, t 1.82 (late window, +1R) | Negative on train in all 30 configs. This is the top rework candidate. |
| T5 inside-bar breakout | 24 | -0.24R | Worse than random. Small stops can't carry the costs. |
| T7 noise-area momentum (faithful) | 36 | QQQ +0.28R (n 4-14) | SPY is negative in all 18 configs. The QQQ results are too small a sample to count. |

All five families are queued for rework (rule 18). Their holdouts are unused, so a reworked version that passes gets look 1 at the normal bar. Per-variant metrics are in `*_results.json`.
