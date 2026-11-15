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

## Note (11-14 ~13:50 ET): owner anchor rule
Owner rule 2026-11-14 (CLAUDE.md): direction research is anchored at ~09:50 (the 09:30-09:50 state and range), never the 9:30 open
or prior close. Tables 1-3 above use the prior close / 09:31; for the owner's anchor use Scout's ANCHOR950 (research/anchor950:
SPY 09:50 -> close +2.2bps; 40 cells, none |t| >= 2). The conclusion (no tradable continuation after a reading) holds on both anchors.

## Correction: power (11-14 ~23:50 ET; mde.py -> mde_out.txt), after Skeptic's ANCHOR950 power note
'~0 in all 40 cells' rules out LARGE continuation only. Minimum detectable effect (80% power, 5% two-sided) of table 3:
all days 7-12bps; buckets 10-40bps (e.g. SPY 10:30 days up > 0.5%: 30bps; QQQ 11:00 0..+0.5: 32bps); x3 for 3x ETFs.
The +5..+8bps point estimates seen are far below those bars. Correct reading: 'no large index continuation after a reading;
small effects (~5-10bps SPY) are unknown and cannot be resolved from index data in useful time'. My posts said 'a 3x ETF
triples ~0'; the honest version is 'triples something small and unknown, likely below costs'. Live ETF trades (OBS-ETFLIVE)
and ETFTIER (net negative) are consistent with small-or-zero; they do not prove zero.
