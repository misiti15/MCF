# PYRAMID round 2, team E ("catch the 09:35 bid", early-session LONGS) — pre-registration
Educational only — not financial advice. Research only. Written 2026-11-25 before any feature table was built or scored.
ENTRY FLOOR EXCEPTION: this team tests entries 09:35-09:50 ET (brief exception for research). Any deployment would need
the owner to lift the standing >= 09:50 entry rule.

## Prior failures not repeated (cited)
- orb5 (failed -0.33R), orb20_a (retired 0.000R), t2-orb15, bdi-rdt-r01-orb30 (0/64), bdi-tod-open-0935-simple (all 30
  negative after opening-spread costs): plain opening-range BREAKOUTS / plain 09:35 entries. Not re-tested. New angle here:
  (i) the sector-ETF-leads-SPY gate at 09:35/09:40 (rotation bid, L1 11-24 evidence), (ii) relative opening volume vs the
  stock's own prior first-5-min volume, (iii) gap-down LOW-BETA reclaim of the first bar's high (defensive rotation).
- ULT-17 sector-lag catch-up (laggards) and L1 C2 sector-leader pullback (10:05+) failed; E3 buys sector members at
  09:40 with the sector already leading — the early bid itself, not a later pullback/laggard.
- ULT-05 with-gap continuation, ULT-26, ULT-28/30 earnings: no gap-up continuation and no earnings angle here.
- NM-AR-AM-gapdown-capitulation-long (live, 09:50-11:00) is a capitulation buy; E2 differs (low-beta, first-bar-high
  reclaim by 09:50, defensive-rotation mechanism).

## Data (what exists)
1-minute RTH bars only (09:30-15:59): data/cache_hist/1Min (1,226 symbols, 2024-09-16..2026-11-04, locked block
filtered at read) and data/cache_fresh/1Min (469 symbols, 2022-10..2024-09-13). NO pre-market / overnight / futures bars
in any cache, so a pre-open predictor can only use prior-day data and the 09:30 open (gap). No pre-open candidate scored.

## Common rules
Long only. Daily features from prior days only: ATR14 (true range, RTH daily bars), ADV20 ($, prior 20 sessions),
beta60 (prior 60 daily returns vs SPY), v5avg20 (mean first-5-min volume, prior 20 sessions). gap = open/prev close - 1.
5-min bars 09:30-09:34 (=tod 935), 09:35-09:39 (940), 09:40-09:44 (945), 09:45-09:49 (950); entry = that bar's close,
exits walked on 1-min bars from the next minute (bench10.walk_trades logic: stop first, gap-through at worse, target
needs +$0.01 through) with a TIME EXIT at entry + 60 min (open of that minute), flat 15:55 irrelevant.
R = 0.25 x ATR14, stop 1R. Price >= $5, ADV20 >= $20M base. First signal per symbol-day per config.
Sector map: L1 secmap.json (highest daily-return correlation with 11 SPDRs >= 0.30, FIT dates only).
Sector/SPY from-open at tod t = ETF close at t / ETF 09:30 open - 1.
Geometries (pre-declared): G1 = 1R target / 1R stop / 60-min cap; G2 = 2R target / 1R stop / 60-min cap.
Costs LR8 (bench10.add_r: entry 1c+1bp x tod mult [2.1x for 935-945, 1.4x for 950], exit 1c+1bp except target, +2c stop,
x3 extended tier). Book = bench10 TESTING_RULES (cap 100, <=3 lots/symbol, stop-cost filter 0.15).

## Candidates and grid (12 configs = 3 candidates x 2 rule values x 2 geometries)
- E1 OPEN-DRIVE-SECTOR (entry 09:35): rvol5 = v5 / v5avg20 >= X; first bar green (c > o) and closes in top 20% of its
  range ((c-l)/(h-l) >= 0.8); stock's mapped sector ETF from-open at 09:35 minus SPY's >= +0.10%; X in {3, 5}.
- E2 DEFENSIVE-GAPDOWN-RECLAIM (entry first 5-min close at 09:40, 09:45 or 09:50 above the 09:30-09:34 high):
  gap <= -G%; beta60 <= 0.8; ADV20 >= $100M; first bar red (c < o); G in {0.5, 1.0}.
- E3 ROTATION-BID (entry 09:40): stock's mapped sector ETF is the strongest of the 11 SPDRs from the open at 09:40 and
  leads SPY by >= S%; stock from-open at 09:40 > 0 and its 09:30-09:39 volume / (2 x v5avg20) >= 1.5; at most the
  top 5 names per day by that volume ratio. S in {0.3, 0.6}.

## Splits, selection, scoring
FIT = 2024-10 + 2025-03..09 (170 sessions); CHECK = 2025-10-01..2026-11-04 (276), scored once; 2023-24 = 2023-01-03..
2024-09-13 (427, cache_fresh 469 symbols) scored once for the selected config. Locked block 2024-11-01..2025-02-28 never read.
Selection per candidate: highest fit avg R after costs among its 4 configs with >= 100 booked fit trades (else most
trades). fitsel.json frozen before any check/2023-24 statistic is computed.
Controls (not counted as configs): (a) SAME-UNIVERSE random: every session, up to 30 random symbols from the candidate's
base universe (E1/E3: price >= 5, ADV20 >= $20M; E2: price >= 5, ADV20 >= $100M) at a random bar in {935,940,945,950},
same geometry/costs/book; (b) same symbol-day random bar in 935-950; (c) E2 only: gap/beta pool random bar (trigger test).
Reported per finalist: brief card, SPY up/flat/down (open->close +-0.30%), correlation of daily R with the Primary book
proxy (L1's re-built RW3-FD, RW5-FD, L3-fromopen-FD, NM-ETF with Primary rules) and R on its 10 worst days, avg R w/o
best day + share, check halves, median hold.

## Bars
- TIER A: fit > 0; check > +0.0836 and check w/o best day > +0.0734 (benchmark standard, "clear-cut better than top
  10"); check day-clustered t >= 1.5; both check halves > 0; 2023-24 > 0; >= 0.5 trades/session on check; beats the
  same-universe random control on check AND on 2023-24.
- TIER B: fit > 0, check > 0 and 2023-24 > -0.02.   Otherwise FAIL.
Configs counted: 12 (+ controls).
