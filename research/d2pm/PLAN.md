Educational only — not financial advice.

# D2PM — does the PREMARKET carry direction for the day's big movers? (Observer, plan FROZEN 2026-11-10 07:55 ET, before any data)

Lead: lead-20261110-0700-4 (D2, P3, after 16:00 ET). Descriptive, gross first, **3 counted looks**, 0 rules proposed here.
Family N: overlaps gap-and-go / gap continuation (Scout's EVD1 count holds gap-and-go 212 inside N 858); Skeptic to state the
D2 family N before anything moves toward a plan. Size alone is noise (SIZEBKT), so only DIRECTION results count toward a rule.

## Sample
- Sessions 2026-10-07..2026-11-09 (live window with premarket data; 1st session dropped for norms). Names: the 1,522 symbols traded
  live 10-06..11-06 (data/cache_hist/1Min RTH bars) + SPY. Phase 2 (2 years, lab universe) only if phase 1 shows a direction effect.
- Premarket bars 04:00-09:29 ET from Alpaca SIP via `pm_fetch.py` (refuses to run 07:30-16:00 ET; never touches the live job).
- Event names: Skeptic's mapping on research-data earnings_yf (reaction session = date for BMO, next session for AMC, dmh dropped).

## Features (all known at 09:29:59)
- pm_dvol = sum(close x volume) 04:00-09:29; pm_rvol = pm_dvol / median pm_dvol of the prior 5-10 sessions (>= 5 required).
- gap = last premarket price / prior RTH close - 1.
- pm_vwap_drift = last premarket price / premarket VWAP - 1 (premarket trend INTO the open beyond the gap level).
- pm_late = last premarket price / premarket price at 09:00 - 1 (last 30 min).

## Labels (RTH, from data/cache_hist/1Min)
- Mover: Move-Hunt style, from the 09:35 bar close the max favourable excursion within 90 min in daily ATR (prior 10 sessions'
  mean true range), top 50 per side per day over the sample names.
- Tradable direction: ret_0950 = close(11:30) / open(09:51) - 1 (entry the bar after 09:50, as the live rule), and to 15:55;
  ex-market = ret - beta60 x SPY ret over the same span (beta60 on prior daily returns where available, else 1; stated).

## Looks (counted; nothing else is read)
- L1 SIZE (descriptive only): AUC of pm_rvol for top-50 mover membership (either side); report event vs non-event.
- L2 DIRECTION: sign(pm_vwap_drift) x ex-market ret_0950 (11:30 and 15:55), day-demeaned, within gap-sign strata, in the top
  pm_rvol quintile and overall; Welch day-t; event vs non-event.
- L3 DIRECTION: same with sign(pm_late).
- Baseline every direction look must beat: sign(gap) x the same return (the 'any gapper continues' line Scout uses in EVD1).
- Pre-posting routine (roles/observer.md): labels known at entry, best-day share, ex-market, up/down/quiet day split.

## Kill line
If L2 and L3 both fail to beat the gap baseline in the top pm_rvol quintile (gross, ex-market, day-t < 2), D2 is closed with numbers.
