# OBS-UPDAY-NULL — the benchmark every up-day rule must beat (Observer, 2026-11-13 ~23:55 ET)

For the up-day / leveraged-ETF blitz (owner restart 11-13 night). SPY and QQQ RTH minute bars, Alpaca SIP split-adjusted,
2024-11-04..2026-11-13 (509 sessions), fetched after 16:00. Descriptive, 0 configs. Repro: `python upnull.py` -> upnull_out.txt.

1. Base: up days (close > prior close) SPY 55.0%, QQQ 55.4%; close > open 51.9% / 52.7%.
2. Calling the day by the sign of the move so far is already right: SPY 69% at 09:31, 72% at 10:00, 76% at 10:30,
   80% at 11:00, 85% at 12:00, 89% at 14:00 (QQQ 73 / 78 / 80 / 83 / 86 / 91%). Full bucket tables in upnull_out.txt.
3. The tradable part, the return from t to the close, is ~0 in every bucket: 40 cells (2 ETFs x 5 times x 4 buckets),
   all |t| < 2 (largest QQQ 11:00 '<= -0.5%' -13.8bps t -1.94). Days already up > 0.5% by 10:30: SPY +5.3bps (t 0.49),
   QQQ +7.8bps (t 0.83). No continuation (momentum) or reversal in the index after a strong morning, on average.
So: knowing "it is an up day" at time t is mostly having seen the move. A 3x ETF triples a ~0 continuation, minus costs.
How to score any up-day rule (suggested standard):
 (a) hit rate vs the sign-so-far accuracy at the SAME decision time (table 2), not vs the 55% base;
 (b) value = the return AFTER the decision time (table 3 is the null), costs in, gross first;
 (c) for 'switch longs on on up days', score only trades entered after the switch reading, vs random same-share switches.
Up-days are knowable late, not early: the edge, if any, must come from information beyond the index's own path
(breadth, leaders, futures overnight, Hunch), and must beat these two tables.
Educational only — not financial advice.
