# reddit_1110 pre-declared test plan (written before any scoring)

*Educational only — not financial advice.*

Common rules (docs/RESEARCH_RULES.md), same harness as reddit_1105/1106/1109: costs in (1c + 1 bp per side; entry side x
`gates.tod_cost_mult`, exit side free on a target limit, +2c on stop fills); next-bar-open entries on 5-minute bars;
stop first; gaps through a stop fill at the open; locked block 2024-11-01..2025-02-28 never read (1-minute and daily
rows dropped at load, before any computation); old holdouts 2026-04..06 and >= 2026-09-16 dropped; earnings blackout
(`GD._blackout`) removed; point-in-time top 250 non-ETF names by prior-day adv20; one trade per symbol-day per config;
day-clustered t; regime gate `gates.session_regimes`; WF = share of months > 0 (>= 54%); TRAIN <= 2025-08-31 / VALID
after (both > 0); beats random entries; avg R without the best day and the best-day share; R split by SPY day type
(SPY open-to-close > +0.25% up, < -0.25% down, else quiet). Data: the 2-year cache rebuilt 2026-11-04.
**N = 8 configurations tonight. Full bar max(1.5, sqrt(2 ln 8)) = 2.04; Testing bar (BAR90) = 0.9 x 2.04 = 1.84.**
No post-hoc configs. The locked block is scored only if a config clears every open-history gate.

## G — "grind with no real pullback" continuation (both sides, LONG first; r/Daytrading 1xszib3, 2026-11-10)
Post: in the last two sessions breakouts were "stuffed" while "a few stocks just grinded upward with no real pullback or
setup" (so pullback/breakout traders never got in). The idea: when a name trends smoothly from the open, enter without
waiting for a pullback and ride it to the close. The post gives no rule; MCF's mechanical reading (fixed here, not
gridded):
- At the check bar (5-minute bar closing at Tc), with open = the 09:30 open, move = close(Tc) - open:
  - move >= +0.5 x ATR14 (long) / <= -0.5 x ATR14 (short);
  - path efficiency ER = |close(Tc) - open| / (sum of |5-minute close-to-close changes| since the open, first bar from
    the open) >= E;
  - "no real pullback": the largest retrace from the running high (long; running low for short) at any bar up to Tc
    <= 35% of (HOD - open) [(open - LOD) for short], and close(Tc) within the top 25% of that move.
- Entry next 5-minute open; stop = lowest low (highest high) of the last 6 five-minute bars -/+ 1c;
  skip R < 0.30% of price or R > 1.5 ATR14. Exit at the 15:55 bar close.
- Grid side {long, short} x Tc {11:00, 12:30} x E {0.30, 0.45} = **8 configs**.
- Random control: per trade, 3 random 5-minute entry bars on the same symbol-day between 10:00 and 14:30, same side,
  same $ R, same exit.
- QDAY read: report SPY up / down / quiet R; a symbol-relative trend idea should not need the tape's direction.

## Kept, not tested tonight
- none (the other posts were dropped; see NOTES.md).
