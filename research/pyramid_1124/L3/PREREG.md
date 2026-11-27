# PYRAMID L3 (longs: ride the trend / mine the live record) - pre-registration
Educational only - not financial advice. Written 2026-11-24 before any backtest of any config below was scored.
Only the live record (live_ext.pkl, run 1, 10 accounts, LR8, 2026-10-06..11-24) has been looked at.

## Data / split / costs (fixed)
- T1 = research/history2y frames + data/cache_hist/1Min. FIT = 2024-10 + 2025-03..2025-09; CHECK = 2025-10-01..2026-11-04
  (ultimate_1119 halves). Locked block 2024-11-01..2025-02-28 never read (bench10 guards: month list, pyarrow filters, asserts).
- T2 = 2023-01-03..2024-09-13 (cache_fresh, 469 symbols, frames built as bench10 t2). Reported (2023-24 vs 2025-26), not used to select.
  T2 has no lab breadth column: breadth is rebuilt on the 469 T2 names (share with 5-min close above session VWAP) - an approximation.
- Entry = decision 5-min bar close (bench10), exits walked on 1-min bars (stop first, target needs +$0.01 trade-through, flat 15:55),
  LR8 research costs (bench10.add_r). Book = testing-arena rules (cap 100 open, <= 3 lots/symbol, price >= $5, cost filter 0.15R).
  First qualifying bar per symbol-day (refire off), as the GEN parents run live.
- SPY state at a bar with close time T uses SPY 1-min bars labelled < T only: spy_vw = SPY last vs session VWAP (09:30-) in %,
  spy30 = SPY 30-min return %, spy_fo1 = SPY from 09:30 open %.

## Part A - live mining (top 3 live LONGS by avg R after costs, >= 20 trades; all three are Setup Generator setups)
Parents scored exactly as their live YAML/module (mask, window, min_adv, geometry). Tightenings chosen ONLY from the live losers'
pattern (mine_live.py output), <= 2 changes each:
- A1 = GEN-261027-01 (late MACD-hist pullback buy, t05s1, 14:00-15:00, ADV >= $20M, breadth > 0.5).
  A1t = A1 + (1) spy30 > 0 at entry (live: spy30 <= 0 trades -0.07R n 13 vs > 0 +0.45R n 26) + (2) ADV >= $100M (spread proxy:
  live losers' median spread 20.6 bps vs winners 9.8).
- A2 = GEN-261020-09 (midday z-score dip with emaDiff turn on a QQQ-down tape, holdtr, 11:00-13:00, ADV >= $150M).
  A2t = A2 + (1) window 11:00-11:30 (live after 11:30: 62 tr -0.18..-0.31R) + (2) qqq_fo <= -1.0 (live -0.3..-1.0: 36 tr -0.36..-0.73R).
- A3 = GEN-261019-02 (PM lower-band buy in an uptrending SMA20 on a QQQ-down tape, t05s1, 13:00-15:00, ADV >= $150M).
  A3t = A3 + (1) spy_vw >= -0.3 (live < -0.3: -0.05R n 7) + (2) entry price <= $50 (live > $50: -0.18R n 12 vs +0.31R n 14).
- A selection: none (each tightening is fixed). Lift = A?t beats A? on CHECK avg R AND on CHECK avg R w/o best day.
  Caveat stated up front: the Setup Generator screened its specs on the whole open 2-year history (T1 train+valid), so T1 CHECK is
  NOT clean out-of-sample for the parents; T2 (2023-24) and live are. A1 already has a Workbench copy (WB5, 106 configs,
  Testing D) - A1t is a different, live-derived pair of changes.

## Part B - momentum longs (new mechanism; 3 candidates x 2 exits)
Not re-tested: ULT-05 (with-gap continuation, VWAP-near pullback, any tape: FAIL -0.003), ULT-26 (with-gap VWAP pullback on a
"trend tape" gate true at any bar on ~50% of sessions: FAIL -0.045), ULT-06 (late morning-turn reversal: FAIL -0.091),
ULT-18 (fixed-time cross-sectional top-N momentum, any tape, 45 min: FAIL). New here: (a) a once-a-day TREND-DAY gate fixed at
10:30 (SPY above session VWAP AND above its 10:00 price AND above its open) instead of an any-bar gate; (b) BREAKOUT trigger
(5-min bar closes at a new high of day with volume) instead of a pullback; (c) "ride" exits (trail / hold to 15:55).
Universe: ADV20 >= $50M, price >= $10.
- B1 NHOD-AM-TREND: UP1030 day; tod 10:30-11:30; new_hod == 1; volumeRatio >= 2.0; fromOpen_atr >= 0.5; vwapDistPct > 0.
  B1a exit t1s1 (R = 0.25 x daily ATR) with 45-min cap; B1b holdtr (stop 1R, 1R trail once +1R, flat 15:55).
- B2 PM-LEADER-NHOD: 13:30-15:00; at entry spy_vw > 0 and spy_fo1 >= +0.3; stock fromOpen_atr >= 1.0; new_hod == 1;
  volumeRatio >= 1.5. B2a holdtr; B2b t1s1 cap 45.
- B3 TREND-CLOSE-DRIFT: UP1030 day and at the 14:30 bar spy_vw > 0 and spy_fo1 >= +0.3; at tod == 14:30 buy stocks with
  fromOpen_atr >= 1.0, vwapDistPct > 0, dist_hod_atr <= 0.25. B3a stop 1R hold to 15:55; B3b holdtr.
- B selection (per candidate, FIT only): higher (FIT total R - best FIT day R). Pick frozen to fitsel.json before CHECK is scored;
  CHECK scored once.

## Count
A: 3 parents + 3 tightenings = 6. B: 6. TOTAL 12 configs. Random-entry controls (same symbol-days, uniform bar in the config's
window, same exit) and the Primary reference book (L3-fromopen-FD, RW3-FD, RW5-FD, NM-ETF via bench10.signals, Primary rules,
no ETB filter available) are reported, not counted. Cumulative job N (ultimate_1119 ~1,882 + 12) -> t bar sqrt(2 ln 1894) = 3.89.

## Tiers (ultimate_1119 PLAN sec. 6, unchanged)
TIER A: CHECK avg R > 0, CHECK w/o best day > 0, FIT avg R > 0, >= 2.0 trades/session on CHECK, no look-ahead.
TIER B: FIT avg R > 0 and CHECK avg R > -0.02. Else FAIL. Also reported: T2, both check halves, vs random, Primary-book
correlation and R on the Primary reference book's 10 worst T1 days, median hold.
