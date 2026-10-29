Educational only — not financial advice.

# Failed Prior-Day-Low Break Longs on demotion watch: evaluation after 2026-10-29

Live **paper** results; costs in (R = `pnl_adj` / $ risk, same as `nightly1029/combined.py`). Journals are the nightly1029
fetch (`n1029` scratch). Records are merged by setup name across accounts, as the dashboard does (p05-long has a few T2
trades). **No new backtest was run and no configurations were tried here.** Two-year numbers are reused from swarm15_1029
(parent, TRAIN+VALID, costs in) and p1_1029. No config, setup, exit, ledger or backlog change; nothing committed.
Script: `evalpdl.py` -> `evalpdl_out.txt`. Known gap: T1's journal is missing 132 trades on 10-19 (nightly1019).

## Per setup

| | p05-long (T1) | p05-lowvol-long (T2) | p10-long (T2) |
|---|---|---|---|
| Today: trades / R / P/L | 57 / -10.25R / -$99 | 49 / -4.71R / -$62 | 35 / +1.22R / -$11 |
| Live: trades / sessions | 675 / 14 | 433 / 14 | 384 / 14 |
| Win vs break-even | 61.8% vs 67.6% | 60.3% vs 68.3% | 66.1% vs 67.6% |
| Avg R (total R, day t) | -0.085 (-57.7R, t -1.04) | -0.115 (-49.9R, t -1.78) | -0.023 (-8.9R, t -0.23) |
| Avg R w/o best day (10-20) | -0.117 (total < 0, share n/a) | -0.142 (total < 0) | -0.069 (total < 0) |
| Last 5 sessions R | 10-23 +3.5, 10-26 -8.6, 10-27 -16.0, 10-28 +0.9, 10-29 -10.3 | -1.8, -7.7, -13.0, -0.3, -4.7 | +10.9, -0.8, -7.3, +1.9, +1.2 |
| Trend (avg R 1st / 2nd 7 sessions) | -0.062 -> -0.101 (worse) | -0.098 -> -0.129 (worse) | -0.059 -> +0.016 (flat/better) |
| Since 10-27 (post GX1 fix) | 233 tr, -0.109, -25.4R, t -1.71 | 157 tr, -0.115, -18.1R, t -1.61 | 121 tr, -0.034, -4.1R, t -0.47 |
| 2-yr avg R (n, t) | -0.068 (53,326, t -9.5) | -0.095 (35,238, t -8.6) | -0.088 (29,836, t -7.7) |
| 2-yr up / down SPY sessions | +0.014 / -0.146 | +0.041 / -0.217 | +0.034 / -0.206 |
| Best variant (swarm15, 19 per setup) | stop x3.0: -0.021 / -0.017 | stop x3.0: -0.028 / -0.027 | stop x3.0: -0.027 / -0.027 |

- **No variant fixes them.** swarm15: 0 of 287 variants pass; the stop-x3.0 curve converges near -0.02R, not above zero;
  the cost floor helps but stays negative; context filters, targets, time stops, re-entry all fail. p1 (L/V gates): no
  CWT14 row positive. They are market-direction bets: small gain on up sessions, large loss on down sessions.
- **Correlation:** 849 symbol-days; 63% traded by 2+ of the three, 13% by all three (p05: 72% of its symbol-days shared,
  lowvol 87%, p10 82%). Same-day R correlation: p05/p10 0.93, p05/lowvol 0.78, lowvol/p10 0.70. Effectively one bet
  taken three times.
- Caveats: the two-year frames do not apply the earnings blackout (coverage1029); signal rates before 10-27 were too low
  (pre-GX1 bug) but per-trade R is what matters here, and since-10-27 R is no better. One-big-day: all three totals are
  negative, so best-day share is n/a; 10-20 is the best day for all three (+16.7 / +9.5 / +15.7R).

## Recommendation (owner decides; rule 20)
- **D1 p05-long: demote to Graveyard.** Loses live (-0.085, worse since 10-27) and on 2 years (t -9.5); no variant crosses zero.
- **D2 p05-lowvol-long: demote to Graveyard.** Worst of the three live and on 2 years; 87% overlap with the others.
- **D3 p10-long: demote to Graveyard.** Near-flat live only because of 10-20 (-0.069 without it); 2-yr -0.088, 0.93 correlated with p05.
- Note (not asked): `CWT14-failbrk-pdl-p10-lowvol-long` (Primary + T2) is the same family, 2-yr -0.095; live +0.002, -0.027 without its best day.

Educational only — not financial advice.
