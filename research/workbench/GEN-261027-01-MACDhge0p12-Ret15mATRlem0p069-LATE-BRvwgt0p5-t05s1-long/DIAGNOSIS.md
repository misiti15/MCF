# Diagnosis — Generated: Late Pullback Buy (MACD rising) `GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long` (Testing E; LONG)
Educational only — not financial advice. Mechanic, 2026-11-16 (Workbench batch; built during and after market hours:
research files only, no config touched, nothing deployed).

Engine: `..._engine.png` (P1..P26, blueprint `GEN-261027-01-...-long.md`). The setup buys the first 5-minute bar
closing 14:00-15:00 where the stock's MACD histogram is rising (macd_hist >= 0.12) right after a 15-minute dip
(ret3_atr <= -0.069 daily ATR), while more than half the market is above VWAP (breadth > 0.5); target +0.5R, stop 1R,
1R = 0.25 x daily ATR, flat 15:55.

**Few live trades (16 in 6 sessions; only 4 losers): this job leans on the 2-year backtest (5,018 parent trades,
277 sessions) and says so.** The live trades point at parts; they decide nothing. The parent's live record is not used
in the pass decision (owner 2026-11-16).

Rule-change context inside the live window (research/ledger.jsonl): 14 of the 16 live trades are from the Setup
Generator account (10-27..11-10: $510 lots, no cost filter, account limits that blocked 40 of its signals); the setup
moved to Testing E on 2026-11-12 (GEN-GRAD, 2 trades since). Also from 11-12: Gen buying power 3.8 -> 1.8 / slots 200 ->
300 (REPV-1), LR1 (flatten at min(15:55, close - 5 min)), LR5 (position check), LR8 cost allowance (live R before
11-12 uses the older allowance). The backtests below use LR8 costs throughout, so they are not mixed.

## The 5 worst and 5 best live trades (16 trades: only 4 losers, so worst5 includes the +0.09R AVL flatten)
Sensor values recomputed from SIP bars with the module's own indicator code (lab frame pipeline; 8 of the 16 symbols
are outside the 1,226-name lab universe and were rebuilt from a read-only SIP fetch). br_chg = breadth at the signal bar
minus breadth at the 09:50 bar. W = window 14:00-14:30 (WB1), A = ADV >= $100M (WB2), B = br_chg <= +0.20 (WB3).

| Trade (chart) | What happened | Part behind it | Catalogue part | What a small tweak does to THIS trade |
|---|---|---|---|---|
| worst1 NYT 10-28 −1.12R (`_worst1_NYT_2026-10-28.png`) | 14:00 signal right after a vertical +1% run 13:30-13:50 (ret12 +1.0%, ADX(7) 83, low daily ATR 2.3%); MFE +0.32R at 14:36 (1 tick short of the target), then slid to the P23 stop 14:57 | P9/P10 fire on the first dip after a spike; P20 1R thin (0.47 on a $69 stock) | Sensors / Stop | All copies KEEP it (14:00, ADV $104M, br_chg +0.07). No single part fixes it; target 0.4R would have filled (+0.4R) but target 0.4R fails over 2 years |
| worst2 ZYME 10-27 −0.76R (`_worst2_ZYME_2026-10-27.png`) | 14:00 signal at the top of the day (day_pos 0.90, +0.74 ATR from the open), ADV only $15M; drifted down, flattened 15:55 | P2 liquidity floor; market had already broadened +0.22 since 09:50 | Intake / Gates | WB2 (ADV $15M < $100M) and WB3 (br_chg 0.22) both skip it → +0.76R |
| worst3 SMCIP 11-13 −0.16R | 14:55 signal, ADV $8.9M (live universe, extended tier), never above entry; flatten | P5 late window; P2 | Timer / Intake | WB1 (14:55 > 14:30) and WB2 skip it → +0.16R |
| worst4 GUSH 10-27 −0.12R | 14:30 signal, ADV $21M, MAE −0.69R, flatten | P2; breadth +0.20 since 09:50 | Intake / Gates | WB2 skips it; WB3 skips it (br_chg 0.202) |
| worst5 AVL 11-06 +0.09R | 14:30 signal, ADV $21M; MFE +0.65R (past the target) but the target did not fill; flatten | P24 (fill) | Target | WB2 skips it (−0.09R) |
| best1 TTD 10-28 +1.05R (`_best1_TTD_2026-10-28.png`) | 14:50 signal; filled 28 bps BELOW the signal close, so the +0.5R target (set from the signal close) became +1.05R on the fill | works — R doubled by favourable fill drift | — | WB1 MISSES it (14:50) |
| best2 CBRS 10-28 +1.02R | 14:55 signal; filled 58 bps below the signal close (same effect); target 15:20 | works (fill drift) | — | WB1 MISSES it |
| best3 BLMN 10-27 +0.50R | 14:25, ADV $19M; target in 6 min | works | — | WB2 / WB3 miss it |
| best4 AGLT 11-10 +0.45R | 14:30, ADV $44M; target 15:29 | works | — | WB2 misses it; WB1 / WB3 keep it |
| best5 INOD 10-27 +0.43R | 14:00, at the low of the day; target in 3 min | works | — | WB2 / WB3 miss it |

**Live read:** the two big losers came from two different parts (a spike-top pullback that P9/P10 treat like any other,
and a thin $15M name on an already-broad afternoon). On the 16 live trades the parts disagree with the backtests:
W keeps 10 at +0.056R and drops 6 at +0.405R (the two late winners TTD / CBRS were doubled by fill drift); A keeps 7 at
+0.309R vs 9 at +0.092R (agrees); B keeps 10 at +0.247R vs 6 at +0.088R (agrees); WB5 (W+A+B) keeps only 3 (NYT, GDXU,
GDXJ: −0.13R avg) and skips 13 at +0.26R. **16 trades decide nothing** — hence the 2-year test (5,018 trades) and the
replay of all 14 live-window sessions on the lab universe (83 trades).

## All trades, component by component (2-year backtest, parent, 1-minute engine, costs in; train ..2025-12 / valid 2026-01..10-26)
Parent: 5,018 trades, win 67.8%, avg +0.032R (train +0.051, valid +0.008), w/o best day +0.002R, worst day −75R,
**best day = 93% of total R** (2025-04-09 +151R; 2025-04-10 +141R; April 2025 = 35% of all trades). Without April
2025: +0.001R. With a 20-trades-per-day cap (a rough stand-in for live lot / account caps): **−0.050R**. The record is
carried by a handful of crash/rally days. Exits: target 66% (+0.45R), stop 20% (−1.14R; 36% of stops first reached
+0.3R), 15:55 flatten 14% (−0.23R, median hold 79 min). Median hold 17 min.

| Part | What the 2-year trades say (avg R by bucket; train / valid) | Verdict |
|---|---|---|
| P1 / P2 intake: liquidity floor $20M | ADV < $50M −0.019 (−0.03 / +0.01); $50-100M −0.007 (+0.03 / **−0.07**); $100-300M **+0.063** (both +); > $300M +0.027 | **tweak: ADV >= $100M (WB2)** |
| P3 price floor $5 | $10-30 −0.022 (valid −0.07); > $30 +0.04; price >= $10 alone changes nothing (20 trades < $10) | keep |
| P4 earnings blackout | not testable here (the earnings calendar file is not on this machine; the generator's screen had it) — same for parent and copies | keep (note) |
| P5/P6 window 14:00-15:00 | 14:00-14:10 −0.013 (−0.09 / +0.08); 14:10-14:20 **+0.201**; 14:20-14:30 **+0.120**; 14:30-14:40 **−0.170** (−0.06 / −0.25); 14:40-14:50 −0.005; 14:50-15:00 **−0.121** (−0.07 / −0.16). The last 30 minutes lose in both halves | **tweak: end 14:30 (WB1)** |
| P7 no entry before 09:50 | not binding (window 14:00) | keep |
| P8 refire off | first bar per symbol-day | keep |
| P9 macd_hist >= 0.12 | rises with the threshold in train (−0.03 → +0.15), flat in valid; 0.15 / 0.20 better over 2 years but the replay falls (+0.097 / +0.056) | keep |
| P10 ret3_atr <= −0.069 | deeper dips a little better (−0.08 / −0.10 thresholds: 2y +0.040 / +0.057) but the replay falls (+0.079 / +0.089) | keep |
| P11 breadth > 0.5 | needed: no gate 2y −0.009 (worst day −243R); 0.4 +0.005; 0.6 +0.014. Inside the gate: 0.6-0.8 negative | keep |
| P11b (new) breadth change since 09:50 | ≤ 0 +0.002; 0-0.1 **+0.119**; 0.1-0.2 **+0.057**; **0.2-0.3 −0.203** (stops 37%; −0.27 / −0.09); > 0.3 +0.143 (train +0.21 = 2025-04-09; valid −0.03). In valid, every bucket above +0.20 is negative | **new gate: ≤ +0.20 (WB3)** |
| P12 market context | SPY since 09:50: no clean split (> +1.2%: train +0.08 / valid −0.29); SPY >= −0.3% gate fails | no change |
| P13-P16 caps / latch / account stop | not modelled in the isolated engine (identical for all); a 20-trades/day cap is reported as a sensitivity | no change |
| P17 cost filter 0.15R | 0.10: 2y +0.047 but replay w/o best day falls (+0.096 vs +0.127); none: 2y +0.012 | keep 0.15 |
| P18 quote / spread checks | live only (23% of live signals blocked) | no change |
| P19 entry at market | fill = open 1 min after the bar close; live fills drifted (TTD / CBRS) | no change |
| P20 1R 0.25 ATR | 0.20: 2y +0.007; 0.30: +0.018 | keep |
| P23 stop 1R | 0.75R: 2y +0.047 but valid −0.042; 1.25R +0.037 (replay +0.109); 1.5R +0.031 | keep |
| P24 target 0.5R | 0.4R +0.031; 0.6R +0.026 (worst day −135R); 0.75R +0.009 | keep |
| P26 flat 15:55 | max hold 30 +0.013 / 60 +0.014; flat 15:30 +0.022; BE at +0.3R +0.034 (valid −0.023); exit at 30 min if MFE < 0.2R +0.015 | keep |
| Sensors not in the setup | SMA20 slope < 0.25 −0.163 / −0.088 (both halves; slope >= 0.25 2y +0.089) but the replay w/o best day falls to +0.073; daily ATR < 3.5% −0.045 (both halves); below VWAP by > 0.17 ATR −0.107 (both); day position < 0.27 −0.086 (both); > 1.08 ATR under the high −0.085 (both) | tested as layers (screen_e1.csv); none beat the chosen parts in BOTH tests |

**Most responsible for the losses:** time and market state, not the exit. Trades after 14:30 (1,432 of 5,018) average
−0.10R and the 0.2-0.3 breadth-expansion afternoons (1,002 trades) −0.20R with 37% stops; together they hold most of the
parent's losing days (2025-04-07 −75R, 04-04 −71R, 2026-01-30 −30R, 05-21 −17R). The exits are fine for a 0.5R / 1R
trade: no stop / target / time-exit tweak beats the parent in both tests.

## Candidate tweaks (one part each) → copies
- **WB1** P5 window end 15:00 → 14:30.
- **WB2** P2 liquidity floor $20M → $100M.
- **WB3** new gate P11b: skip when breadth has risen more than +0.20 since the 09:50 bar (market state measured after
  09:50, owner rule).
- **WB4** = WB1 + WB3; **WB5** = WB1 + WB2 + WB3 (combos, each part passed alone).

Results and the sign-off: RESULTS.md. Educational only — not financial advice.
