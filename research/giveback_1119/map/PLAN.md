# Giveback map (giveback_1119/map) — pre-registered plan

*Educational only — not financial advice.* Written 2026-11-19 evening, before any score was computed. This is a
descriptive map (cartography), not a rule test: nothing here proposes a live change by itself. Any exit class that the
map suggests goes to the backlog and must be scored under WB2 (paired, parent's own signals, pooled by mechanism family,
configs counted).

## Data
- **Live:** run 1 (live paper) of all 10 journals (`origin/mcf-data*`: Primary, Testing1, Testing2, LiveLab, Explore1,
  Graveyard, TestingD/E/F, Gen), 2026-10-06..11-19. R = pnl_adj / (|entry - stop| x shares) (LR8 costs in).
  Minute paths: 1-minute SIP bars 09:30-16:00 from Alpaca market data (read-only GET), one fetch, kept in scratch only.
  Path R unit = |entry - stop| (the live R). Identical signals in two accounts are kept per account for the account-day
  part (b) and de-duplicated (strategy, symbol, entry minute) for the per-trade part (a)/(c).
- **2-year lab:** `research/history2y/data/bt_lab1104` signal lists (current lab setups, 2024-10..2026-11-04) walked on
  `data/cache_hist/1Min` with the BEREPLAY engine conventions (entry = signal-bar close, R = 0.25 x atr_d, live
  geometry, stop-first inside a minute, costs exactly as bt_all). **Locked block 2024-11-01..2025-02-28 is filtered at
  read time and asserted absent.** To avoid uncapped overlapping chains, only the first signal per (setup, symbol, day)
  is walked. Fit = dates <= 2025-09-30, check = later dates. Unit = stop distance (as BEREPLAY: result / dn).

## (a) Per trade
MFE, MAE (stop units, gross, from bars), minutes to MFE, giveback = MFE - final net R; P(full stop | reached +x) for
x in {0.5, 0.8, 1.0}; R lost by trades that reached +x and closed <= 0. Cuts: family x side, instrument type (stock /
ETF / leveraged ETF / inverse ETF, by name rule from rootcause itype.py), entry time bucket (09:30-10:30, 10:30-12:00,
12:00-14:00, 14:00+), hold time, day type (SPY open->close +/-0.25%), SPY move during the trade signed by trade side
(with / against, +/-0.2%).

## (b) Per account-day (live only)
Minute MTM R curve = realized net R of closed lots + open lots marked at minute close in R. Peak, trough, close. Count
account-days with peak >= +5R that close red (and peak >= +3R). For peak->close legs >= 5R: decompose the giveback into
(i) lots open at peak (their change), (ii) lots entered after the peak (late entries), and report SPY move peak->close
signed by the book's net direction at the peak, and the same-direction share of open lots at the peak.

## (c) Stalled-trade signature
At checkpoints t = 5, 10, 15, 30, 45, 60, 90, 120 minutes after entry, for trades still open: state from the path so far,
and **remaining value = final net R - net R of a market exit at the minute-t close**. Early-exit cost = bt_all exit cost
(SL + px x BP) **plus an extra 0.01/share** (conservative). Pre-registered states (exclusive, in this order):
1. `below` : mark <= -0.5
2. `faded` : MFE so far >= 0.5 and mark <= 0 (had it, gave it all back)
3. `flat`  : MFE so far < 0.25 and -0.5 < mark < 0.25 (no progress)
4. `working`: mark >= 0.5
5. `other`
Per family x side (n >= 300 in-state trades, lab) report mean remaining value, day-clustered t, fit and check halves,
avg w/o best day. A pocket is called "not going to work out" only if remaining < 0 in **both** halves and the full-
sample t <= -T, with T = max(2.0, sqrt(2 ln K)) where K = number of (family x side x state x t) cells scored (counted
and reported). Same table on live (descriptive only; too few sessions for a bar).

## Counting
This map scores descriptive cells, not configs; the cell count K is reported. Configs tried for exit rules: 0.
