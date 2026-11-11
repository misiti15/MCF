# DISP1 — within-sector split on a flat sector morning: persist or close? (FROZEN before any look)
Educational only — not financial advice. Requested by Lead (lead-20261111-0300-2). One look.

## Data (open data, no locked block)
HODSEP Alpaca SIP 5-min bars, 2026-09-24..2026-11-09: 1,226 lab names + XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY + SPY;
daily bars from 2026-06-01 for ATR. RTH only, timestamps converted to America/New_York (DST change 11-02 handled).

## Sector assignment (no sector map in the repo; data-driven, formation only)
Formation = the first 10 sessions (09-24..10-07). For each name: correlation of its 5-min RTH returns (10:00-15:30 bars)
with each SPDR ETF's; sector = the ETF with the highest correlation, kept only if corr >= 0.40. Never re-fit on test days.
Test = sessions 10-08..11-09 (about 23).

## Event (known at 09:50:00 ET)
r20(x) = close of the 09:45 bar / open of the 09:30 bar - 1. ATR% = 14-day mean true range / prior close, days < D only.
Sector flat: |r20(ETF)| <= 0.20%. Member split: rel = (r20(member) - r20(ETF)) / ATR%; event if |rel| >= 0.50,
and the sector that day has at least one event on each side (a real split). Price >= $5. s = sign(rel).

## Outcome
Entry = open of the 09:50 bar; exit = close of the 15:50 bar (15:55). ATR units.
c_sec = s x [(member exit/entry - 1) - (ETF exit/entry - 1)] / ATR%   (primary, ex-sector)
c_spy = same with SPY in place of the ETF                             (ex-market check)
Costs on the member leg (production): entry 1c + 1bp x 2.1 + 4.4bp spread, exit 1c + 1bp; hedge leg 2bp each way.
follow net = c_sec - cost ; fade net = -c_sec - cost.

## Counting and bar
Configs: 2 (follow / fade, one threshold set, no grid). Family: sector / peer / laggard lines 92 + 2 = 94 -> BAR90 2.71.
Day-clustered t: mean of daily means / (sd of daily means / sqrt(days)).

## Pass (all of)
1. |t(c_sec)| >= 2.71, and the chosen direction (follow if c_sec > 0, fade if < 0) has net > 0 per trade.
2. Same sign without the best day (for that direction), and c_spy same sign with t >= 2.
3. Same sign on the long and short legs (s = +1 and s = -1 separately).
Reported beside (not gates): control = same member rule on NON-flat sector mornings (|r20(ETF)| > 0.20%); the skip funnel;
events per day; per-sector counts.

## Kill line
Fails 1 -> DISP1 closed, the family stays closed. Passes -> a counted forward shadow plan goes to Lead, nothing live.
