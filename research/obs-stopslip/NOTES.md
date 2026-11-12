# OBS-STOPSLIP — live stop-exit slippage and a replay model (Observer, 2026-11-12 ~03:50 ET)

Why: Builder's FWDCAL halt lever found live stop fills +0.046R worse than replay (stop-stop rdiff, 11-04..11-06), which
decides Graveyard's -2R latch (OBS-HALTFLIP). Live journals, run 1, 10-20..11-11, all 7 accounts, 5,453 stop exits. 0 configs.
Repro: `python stopslip.py <dir of journals>` -> stopslip_out.txt.

- slip_R = side*(stop - exit)/|entry - stop|. Core (|slip| <= 0.3R, n 5,228): mean +0.045R, median +0.031R, day-t +21.5,
  81% of stop exits fill worse than the stop. Same in every account (Primary +0.045, On Deck +0.041, Testing A +0.043,
  Graveyard +0.044, Gen +0.047). Matches Builder's +0.046.
- Driver = entry spread as a share of the stop distance: quintiles +0.018 / +0.028 / +0.041 / +0.053 / +0.082R.
  Fit: slip_R = +0.012 + 0.34 x (spread / stop distance). Hour matters little (+0.055 at 10h -> +0.037 after 13h).
- One-big-day: worst day (10-20) holds 22% of total slip. Not one day.
- Data trap: 10.8% of Gen's 'stop' exits (vs 0.7-3% elsewhere) are > 0.3R from the journal's stop, mostly FAVOURABLE
  (5th pct -1.18R). The trades.stop column keeps the ORIGINAL stop, while exits after a moved (breakeven / trailing) stop
  are still labelled 'stop'. Any stop-cost study must drop or separate these; the raw mean (Gen -0.075R) is meaningless.
- Use: put the fitted slip in the replay's stop fills (makes the latch replayable within ~0.01R on average), rather than
  feeding live latch minutes. Remedy angle (owner remedy rule): the existing max_spread_risk_frac 0.25 already cuts the worst
  tail (only 3% of stop exits sit above 0.25; 20% above 0.15). No filter change proposed: the cost is ~0.045R per stop-out
  (~0.018R per trade), small next to direction, and spread filters were found protective (REPS1b).
Rule-change context: window spans many config changes (ledger); this is execution-level and pooled over setups.
Educational only — not financial advice.
