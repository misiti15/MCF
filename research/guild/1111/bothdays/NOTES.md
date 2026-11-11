# BOTHDAYS — do any live setups earn on both SPY up and down sessions? (descriptive, 0 configs)
Educational only — not financial advice.

Source: the 7 account journals (live paper run only, to 2026-11-10), 18,878 trades / 194 setups, pooled over accounts.
Day type = SPY 09:30 open -> 16:00 close (Alpaca daily SIP bar, `spy_daily.csv`): 17 up days, 9 down days.
Script: `python -I research/bothdays/bothdays.py <journal dir> research/bothdays` -> `bothdays_out.txt`, `bothdays_all.csv`.

Result (74 setups with >= 10 trades on each day type; 32 long-only, 40 short-only):
- Positive on up days: 20. Positive on down days: 24. Positive on both: 2 (L3-gap-slope-fromopen-FD, L3-gap-slope-lowdist-FD),
  and each fails w/o its best day on one side. Passing the full gate (both sides positive, also w/o best day): **0**.
- Median market beta: longs +0.145 R per 1% SPY o->c, shorts -0.134. Every family leans with the tape.
- Direction-free part (intercept of daily R/trade on SPY o->c): 13 of 74 > 0; 1 with t >= 2 (CWT13-vwapstretch-z075-long,
  +0.45, t 2.56, only 40 trades / 9 days), fewer than the ~3.7 expected by chance.
- This matches Builder's 2-year lab join (builder-20261111-0040-1): live "what works" is a direction bet; none is all-weather.

Rule-change context: the window 10-06..11-10 holds the ledger changes listed in WHATWORKS (up to 7 per setup:
sizing/PVSCALE, timing fixes, moves); results mix setup behaviour with those changes, and down days are only 9.
Next idea it points to: a setup whose *side* follows the day type known at entry (e.g. SPY first-30-min sign or the
compass "staying" read) — but RCOMPASS showed the compass reads staying, not heading, so any such test needs an
ex-ante day-type label scored against the same setups with a fixed side.
