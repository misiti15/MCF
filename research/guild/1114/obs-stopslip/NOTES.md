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

## Refit with Skeptic's side split (11-12 ~05:45 ET; stopslip2.py -> stopslip2_out.txt)
- Drop only exits BETTER than the original stop by > 0.02R (moved breakeven / trailing): 463 of 5,461 (8.5%; Gen 13.4%,
  Primary 5.9%). Keep every adverse exit, however large.
- Kept 4,998: mean +0.059R (was +0.045 with the symmetric trim), median +0.036, p90 0.136, p95 0.196, p99 0.376, max 2.46;
  1.9% beyond 0.3R. Per account mean +0.054..+0.061, p99 0.28..0.40: the same everywhere.
- Fit: slip_R = -0.003 + 0.63 x spread/stop (the adverse tail scales with spread; steeper than the trimmed 0.34).
  Quintile mean / p95: 0.024/0.09, 0.036/0.11, 0.052/0.16, 0.066/0.18, 0.120/0.35.
- Unstable by window: 10-20..11-03 mean +0.053 (slope 0.62), 11-04..11-06 sell-off +0.079 (0.74), 11-09 +0.057 (0.27),
  11-10..11-11 +0.044 (0.34). Per-day means 0.036..0.097. One fixed fit overcharges calm days by ~0.01-0.02R and
  undercharges fast tape: check by quintile on 11-12..11-13 before trusting, as Skeptic said.

## Housekeeping flag (11-12 07:45 ET): 'stop' exits that are winners
- r_multiple >= 0 among exit_reason='stop' (live, 10-20..11-11): Gen 7.8% of 1,419 (+82.4R), Testing A 0.4% (+1.8R),
  Primary / On Deck / Graveyard 0.0%. Gen's trailing / breakeven stops exit in profit but keep the label 'stop'.
- Consumers: mcf/report/live_status.py:32 and mcf/report/daily_review.py:30 report stop_exit_share = share of
  exit_reason == 'stop', so Gen's stop-out share is overstated by ~8% of its stop exits. The other accounts' moved-stop
  exits (6-10% better than the original stop by > 0.02R) are still losers, so 'stop' stays honest there.
- Suggest (housekeeping, outside market hours): label profitable stop exits 'trail' (or report stop_exit_share on r < 0).
Educational only — not financial advice.
