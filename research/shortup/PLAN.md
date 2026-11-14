# SHORTUP — short-hold up-day long: strongest stock in the strongest sector, 10:30 -> 11:30 (FROZEN 2026-11-14 05:30 ET, before any fetch)
Educational only — not financial advice. Lead lead-20261114-0500-2 (main-session brief: short-hold up-day longs).
Prior: UPDAY-LONG found no cross-sectional long edge on up readings (ex-market ~0), and first-hour momentum lines in the backlog
mostly failed. Expected: ~0 excess.

## Data (Alpaca SIP, GET only; locked block 2024-11-01..2025-02-28 never fetched)
30-min bars (split-adjusted) and daily bars for: the 500 highest-adv non-ETF names in data/universe.csv (snapshot 2026-10-05;
survivorship applies equally to the pick and its control), the 11 SPDR sector ETFs, SPY. 2024-10-01..2024-10-31 and
2025-03-03..2026-11-13.
## Sector map (formation only)
Formation 2025-03-03..2025-04-30. Each name -> the SPDR with the highest correlation of 30-min RTH returns, kept if corr >= 0.40.
Test window 2025-05-01..2026-11-13 (TRAIN <= 2025-12-31 < VALID). The map is never refit.
## Rule (ONE config), all readings use bars that END by 10:30 ET
Up reading: SPY close of the 10:00 bar > SPY 09:30 open. Move m(x) = (close of the 10:00 bar / 09:30 open - 1) / ATR%(x),
ATR% = 14-day mean true range / prior close (days < D). Strongest sector = the SPDR with the highest raw 09:30 -> 10:30 return.
Pick = the member of that sector with the highest m (price >= $5). Long at the 10:30 bar open, exit at the 11:30 bar open (one hour).
Outcome per day: c = (exit/entry - 1) - (SPY 11:30 open / SPY 10:30 open - 1), in ATR units and bps (ex-market).
Control (same minute): all names (any sector, price >= $5) in the top decile of m that day, excluding the pick. Control value =
their mean c. Excess = c(pick) - control. Costs on the pick: entry 1c + 1bp x 1.4 + 4.4bp spread; exit 1c + 1bp.
## Counting, bar, pass
Family: market-state / up-day track 2,608 + 1 = 2,609 -> BAR90 3.57.
Pass (all of): excess day-t >= 3.57; pick's gross ex-market c > 0 and NET c > 0; same sign in TRAIN and VALID; w/o best day > 0.
Kill line: fails -> SHORTUP closed; no grid over time, hold or decile.
Reported (not gates): top-3 picks average; strongest-sector ETF itself over the same hour; pick's raw (not ex-market) return.
