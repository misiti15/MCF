# reddit_1105 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Common rules (docs/RESEARCH_RULES.md), as reddit_1104: costs in (1c + 1 bp per side; entry side x
`gates.tod_cost_mult`, exit side free on a target limit, +2c on stop fills); next-bar-open entries; stop first when a
bar touches stop and target; gaps through a stop fill at the open; locked block 2024-11-01..2025-02-28 never read
(1-minute rows and daily rows dropped at load, before any computation); old holdouts 2026-04..06 and >= 2026-09-16
dropped; earnings blackout (`GD._blackout`) removed; point-in-time top 250 non-ETF names by prior-day adv20; one trade
per symbol-day per config; day-clustered t; regime gate `gates.session_regimes` (up and down both > 0); WF = share of
months > 0 (>= 54%); TRAIN <= 2025-08-31 / VALID after (both > 0); beats random entries (excess > 0); avg R without
the best day and the best-day share; R split by SPY day type (SPY open-to-close > +0.25% up, < -0.25% down, else
quiet). Data: the 2-year cache rebuilt 2026-11-04 (research/bdi/1104/DATA.md), 1-minute SIP resampled to 5 minutes.
**N = 12 configurations tonight (A 8 + B 4), counted together -> full bar sqrt(2 ln 12) = 2.23, BAR90 = 2.01.**
No post-hoc configs. The locked block is scored only if a config clears every open-history gate.

## A — twice-defended level that weakens, then breaks (r/Daytrading 1xom7y4, 2026-11-05)
Poster (CRWV short): buyers defended a level twice, each bounce weaker; when the level finally broke, short, stop
above the failed bounce highs, target the next level. Tonight's BURST1 finding (shorts that wait for the bounce work,
shorts that chase the flush fail) adds a retest entry; the long mirror (resistance rejected twice, higher pullback
lows, break up) is tested with the same rules.

Short side (long side is the exact mirror: H = session high, highs >= H - 0.1 ATR, pullbacks, higher lows):
- At bar i, L = session low through bar i-1. Touch bars: low <= L + 0.10 x ATR14 (prior days). Touch bars group into
  episodes; a new episode starts only after a bounce (high since the last touch >= L + 0.30 ATR). Need >= 2 episodes,
  and the final bounce (max high since the last touch) < the previous inter-episode bounce (weakening).
- Break: bar i closes < L - 0.05 ATR; bar close 10:00..14:30; first qualifying break per symbol-day.
- Entry `break`: open of bar i+1; stop = final bounce high + 1c.
- Entry `retest`: first bar j in i+1..i+12 (bar close <= 15:00) whose high >= L - 0.02 ATR and close < L; cancelled
  if any bar closes >= L before that; entry open of bar j+1; stop = max high of bars i..j + 1c.
- Skip R < 0.10% of price or R > 1.0 ATR. Target m x R, else out at the last bar's close.
- Grid: side {long, short} x entry {break, retest} x m {1.5, 2.0} = **8 configs**.
- Random control: per trade, 3 random entry bars (opens 10:05..15:00) on the same symbol-day, same side, same $ R and
  m x R target.

## B — gap-up that holds the prior close after the open (r/Trading 1xokdhq, comment, 2026-11-05)
Commenter: waits ~13 minutes by rule; the condition is "holds the level (yesterday's close) after the open"; names
that open above it and trade back below in the first minutes are skipped. 5-minute proxy: 15 minutes.
- Gap: open / prior close - 1 >= g (and <= 8%); lows of the 09:30, 09:35, 09:40 bars all > prior close.
- Entry: open of the 09:45 bar. Stop: prior close - 1c. Skip R < 0.10% or R > 1.5 ATR.
- Exit: `hold` (out at the last bar's close) or `t2` (2R target).
- Grid: g {0.5%, 1.0%} x exit {hold, t2} = **4 configs**.
- Random control: per trade, 3 random entry bars (opens 09:50..13:00), same symbol-day, same $ R and exit.

## Not tested tonight (backlog only or dropped)
See NOTES.md.
