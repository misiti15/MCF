Educational only — not financial advice

# U7 notes (working log)

- 18:05 UTC journals copied from the 10 mcf-data* branches. Arena records computed from assignments.json 11-18.
- 18:20 eligibility filter + ranking frozen (u7_eligible_ranked.csv). 1-min SIP bars fetched GET-only for the 1,601
  symbol-days of the 20 setups, and daily bars from 08-20 (no locked-block date involved).
- 18:30 PLAN.md written and pushed before any scoring (commit a36038e7c).
- Set before scoring: the stop-cost feature is the LR8 formula (journal stop_cost_r is missing on about half the
  trades). A missing feature never blocks a trade.
- First run: RW7's time stop showed +130R on fit. Traced to ITA 10-27: Alpaca bars are split-adjusted after a later
  3:1 split, and the live price is not. Fix: rescale a path when the last close before entry is more than 3% off the
  live entry (only ITA was affected). Re-run: RW7 still picks the 120-minute time stop (fit -11.4 → -8.7R). Check
  -30.2R. No verdict changed.
- diag.py runs after the verdicts (never used for them): parent entries vs random entries on check days, and every
  candidate's check effect, to test whether fit picking beats a median pick.
- Scratch directory (journals, bars) deleted at the end.
