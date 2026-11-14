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

## RESULT (one look, 2026-11-14 03:30 ET) — FAIL, ETFTIER closed; the prior held
`etftier.py` (selftest ok) -> `etftier_out.txt`. 240 SPXL / 242 TQQQ up-reading days.
| | SPXL plain | SPXL tiered | TQQQ plain | TQQQ tiered |
|---|---|---|---|---|
| gross avg R | +0.057 | +0.035 | +0.072 | +0.054 |
| net avg R (t) | -0.031 (-0.43) | -0.052 (-0.99) | -0.023 (-0.30) | -0.038 (-0.74) |
| median net R | -0.083 | **+0.088** | -0.017 | **+0.075** |
| TRAIN / VALID net | +0.067 / -0.090 | -0.015 / -0.074 | +0.043 / -0.062 | -0.056 / -0.026 |
Tiered minus plain (paired): SPXL -0.021R (t -0.67), TQQQ -0.015R (t -0.40); tiered better on only 29-30% of days.
Stop hit 37% / 33%; +0.5R reached 59% / 55%; +1R 35% / 32%.
Reading for the owner: scale-outs make the TYPICAL trade look better (the median turns positive, the 'feels like winning' effect)
while lowering the AVERAGE, because they cut the right tail that pays for the stops. Both versions lose after costs on a ~0
drift, as the prior said.
