# ETFTIER — 3x ETF long on SPY-up mornings: tiered scale-outs vs a plain close exit (FROZEN 2026-11-14 03:20 ET, before scoring)
Educational only — not financial advice. Lead lead-20261114-0300-2 (main-session brief: tiered 3x ETF setups with scale-outs).
**Prior, stated up front:** exits reshape the distribution of a trade but cannot create expectancy from a ~0 drift (BEREPLAY:
path-conditioned exit fixes were ~10x overstated). Observer's null: SPY's return from 10:30 to the close is ~0 on up-reading
days, and LEAD20 measured +0.3..+6.5bps on them. So the expected result is: tiered ~= plain ~= 0 gross, negative net.
Data: LEAD20's cache (5-min SIP bars, SPXL / TQQQ / SPY, 2024-10-01..2026-11-13, locked block absent). Bars and prices were
fetched for LEAD20; this rule's outcomes have not been computed.

## Rule (one entry, two exits = 2 configs; instruments SPXL and TQQQ scored separately in their own prices)
Day filter: SPY close of the 10:25 bar > SPY 09:30 open (up reading at 10:30, strict).
Entry: long at the open of the 10:30 bar. Stop: the ETF's own low of the 09:30..10:25 bars. R = entry - stop, floored at
0.5% of entry (a stop at or above the entry gets the floor). Within a bar, the stop is checked before a target (conservative).
- PLAIN: stop, else the close of the 15:50 bar.
- TIERED: 1/3 out at +0.5R, 1/3 at +1.0R, the rest at the 15:50 close. The stop applies to whatever is still open; it never moves.
Costs, own price, per share: entry 1c + 1bp x 1.4 + 4.4bp spread; each exit (each tranche) 1c + 1bp. The stop adds 2c.
R per trade = sum over tranches of (weight x (exit - entry - costs)) / R.
## Score
Per instrument: avg net R and gross R for PLAIN and TIERED; TIERED minus PLAIN (paired by day; day t); TRAIN (<= 2025-09-30)
/ VALID; w/o best day; median R; share of days hitting +0.5R / +1R / the stop.
Family: market-state 2,606 (LEAD20) + 2 = 2,608 -> BAR90 3.57.
Pass (a lead for Testing A-F, owner decision): TIERED net avg R > 0 with t >= 3.57 on SPXL, > 0 in TRAIN and VALID, w/o best
day > 0. Anything less -> closed, and the number goes to the owner.
