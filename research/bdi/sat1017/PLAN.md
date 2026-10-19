# BDI Saturday deep run 2026-10-17: pre-declaration

*Educational only — not financial advice. Daily-bar backtests only (rule 7); nothing here is paper or live.*

Written before any configuration in this folder was scored. Before writing it I read the backlog notes, the earlier
study notes (W3 `research/swarm1010/w3_daily`, longhold, CWT package C `research/bdi/cwt/test_c`, saturday1010,
earnings) and checked which ETF symbols the daily file holds. No return was computed by condition.
Changes after this point go in section 9 (dated amendments) only.

## 0. What swarm1017 already did (not repeated)
swarm1017 reworked every live intraday family (MF, NS, RW, ST/L3, misc, CWT, CWT14) and ran the 6-arena indicator
search (1,054,906 configs, 0 survivors), plus Q9/Q10/Q11 follow-ups. **Locked look 1 is spent** for the L3/ST (RST1),
arena-index-etf and arena-am-long lineages. Nothing below belongs to those lineages, and nothing below is intraday.

## 1. Data, splits, costs (shared by every part)
- Daily bars: `research/swarm1010/w3_daily/data/daily_2016.parquet` (Alpaca SIP 1Day, adjusted, 2016-01-04..2026-10-09,
  1,225 symbols), loaded through `research/bdi/cwt/test_c/common.py` (R1, R2, N1, N2) or a copy of the longhold
  simulator (R3).
- Splits: train 2016-01..2022-12, valid1 2023-01..2024-10, valid2 2025-03..2026-10-09. Longhold (R3): train 2017-2020,
  valid 2021-01..2024-10, valid2 2025-03+.
- **Locked block 2024-11-01..2025-02-28 is never loaded as an outcome**: `common.py` NaNs every outcome price in it
  and drops trades whose path touches it; the R3 simulator zeroes every locked-day return and drops those days.
  `MCF_HIST_ALLOW_LOCKED` is not set. Look-back features may use prices from the block (inputs only, W3 convention).
- Costs always in: 1c/share + 1 bps per side at the auction print; shorts/hedge legs pay 3 %/yr borrow; hedge legs
  pay their own 1c + 1 bps per side.
- Survivorship: today's list applied backward (no delistings). Long results are biased up, most in train.

## 2. Gates (fixed now; daily trade families R1, R2, N1, N2 — W3 / package C gates)
1. Net expectancy > 0 in train, valid1 and valid2, n >= 100 per split (ETF family R2: n >= 20).
2. Clustered t on train+valid1 >= t_required(N_lineage) = max(1.5, sqrt(2 ln N)).
3. Valid1 clustered t >= 1.5 (ETF family R2: >= 1.0).
4. Stock long families: **excess vs the equal-weight eligible universe over the same entry/exit > 0 in train, valid1
   and valid2** (this is the flaw R1 must fix, so it is checked in all three splits, stricter than W3).
5. Regime: net expectancy > 0 in SPY-up months and SPY-down months (all open splits pooled), n >= 30 each
   (R2: n >= 15).
6. Plateau: mean net expectancy of the one-step grid neighbours (train+valid1) > 0.
7. Walk-forward share of positive months >= 0.6 (all open months).
Verdict: candidate (all) / near (exp > 0 in all three splits, a gate fails) / fail.

R3 uses the longhold gates unchanged (A1 active > 0 in train/valid/valid2, A2 monthly active t (train+valid) >=
t_required(N_lineage), A3 plateau, A4 active > 0 in SPY-up and SPY-down months).

A candidate would still need its locked look (R2: look 2, t >= 1.5; R1/R3/N1/N2: look 1, t >= 1.0), which only the lead
runs. This run never scores the locked block.

## 3. Rework R1 — CWT25 uptrend MA pullback (backlog `cwt-c-c3-ma-pullback`)
- **Single flaw:** every one of 8 configs is positive per trade in all splits (t 2.3-3.4 vs bar 2.04) but it is market
  beta: excess vs universe -22..-61 bps in valid1, down months -51..-96 bps.
- **Rework A, hedge (8):** the same 8 configs (k SMA20/SMA50 x entry close/stop x exit 2nd_sma20/k10), each trade
  hedged with beta x SPY over the same entry->exit prints (beta = 252-day daily beta vs SPY at the signal, clipped to
  [0, 3]). Net = stock net - beta x (SPY return) - beta x SPY costs - beta x SPY borrow. The hedge removes beta;
  survivors would be true timing.
- **Rework B, one condition added (8):** the same 8 configs + relative strength: 63-day stock return > 63-day SPY
  return at the signal (a stock in its own uptrend, not just riding the market). Unhedged, judged on gate 4.
- N = 16 here. Lineage: 8 (C3) + 3 (C8 gates on C3) + 4 (C9 overlays on C3) + 16 = **31, t bar 2.62**.

## 4. Rework R2 — CWT45 index down-streak (backlog `cwt-c-c7-index-streak`)
- **Single flaw:** only 3 highly correlated ETFs (SPY/QQQ/IWM), ~38 trades a year; the lead's locked look 1 had n = 12
  (+5.4 bps, t 0.13): a sample-size failure, not a sign failure.
- **Rework:** the same rule (buy the close of the Nd-th consecutive down close, sell the first up close, cap 20) on a
  wider equity-ETF set it has **never been scored on**: U_eq = DIA, XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU, XLB, XLRE,
  XLC, SMH, SOXX, XBI, IBB, KRE, KBE, XHB, ITB, XRT, XME, XOP, OIH, IYR, VNQ, EFA, EEM (28). U_all = U_eq + SPY/QQQ/IWM.
- Grid (12): Nd {2, 3, 4} x exit {upclose cap 20, upclose cap 5} x universe {U_eq, U_all}. **The decision rests on
  U_eq** (out-of-instrument replication); U_all is reported.
- Trades on the same day are correlated: t is clustered by calendar blocks of 2 x median hold (common.summ).
- Lineage: 10 (C7) + 12 = **22, t bar 2.49**. Next locked look for this lineage is look 2 (t >= 1.5), lead only.

## 5. Rework R3 — residual momentum (backlog `lh-resmom-near`)
- **Single flaw:** active t 0.69-2.23 < 3.05; the backlog note names the fix: a longer beta window (252-day betas are
  noisy, which leaks beta into the residual score).
- **Rework:** S2 res12_1 / res6_1 x top-N {10, 20, 50} x rebalance {M, W} with beta and residual sd from **756
  sessions** (min 500). Everything else as longhold S2 (MOO execution, drift between rebalances, 1c + 1 bps).
  Parity check first: the 252-day version must reproduce longhold's S2 active returns (not counted).
- N = 12. Lineage: 105 (longhold) + 18 (sat1010 crash-guard on momentum) + 12 = **135, t bar 3.13**.

## 6. New direction N1 — overnight-return persistence ("tug of war", Lou, Polk & Skouras 2019)
- Idea: a stock's past overnight returns (close -> open) reflect a persistent investor clientele; stocks with high
  recent overnight returns relative to their intraday returns keep outperforming over days to weeks.
- Signal at the close of t, eligible stocks: score = sum of the last L overnight log returns (ON) or ON minus the sum
  of the last L intraday log returns (ONID); long the top decile; enter MOO t+1; exit at the close of t+H.
  Rebalance: a new signal each Friday close only (one cohort a week, so holds do not stack beyond H/5 cohorts).
- Grid (8): L {20, 60} x feature {ON, ONID} x H {5, 20}. Long only (every short in W3 failed). N = 8, bar 2.04.

## 7. New direction N2 — high-volume return premium (Gervais, Kaniel & Mingelgrin 2001)
- Idea: an unusual volume spike without a big price move raises a stock's visibility; it outperforms over the next
  weeks.
- Signal at the close of t: V[t] / median(V[t-20..t-1]) >= k and |C[t]/C[t-1] - 1| <= a; eligible stocks; enter MOO
  t+1; exit at the close of t+H. One position per symbol at a time.
- Grid (8): k {2, 3} x a {1 %, 2 %} x H {5, 20}. Long only. N = 8, bar 2.04.

## 8. Counts
Configurations scored in this run: R1 16 + R2 12 + R3 12 + N1 8 + N2 8 = **56** (plus the R3 parity re-run, not
counted). Every row is reported in NOTES.md, failures first.

## 9. Amendments (dated)
- **2026-10-17, R3 window (after the first R3 run, before reading any other R3 number than the first table).** With a
  756-session beta (min 500) the residual score only exists from about 2017-12-27, so in 2017 the 756 book holds
  nothing while the EW benchmark earns: train active is biased down by construction. Both windows (252 parity and 756)
  are therefore also scored with train starting 2018-02-01 (`R3_TRAIN_START=2018-02-01`, `gates_resmom_from2018-02.csv`).
  Both runs are reported; the count is taken as 24 R3 scorings (lineage 147, bar 3.16) to be conservative.
- **2026-10-17, N1 adversarial checks (after the gates, written before running them; can only remove a candidate).**
  For any candidate: (a) day-clustered t of the *excess* return (train+valid1 and per split) must be >= 1.5 on
  train+valid1; (b) beta-hedged net (R1 hedge) > 0 in all three splits; (c) top-300 names by 20-day ADV: net > 0 and
  excess > 0 in all three splits; (d) 2x costs: net > 0 in all three splits; (e) excess by calendar year reported;
  (f) N1 cohorts overlap (4 weekly cohorts open at H20): t also reported with 80-session blocks.
