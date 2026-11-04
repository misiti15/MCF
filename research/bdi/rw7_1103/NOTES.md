# rw7_1103 — RW7-gapdn-bounce-early-short-FD (Testing 1): is the green streak real, and can a variant make it viable?

*Educational only — not financial advice.* Owner ask 2026-11-03. Research only; no config or trading-path change.
No display name in docs/live/setup_names.json (code name shown). Files: PLAN.md (pre-registered grid), live.py →
live_out.txt / live_trades.csv, cands.py + sim.py + score.py → score_out.txt / results.csv.

## Failures first
- **0 of 24 pre-registered configs reach the Testing bar (t ≥ 2.27 at N 24), and none is even positive after costs.**
  The best is still −0.089R (M1, SPY below its open), so there are no near-misses and no decision.
- The parent loses on 2 years: −0.106R at t −5.45 (n 26,163, 426 sessions, 61.4 a session), −0.061R on production
  costs alone. Avg R w/o best day −0.110R. Ex-market −0.103R, beta −1.06R per 1% SPY. TRAIN −0.124, VALID −0.088.
  Walk-forward 12% of months positive. It beats random same-time shorts by only +0.015R.
- The live record matches the backtest. It is a market-beta short with no edge left once the market is taken out.

## Live record (Testing 1 paper, 10-12..11-03: 17 sessions, 348 trades)
- Avg R +0.017 after costs (P/L +$184.71, win 53%), day-clustered t 0.26. **W/o best day −0.014R**: the best session
  (10-30, +10.4R) is 178% of the total +5.9R (`1 day`, and 10-14 has +10.4R too). 8 of 17 sessions green.
- **Ex-market (BETA1) −0.115R, beta −1.34R per 1% SPY.** By SPY day type: down days +0.210R (n 120 / 5 days),
  quiet −0.091R (171 / 8), up −0.066R (57 / 4). Corr of session R with SPY open-to-close is −0.49.
- **Owner's read, checked:** the last 3 sessions were green (10-30 +10.4R / 27 trades, 11-02 +1.7R on just **2 trades**,
  11-03 +5.5R / 17). Primary was red on 10-30 (−$91) and 11-02 (−$627), so "2 green on red days" is **correct**. But
  both of those were SPY-down days (−0.75% / −0.97%), and a short with beta −1.3 is green on them by construction.
  Over all 17 sessions it does no better on Primary-red days (+0.009R, 10 days) than on green ones (+0.023R, 7 days).
  Its corr with Primary's daily P/L is −0.10, so it is not a red-day hedge.
- **Chance of the streak:** at the 2-year green-session rate (35%), 3 given sessions in a row come up green 4.3% of the
  time. At the live rate (47%) that is 10%. A 3-green run somewhere in 17 sessions happens 38-67% of the time.
  **Verdict: noise plus market direction.**
- Rule changes inside the window (ledger): per-lot stacking 10-13; split-tape short gate (T1) 10-14, which skipped 20
  signals; Testing 1 per-setup −2R latch 10-20..10-22, which skipped 105 signals on 10-22 and was turned off 10-23;
  GX1 5-min clock gate 10-27; CF stop-cost filter 0.15R (Testing) 10-30, which skipped 12 signals on 10-30 / 11-03.
  The whole 3-green streak falls after CF started.
- Live friction was only 0.014R a trade (gross +0.031R), against 0.12R modelled. Paper fills are optimistic (rule 7).
  Even at live friction the 2-year gross (+0.016R) leaves about 0R, and ex-market about 0.

## Where the R comes from (live, 348 trades; small-sample cells)
- Exits: target 119 (+106R), stop 84 (−93R), 15:55 time 145 (−7R). 60% reach +0.5R but only 16% reach +1R.
  Give-back (MFE ≥ 0.5R closed ≤ 0) 42 trades, −25R. Holding to 15:55 with no stop: −0.011R gross.
- Time: 11:30-13:00 +0.098R (n 123) is the only good bucket. 13:00-14:00 −0.118R. 2 years: every bucket negative,
  09:50-11:30 the least bad (−0.075R).
- Gap: ≤ −3% +0.237R (n 44). −0.75..−1.5% −0.137R. 2 years: all negative (≤ −3% −0.099R).
- Kind: ETFs +0.194R (92) and leveraged +0.348R (10), stocks −0.063R (246). These ETFs are index and sector beta
  (SCO etc.). 2 years: ETF −0.115R, leveraged −0.084R, stock −0.106R.
- ADV: > $2B +0.279R (31) and top-100 by ADV +0.209R. 2 years: flat across ADV buckets (−0.10..−0.12R).
- RSI / heat / bp (2 years): flat, −0.09..−0.13R in every bucket. Heat ≤ −40 −0.043R, n 305 only.
- SPY at entry (live): −0.5..−0.25% from open +0.325R; 0..+0.25% −0.176R. 2 years: SPY −0.25..0 −0.050R is the least
  bad, and every bucket is negative.
- Sister stacking: 89 trades on symbols that RW1 / RW5 / MF2 / RW3 / RW3S also shorted the same day (+0.057R), 259 not
  (+0.003R). RW1-FD overlap is the biggest (58). No same-setup re-entries (one per symbol-day).

## Variant grid (2 years, max(0.10R, production) costs; full table results.csv)
| cfg | n/day | avg R | t | w/o best | ex-mkt | VALID | up / down regime | vs random |
|---|---|---|---|---|---|---|---|---|
| P0 parent | 61.4 | −0.106 | −5.45 | −0.110 | −0.103 | −0.088 | −0.32 / +0.07 | +0.015 |
| M1 SPY < open | 44.0 | −0.089 | −3.22 | −0.097 | −0.105 | −0.083 | −0.42 / +0.03 | +0.031 |
| K2 M1 + after 10:30 | 45.9 | −0.092 | −3.25 | −0.100 | −0.108 | −0.086 | −0.42 / +0.03 | +0.029 |
| W2 10:30-13:00 | 40.9 | −0.099 | −4.24 | −0.104 | −0.100 | −0.075 | −0.34 / +0.10 | +0.022 |
| E1 t1.5s1 | 61.4 | −0.104 | −4.47 | −0.109 | −0.103 | −0.079 | −0.36 / +0.11 | +0.019 |
| U2 ADV ≥ $300M | 24.9 | −0.103 | −4.47 | −0.108 | −0.102 | −0.092 | −0.31 / +0.08 | +0.018 |
| E2 t0.5s1 | 61.4 | −0.119 | −9.05 | −0.122 | −0.112 | −0.107 | −0.25 / −0.01 | 0.000 |
- The other 17 (W1, W3, R1, R2, H1, H2, E3, E4, E5, M2, U1, C1, C2, G1, K1, K3, K4) score −0.103..−0.126R. None
  passes the regime gate (all lose in up sessions). Cooldown refire (C1 / C2) adds trades at the parent's rate.
  Partial / BE / time-stop exits (E3-E5) make it worse.
- Sanity: the simulated t1s1 matches the lab's r_short_t1s1 on 100% of the 26,163 parent trades. Locked block never read.

## Recommendation
- No DECISION and no near-miss. Keep RW7-FD running as is in Testing 1 as a forward record. It stays a teammate
  for down tapes, not an edge.
- What would make it viable is not a filter. It needs either (a) a real market-direction call before entry (the
  regime / QDAY work; "SPY below open so far" does not do it on 2 years), or (b) pairing it with a long
  book to cancel the beta. Both are open backlog lines, so no new idea is added. The grid is logged as a parked
  backlog entry (rw7-1103-variant-grid).
