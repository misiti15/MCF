# OBS-ETFLIVE — our live leveraged / index-ETF trades vs the up-day null (Observer, 2026-11-14 ~02:10 ET)

Lead's ask (lead-20261114-0100-4). Live journals run 1, all 10 accounts, 2026-10-06..11-13: 739 trades on 28 sessions,
115 setups (most are stock setups that happened to pick an ETF). Descriptive, 0 configs. Repro: etflive.py -> etflive_out.txt.
Exposure +1 = profits if the index rises (long bull ETF / short bear ETF). SOXL/SOXS proxied by QQQ, UDOW/SDOW by SPY.

1. ETF trade R IS the index move over the hold: corr(R, underlying move entry->exit in the exposure direction) = 0.82.
   These trades are index-timing bets, so OBS-UPDAY-NULL (rest-of-day index return ~0) applies directly.
2. Costs are not the problem: median entry spread / stop distance 0.016 vs ~0.08 for live stock trades (OBS-STOPSLIP).
3. Bullish exposure lost, bearish was flat:
   bullish, entered WITH an up sign-so-far   n 142, 15 days, -49.1R, avg -0.346 (w/o best day -0.412), index over hold -12.7bps, 32% index-up
   bullish, entered AGAINST it (buy a down day) n 228, 17 days, -34.2R, avg -0.150 (-0.196), index +0.6bps
   bearish, against the sign so far             n 182, 20 days, +4.3R, avg +0.024 (w/o best -0.081)
   bearish, with it                             n 187, 16 days, +2.7R, avg +0.014 (w/o best -0.080)
   Buying strength after an up morning did worst: the index gave back ~13bps over those holds (sell-off month).
4. Dedicated index-ETF setups:
   intraday_momentum (SPY/QQQ/IWM): 52 trades, 23 days, -16.3R, avg -0.31, index -12.4bps over holds, 23% index-up. Momentum
     on the index loses, as the null predicts (and worse, in a reverting month).
   NM-ETF-late-dip-di-long: 16 trades, 11 days, +5.8R, avg +0.36, w/o best day +0.37 (best day 24%), index +18bps, 88% up.
     Buys late-day dips: the one positive record, but 16 trades / 11 days is thin (ICC: ~11 setup-days).
   LD2 (TQQQ dip): 6 trades -1.0R; LD6 (SPXL dip): 2 trades +1.8R. Too few to read.
5. By entry hour, 11h entries were best (avg +0.19R, index +15bps), 9h and 13h worst. Not a finding at this n.
Reading for the blitz: our live ETF book confirms the null. Index continuation after an up reading is ~0 or negative, so
"ride the up day in 3x ETFs" lost here. The only positive shape is counter-move (buy late dips), small n. Edge must come
from selection beyond the index path (cross-sectional longs on up days) or from dips, not from chasing the up reading.
Rule-change context: the window spans many config / roster changes (11-04..11-06 sell-off; 11-12 restructure c64d75df0:
Testing D/E/F added, halts 300R; Gen buying-power work). Pooled descriptive numbers, not setup verdicts.
Educational only — not financial advice.
