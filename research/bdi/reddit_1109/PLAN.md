# reddit_1109 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Common rules (docs/RESEARCH_RULES.md), same harness as reddit_1105/1106: costs in (1c + 1 bp per side; entry side x
`gates.tod_cost_mult`, exit side free on a target limit, +2c on stop fills); next-bar-open entries on 5-minute bars;
stop first when a bar touches stop and target; gaps through a stop fill at the open; locked block
2024-11-01..2025-02-28 never read (1-minute rows and daily rows dropped at load, before any computation); old holdouts
2026-04..06 and >= 2026-09-16 dropped; earnings blackout (`GD._blackout`) removed; point-in-time top 250 non-ETF names
by prior-day adv20; one trade per symbol-day per config; day-clustered t; regime gate `gates.session_regimes` (up and
down both > 0); WF = share of months > 0 (>= 54%); TRAIN <= 2025-08-31 / VALID after (both > 0); beats random entries
(excess > 0); avg R without the best day and the best-day share; R split by SPY day type (SPY open-to-close > +0.25%
up, < -0.25% down, else quiet). Data: the 2-year cache rebuilt 2026-11-04 (research/bdi/1104/DATA.md).
**N = 14 configurations tonight (A 6 + B 8). Full bar max(1.5, sqrt(2 ln 14)) = 2.30; Testing bar (rule 22 BAR90)
= 0.9 x 2.30 = 2.07.** No post-hoc configs. The locked block is scored only if a config clears every open-history gate.
Stops narrower than 0.30% of price are skipped (guild Skeptic 11-09: tight stops pay most of the cost per R).

## A — leader pulled back 3-7 days into the rising daily 9/21 EMA, intraday trigger (LONG; r/swingtrading 1xqieam, 2026-11-07)
Post (a study of a public trader's 2026 streams): 66% of longs are pullbacks of a leader into the rising daily 9/21 EMA
after 3-7 days; entries are intraday (VWAP reclaim, 1/5/15-minute opening-range break, opening flush undercut and
reclaim) with a tight intraday stop at the low of day. Intraday adaptation (MCF is flat by the close): exit at the
close or at a fixed target.
- Daily context for session D (data through D-1 only): leader = close(D-1) / close 60 sessions earlier >= 1.20;
  EMA21(D-1) > EMA21(D-6) (rising) and close(D-1) > EMA21(D-1) x 0.98; the highest close of the last 10 sessions was
  3..7 sessions before D; low(D-1) <= EMA9(D-1) x 1.005 (into the 9 EMA zone). 60-session window must span <= 100
  calendar days (no dropped block inside).
- Triggers T (first per symbol-day, 5-minute closes 09:45..11:30):
  - T1 ORB15: close > 09:30-09:45 high.
  - T2 undercut-reclaim: the session low so far < prior-day low, then close > prior-day low.
  - T3 VWAP reclaim: some earlier 5-minute close < session VWAP, then close > VWAP.
- Entry next 5-minute open. Stop: session low so far - 1c. Skip R < 0.30% of price or R > 1.5 ATR14.
- Exit X: {close (15:55 bar close), 2R target else close}.
- Grid T {1,2,3} x X {close, 2R} = **6 configs**.

## B — daily inside-day breakout, both sides (r/Daytrading 1xrs4yu "Inside Bars & Gap Fills (Compression)", 2026-11-09)
Post: watchlist of inside-bar compression names with a long trigger above the level (and the opposite below).
- Daily context: D-1 is an inside day (high(D-1) < high(D-2) and low(D-1) > low(D-2)); D-2..D within 7 calendar days.
- Trigger: first 5-minute close above high(D-1) (long) / below low(D-1) (short), 09:35..15:00.
- Entry next 5-minute open. Stop S: {mid of the D-1 bar, far side of the D-1 bar}; skip R < 0.30% or R > 1.5 ATR14.
- Exit X: {close, 2R target else close}.
- Grid side {long, short} x S {mid, far} x X {close, 2R} = **8 configs**.

## Random control (both)
Per trade, 3 random 5-minute entry bars on the same symbol-day within the trigger window, same side, same $ R, same
exit rule (target m x R, or the close).

## Not tested tonight (backlog only)
- reddit-1109-chop-day-inside-pdr-lowvol-filter (r/Daytrading 1xrifsz): a filter on other families; needs a remedy-style
  per-setup report, not a scout run.
