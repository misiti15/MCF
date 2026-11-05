# reddit_1104 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Common rules (docs/RESEARCH_RULES.md), as reddit_1103: costs in (1c + 1 bp per side; entry side x
`gates.tod_cost_mult`, exit side free on a target limit, +2c on stop fills); next-bar-open entries; stop first when a
bar touches stop and target; locked block 2024-11-01..2025-02-28 never read (1-minute rows and daily rows dropped at
load, before any computation); old holdouts 2026-04..06 and >= 2026-09-16 dropped; earnings blackout
(`GD._blackout`) removed; one trade per symbol-day; day-clustered t; regime gate `gates.session_regimes` (up and down
both > 0); WF = share of months > 0 (>= 54%); TRAIN <= 2025-08-31 / VALID after; avg R without the best day and the
best-day share; R split by SPY day type (SPY open-to-close > +0.25% up, < -0.25% down, else quiet) for the QDAY focus.
Data: the 2-year cache rebuilt 2026-11-04 (research/bdi/1104/DATA.md), 1-minute SIP resampled to 5 minutes.
**N = 6 configurations -> full bar sqrt(2 ln 6) = 1.89, BAR90 = 1.70.** No post-hoc configs. The locked block is
scored only if a config clears every open-history gate.

## A — morning-rally pullback long with a "session room" target check (r/Daytrading 1xnpo24 = r/Trading 1xo1lmv, 2026-11-04)
Poster: after a morning rally, wait for a pullback and buyers stepping in, go long — but first check whether the
target fits the range the session still has (an ADR-style range estimate); skip the trade when the target needs an
extension the session has shown no sign of. The poster's own range model (similar historical sessions) is not
published; the stand-in is the stock's ATR14 (prior days) measured from the session low so far.

Universe: point-in-time top 250 non-ETF names by prior-day adv20 (daily.parquet), blackout removed. Long only.
- Rally: session high so far H (09:30 through bar i-1) >= open + 0.5 x ATR14, and H was set >= 2 bars before bar i.
- Pullback: lowest low since the bar that set H, L_pb, is <= H - (1/3)(H - open) and > open (still green on the day).
- Buyers step in: signal bar i (bar close 10:00..13:30) closes above the high of bar i-1, close > L_pb, and bar i's
  low >= L_pb (no new pullback low on the signal bar). First signal per symbol-day.
- Entry: open of bar i+1 (e). Stop: L_pb - 1c. Skip R < 0.10% of price. Target: e + m x R. Else out at the 15:55
  close.
- Room filter (the idea): `none`, or keep only if target <= LOD so far + k x ATR14, k in {1.0, 1.25}.
- Grid: room {none, k1.0, k1.25} x m {1.5, 2.0} = **6 configs**.
- Random control: per trade, 3 random entry bars (10:05..13:35 opens) on the same symbol-day, same $ stop distance,
  same m x R target; excess = trade R minus the mean of its controls.
- Diagnostic (not a config, no extra bar): for each m, trades the k filter keeps vs the trades it drops from `none`
  (difference of means, day-clustered) — does the room check add anything on its own.

## Not tested tonight (backlog only or dropped)
Everything else scanned was psychology, forex / gold / crypto / futures, brokers, prop firms, news, AI-platform
promotion, or mechanisms already in research/backlog.jsonl (see NOTES.md).
