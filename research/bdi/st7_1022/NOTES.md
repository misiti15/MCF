# st7_1022: why ST7-rsi50dn-long-pm-t1s1-FD lost on 10-21, and can a variant earn more on up days? (owner 2026-10-22)

*Educational only - not financial advice. Backtests on the open two-year history (lab frames 2024-10..2026-10-07; the
locked block 2024-11-01..2025-02-28 was never read; no holdout was scored), costs always in (production cost,
time-of-day entry cost, x3 on the extended tier). Live = Testing 1 paper journal (run 1). TRAIN = sessions to
2025-12-31, VALID = 2026-01-01..10-07. `PLAN.md` was written and pushed before anything was scored and was not
changed. No config, setup or exit was changed (market hours).*

**Configurations scored: 60.** 42 pre-declared, 12 added after the diagnosis (H rows, flagged), 6 robustness rows.
Study bar max(1.5, sqrt(2 ln 60)) = 2.86. ST family lineage N ~227,561 (swarm1017 rework-st ~227,400 + tf1019 95 +
regime1022 6 + 60), so the lineage bar is **4.97**.

## Verdict (plain English)
1. **Yesterday (10-21) was a bad but not rare day.** ST7 bought 5 stocks between 12:36 and 13:51 that were falling
   while the market was rising. SPY and QQQ were above their VWAP at every entry (SPY +0.15% to +0.36% on the day).
   Three of the five fired in the same 13:50 bar, so it was one bet placed three times. The market then sold off from
   14:45 to 15:10 (SPY +0.40% -> +0.06%, QQQ +0.69% -> +0.25%). That pushed Z and SMR to their stops. The other three
   never got more than +0.3R in their favour and were closed at 15:55. Day total -2.45R (-$44.22 paper).
   Over 2 years, 1 in 13 of ST7's trading days is this bad (25 of 322, 7.8%), and about 1 in 4 of its days with 5 or
   more trades (28%). Bad days do not come in streaks.
2. **"Best conditions: Bull" is right as a backtest average, but 10-20 and 10-21 were not Bull days.** The chip comes
   from regime1022. That study labels each day by SPY's open-to-close move. A Bull day means SPY closed at least 0.5%
   above its open. 10-20 (+0.41%) and 10-21 (+0.25%) closed less than 0.5% from the open with a wider-than-usual
   range, so they count as **Choppy** days (a choppy up-drift, not a Bull day). On 2 years ST7's average trade earned
   +0.226R on Bull days (153 trades), the best of the four labels. On Choppy up-drift days it was even better (+0.276R,
   74 trades), and none of those 21 days was as bad as 10-21. So yesterday went against its history.
   Live, ST7 has never traded on a Bull day (16 trades: 9 Quiet, 6 Choppy, 1 Bear).
3. **The "good on down days" record only holds for 2026.** On Bear days ST7 made +0.171R per trade in 2026 (108
   trades) but lost -0.449R per trade in 2025 (138 trades), so the 2-year Bear-day average is -0.177R. Its 2025 total
   is negative too (-0.062R/trade on 371 trades); all the profit is in 2026 (+0.071R on 664 trades).
4. **What separates ST7's good trades from its bad ones is the market's position at entry, not the day's label.**
   ST7 is a dip buy. It works when the stock is falling **together with** a market dip: QQQ at or below its own VWAP
   when the signal fires. Those trades made +0.092R in 2025 and +0.141R in 2026 and are positive in every regime.
   It fails when the stock is falling **alone** while QQQ is above its VWAP: -0.211R in 2025, -0.008R in 2026, and
   -0.907R per trade on Bear days. That is the 10-21 pattern. In live paper trading the same split holds: QQQ at or
   below VWAP 5 trades +0.90R average, QQQ above VWAP 11 trades -0.10R average.
5. **"Make it more profitable on up days" does not work as asked.**
   - Requiring a strong tape is the worst idea we tested. "SPY above VWAP" gives -0.091 / -0.022R and "QQQ above
     VWAP" gives -0.211 / -0.011R; on Bear days these lose -0.78 and -0.91R per trade.
   - Letting winners run (1.5R or 2R targets, holding to the close, a trailing stop, or scaling out) adds a little on
     Bull days. Holding to the close: +0.356R vs +0.226R on Bull days. But every one of these exits loses more on Bear
     days and lowers both train and valid.
   - Earlier or later entry windows and +-10-20% changes to the thresholds also fail. None of the 42 pre-declared
     variants passes both the merit rule and the down-day guard.
6. **One variant meets your near-miss merit rule: S1 "RSI Collapse Dip Buy, Nasdaq-below-VWAP only (all day)"
   (ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD).** It is ST7 plus one rule: only when QQQ is at or below its VWAP.
   - Results: train +0.092R (183 trades), valid +0.141R (351), 2-year total +66.4R against the parent's +24.4R, on
     half the trades.
   - It beats random same-minute entries in both periods. Its worst day is -7.3R (parent -26.1R), and no single day
     is more than 15% of its total R.
   - By regime: Bull +0.654, Bear +0.059, Choppy +0.188, Quiet +0.091. It keeps the 2026 Bear-day profit (+19.8R vs
     +18.5R) and turns 2025's Bear-day losses into a small loss (-0.104R vs -0.449R).
   - Three caveats. (a) I chose this rule **after** the diagnosis had looked at both periods, so its valid numbers
     are not out-of-sample. Its t of 2.27 is far below the 4.97 bar, and a forward test in Testing is the real check.
     (b) **It gives up half of the up-day profit** (up-day total 27.8R vs 54.9R), because most up-day trades happen
     while QQQ is above VWAP. It improves ST7 in every kind of weather, not only on up days. (c) **It needs a small
     code change before it can trade.** The live engine does not yet supply QQQ's VWAP distance to lab setups;
     without it the module fires nothing (fail safe).
   - Recommendation: add it to Testing 1 as a new setup next to the parent (the parent keeps running). See the
     2026-10-22 inbox (S1 / S2).

## By-regime table (2 years; avg R per trade after costs, trades in brackets)
| row | trades train / valid | avg R train / valid | total R | t (2y) | Bull | Bear | Choppy | Choppy-up | Quiet | up-day total R | Bear avg train / valid | vs random train / valid | worst day |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **P0 parent ST7-FD (as run)** | 371 / 664 | -0.062 / +0.071 | +24.4 | 0.50 | +0.226 (153) | -0.177 (246) | +0.126 (172) | +0.276 (74) | +0.021 (457) | +54.9 | -0.449 / +0.171 | +0.006 / +0.157 | -26.1 |
| P1 windowed parent 13:35-15:00 (ref, disabled) | 73 / 93 | +0.056 / +0.245 | +26.9 | 2.02 | +0.074 (16) | +0.246 (40) | +0.219 (36) | +0.400 (14) | +0.104 (73) | +6.8 | -0.165 / +0.582 | +0.065 / +0.320 | -2.5 |
| **H1 = S1: QQQ at/below VWAP (post-diag)** | 183 / 351 | **+0.092 / +0.141** | **+66.4** | 2.27 | +0.654 (26) | +0.059 (186) | +0.188 (91) | +0.358 (30) | +0.091 (226) | +27.8 | -0.104 / +0.196 | +0.062 / +0.189 | -7.3 |
| H4: QQQ at/below VWAP or after 13:35 (post-diag) | 221 / 389 | +0.094 / +0.131 | +71.8 | 2.40 | +0.433 (42) | +0.058 (188) | +0.193 (110) | +0.372 (44) | +0.077 (264) | +34.6 | -0.107 / +0.197 | +0.066 / +0.180 | -7.3 |
| A1 SPY above VWAP (owner idea) | 149 / 313 | -0.091 / -0.022 | -20.4 | -0.77 | +0.140 (116) | -0.782 (35) | +0.107 (86) | +0.327 (50) | -0.088 (223) | +32.5 | -1.133 / +0.231 | -0.041 / +0.110 | -9.2 |
| A4 QQQ above VWAP | 188 / 314 | -0.211 / -0.011 | -43.2 | -1.19 | +0.138 (127) | -0.907 (60) | +0.056 (81) | +0.219 (44) | -0.052 (232) | +27.2 | -1.002 / -0.189 | -0.049 / +0.117 | -26.1 |
| B2 entries 12:00-15:00 | 141 / 185 | +0.029 / +0.121 | +26.4 | 1.45 | +0.187 (44) | +0.001 (75) | +0.182 (66) | +0.288 (28) | +0.035 (139) | +16.3 | -0.317 / +0.294 | +0.013 / +0.255 | -3.4 |
| A6a skip the 10:45 bar | 181 / 260 | +0.029 / +0.060 | +20.8 | 1.00 | +0.204 (65) | -0.036 (92) | +0.143 (89) | +0.296 (33) | -0.022 (192) | +23.0 | -0.291 / +0.220 | +0.015 / +0.182 | -4.3 |
| E2 max 2 entries per bar | 290 / 423 | +0.013 / +0.029 | +15.8 | 0.58 | +0.209 (112) | -0.213 (147) | +0.140 (133) | +0.342 (49) | +0.003 (316) | +40.2 | -0.313 / -0.079 | +0.038 / +0.134 | -4.8 |
| D1 target 1.5R | 371 / 664 | -0.068 / +0.051 | +8.6 | 0.17 | +0.285 (153) | -0.275 (246) | +0.101 (172) | +0.251 (74) | +0.032 (457) | +62.1 | -0.455 / -0.044 | +0.003 / +0.151 | -26.1 |
| D3 hold to close (stop 1R) | 371 / 664 | -0.097 / -0.021 | -49.7 | -0.90 | +0.356 (153) | -0.435 (246) | +0.007 (172) | +0.202 (74) | +0.002 (457) | +69.4 | -0.507 / -0.344 | +0.016 / +0.113 | -26.1 |
| F1 hold only when SPY > VWAP at entry | 371 / 664 | -0.074 / +0.067 | +16.7 | 0.32 | +0.301 (153) | -0.196 (246) | +0.049 (172) | +0.173 (74) | +0.019 (457) | +58.9 | -0.447 / +0.126 | +0.017 / +0.170 | -26.1 |
| F2 2R target only when SPY > VWAP | 371 / 664 | -0.070 / +0.072 | +21.7 | 0.43 | +0.244 (153) | -0.164 (246) | +0.081 (172) | +0.202 (74) | +0.020 (457) | +52.3 | -0.447 / +0.198 | +0.008 / +0.169 | -26.1 |

Up days = Bull + Choppy-up (SPY closed up but < +0.5% from the open, wide range). All 60 rows: `variants.csv`,
`robust.csv`.

## Failures first
- **0 of 42 pre-declared variants can be proposed.** The pre-declared test was: the merit rule (or the Testing bar),
  plus up-day average R above the parent in train and valid, plus Bear-day strength kept.
  - Two pre-declared rows pass the near-miss merit rule but fail the down-day guard. A7b "gap <= 0" (+0.187 / +0.030)
    makes -0.9R on Bear days in valid against the parent's +18.5R. E2 "max 2 entries per bar" (+0.013 / +0.029) makes
    -5.0R there.
  - None reaches the Testing bar t of 4.97. The best pre-declared t is 1.53 (A7b).
- **The owner's up-day ideas are backwards for this setup.**
  - Strong-tape filters (SPY or QQQ above VWAP, SPY up from the open) make it worse in both periods and lose
    -0.78..-1.22R per trade on Bear days.
  - Breadth rising: -0.153 / +0.112. RS vs SPY >= -2: -0.048 / +0.082.
  - All 8 exits that let winners run lower total R. Holding to the close raises the up-day total (+69.4R vs +54.9R)
    but costs -0.435R per trade on Bear days.
- **Threshold tweaks of +-10-20%** (RSI <= 24/27/33/36, fromOpen < -0.8/-0.9/-1.1/-1.2, trigger 45/55) are all
  negative in train. Looser thresholds (RSI <= 36, cross 45) lose in both periods. So the parent's numbers are not an
  isolated sweet spot, and none of these neighbours fixes 2025 either.
- **S1 (H1) was chosen after the diagnosis** looked at train and valid together. It is counted (12 H rows) but its
  valid numbers are in-sample for this choice.
  - Threshold neighbours are positive in both periods for QQQ <= -0.10 (+0.057 / +0.139) and <= -0.25
    (+0.123 / +0.117), but QQQ <= +0.10 is negative in train (-0.032).
  - Both halves of the setup hold up: the 10:45 bar +0.189 / +0.111, the other bars +0.004 / +0.188 (the train half
    there is flat).
  - 8 of 9 quarters are positive. The negative one is 2024-Q4 (-0.22).
  - Mechanism check: among the 15 long lab setups in regime1022, "QQQ below VWAP" beats "above" in both periods for
    only 5 (incl. ST7). The sister setup ST8 shows no such split. This is an ST7-specific pattern, not a market law.
- **58% of ST7's backtest trades (597 of 1,035) fire on the single 10:45 bar, and every one of them gapped up.**
  - RSI(14) on 5-minute bars still contains the overnight gap until 10:40. At 10:45 the gap bar drops out of the
    window, so a gap-up stock that has faded > 1% shows RSI collapsing from 50+ to <= 30 in one bar.
  - Live has the same artifact: signals at 10:45-10:47 on 10-12, 10-13, 10-19 and 10-20. The live mask matched the
    lab mask on every recent signal bar (`live_trades.csv`, `lab_mask_bars_today`).
  - So ST7 is really two setups: "gap-up fade at 10:45" (+0.005R, train -0.148) and "true intraday RSI collapse" (all
    other bars, +0.049R). Skipping the 10:45 bar (A6a) is not enough on its own (+0.029 / +0.060).
- **The windowed parent P1 (13:35-15:00) looks better than the full-day version** (+0.056 / +0.245, t 2.02). That
  window was chosen on the whole history in stack1009 (in-sample), its 2025 Bear days still lose (-0.165), and it
  trades about once every 2-3 days. It is disabled in config. Not proposed here.
- **Live is small.** 16 paper trades. One of them, PBF 10-12 (+3.78R), was carried overnight and closed the next day,
  so the +0.21R live average is flattered by an exit the backtest cannot make.
- **Simulator / data limits.**
  - The exits use 5-minute bars rebuilt from the 1-minute cache. The frames stop at 15:00; the simulator equals the
    frames' lab outcomes on 100% of the 1,035 P0 trades for t1s1, t05s1 and t1s05 (`parity.json`).
  - No fill slippage beyond the cost model.
  - The universe is today's list (survivorship).

## Part 0: the live trades of 10-20 and 10-21 (`live_trades.csv`, `scripts/live.py`)
All six signals match the lab mask on the same bar (parity). RS = stock fromOpen - SPY fromOpen.

| date | symbol | signal (ET) | RSI prev -> now | fromOpen | gap | RS vs SPY | SPY / QQQ vs VWAP at entry | MFE / MAE (R) during hold | exit | R |
|---|---|---|---|---|---|---|---|---|---|---|
| 10-20 | SSPC | 10:47 (10:45 bar) | 50.7 -> 21.5 | -3.10% | +2.6% | -3.83 | +0.36% / +0.58% | +0.93 / -0.10 | target 11:13 | +0.88 |
| 10-21 | RIO | 12:36 | 51.6 -> 29.6 | -1.17% | -0.3% | -1.32 | +0.19% / +0.28% | +0.91 / -0.92 | 15:55 | +0.28 |
| 10-21 | NVAX | 13:36 | 51.8 -> 29.5 | -2.15% | -0.4% | -2.48 | +0.29% / +0.37% | +0.28 / -0.38 | 15:55 | -0.37 |
| 10-21 | KTOS | 13:50 | 53.0 -> 18.6 | -1.99% | +1.6% | -2.34 | +0.30% / +0.35% | +0.30 / -0.79 | 15:55 | -0.27 |
| 10-21 | SMR | 13:51 | 60.9 -> 30.0 | -1.15% | +1.8% | -1.51 | +0.31% / +0.35% | +0.16 / -1.11 | stop 15:09 | -1.03 |
| 10-21 | Z | 13:51 | 53.7 -> 28.6 | -2.27% | -0.1% | -2.63 | +0.31% / +0.35% | +0.21 / -1.06 | stop 15:06 | -1.06 |

- **SPY / QQQ path on 10-21:** red until about 11:00, then a slow climb to SPY +0.40% / QQQ +0.69% by 14:30. A sharp
  dip followed from 14:45 to 15:10 (SPY +0.06%, QQQ +0.25%), then a partial recovery into the close (SPY +0.25%,
  QQQ +0.42%). Every ST7 entry was a stock falling while the indexes were above VWAP and rising, the weakest spot in
  the 2-year table (QQQ above VWAP: -0.211 / -0.008R). The late dip hit all five at once: the 13:50 bar's three
  entries were one correlated bet.
- **10-20 (SSPC, +0.88R)** was a 10:45-bar gap-up fade bought with QQQ above VWAP that worked. On 2 years this kind
  of trade is about break-even.
- **Is -2.45R normal?** On 2 years, 25 of ST7's 322 trading days (7.8%) closed at -2.47R or worse; on days with 5 or
  more trades it was 28%. On Choppy up-drift days it never happened (0 of 21; median Choppy-up day +0.97R); on Bull
  days once in 59. P(bad day | previous trading day bad) = 4% vs 7.8% base: no streaks. So it is a normal-sized loss
  for this setup, but on an unusual kind of day for it.
- **S1 (QQQ at/below VWAP) on the live record:** it would have skipped all six trades of 10-20/10-21 (QQQ +0.27..+0.64%
  above VWAP). Over all 16 live trades it keeps 5 (+0.90R average, +$51.23) and skips 11 (-0.10R average, -$21.81)
  (`live_h1.csv`). Sixteen trades are not evidence.

## Part 1: 2-year diagnosis of the parent (`diag.csv`, `days.csv`; train / valid avg R, random same-minute longs as baseline)
- **Regime:** Bull +0.385 / +0.114; Bear -0.449 / +0.171; Choppy +0.531 / +0.007 (Choppy-up +0.778 / +0.148,
  Choppy-down +0.377 / -0.105); Quiet -0.064 / +0.053. Random longs: Bull +0.159, Bear -0.280, Choppy +0.005,
  Quiet -0.091. ST7 beats random by about +0.07 on Bull days and +0.10 on Bear days. Its regime profile is mostly
  the market's own drift.
- **Time of day:**
  | window | trades | 2-year avg R | t |
  |---|---|---|---|
  | 10:45 bar | 597 | +0.005 | |
  | 10:50-11:55 | 105 | -0.079 | |
  | 12:00-13:30 | 159 | -0.009 | |
  | 13:35-15:00 | 164 | +0.173 | 2.16 |
  | 09:50-10:40 | 10 | | |
- **Market at entry:**
  | condition | 2-year avg R | t |
  |---|---|---|
  | QQQ <= VWAP | +0.124 | 2.27 |
  | QQQ > VWAP | -0.084 | |
  | SPY <= VWAP | +0.076 | |
  | SPY > VWAP | -0.042 | |
  | SPY down from open | +0.031 | |
  | SPY up from open | +0.013 | |
  | breadth rising | +0.032 | |
  | breadth falling | +0.020 | |
- **Stock at entry:**
  - buyPressure > 0.25: +0.160 (t 2.56; train +0.093 / valid +0.196). A post-diagnosis row; its 2025 Bear days still
    lose.
  - gap <= -1%: +0.215 (77 trades). Gap > 3%: +0.012, with train -0.261.
  - RSI < 20: +0.085. RSI 20-25: -0.036. RSI 25-30: +0.038.
  - RS vs SPY: no clear order. RS < -4 +0.110, -4..-3 -0.088, RS >= -2 +0.036.
  - Daily ATR% < 3: +0.058, the best of the three ATR% buckets.
- **Crowding:**
  - Entries #4 and later of a day are worse in train (#4-6 -0.207, #7+ -0.308) but positive in valid.
  - 3 or more signals in the same bar: -0.175 in train, +0.112 in valid.
  - Neither is consistent across periods. The caps E1-E3 fail.
- **Re-entries:** none. Refire is off, so there is one signal per symbol-day; a one-lot-per-symbol rule or a cooldown
  changes nothing and was not counted.

## Part 2: grid (all rows `variants.csv`; robustness `robust.csv`)
Scored on P0's signals with the same simulator and costs. Entry filters are applied inside the mask, then the first
signal per symbol-day is taken.
- **A filters.**
  - A1 SPY above VWAP -0.091 / -0.022. A2 SPY up from open +0.057 / -0.011. A3 breadth rising -0.153 / +0.112.
    A4 QQQ above VWAP -0.211 / -0.011.
  - A5 RS >= -2: -0.048 / +0.082. RS >= -3: -0.073 / +0.080.
  - A6 skip the 10:45 bar: +0.029 / +0.060. Only the 10:45 bar: -0.148 / +0.077.
  - A7 gap > 0: -0.129 / +0.080. Gap <= 0: +0.187 / +0.030.
- **B windows.** 09:50-12:00: -0.118 / +0.052. 12:00-15:00: +0.029 / +0.121. 09:50-11:00: -0.149 / +0.066.
- **C thresholds.** All are negative in train, from -0.004 (RSI <= 24) to -0.134 (cross 55).
- **D exits** (train / valid):
  | exit | avg R train / valid |
  |---|---|
  | t1.5s1 | -0.068 / +0.051 |
  | t2s1 | -0.100 / -0.001 |
  | hold to close | -0.097 / -0.021 |
  | 1R trail | -0.125 / -0.020 |
  | 2R target, break-even after +1R | -0.104 / +0.000 |
  | half at +1R, rest held | -0.090 / +0.025 |
  | t05s1 | -0.074 / +0.049 |
  | t1s05 | -0.087 / -0.023 |
- **E crowding caps.** Max 1 per bar: -0.016 / +0.000. Max 2 per bar: +0.013 / +0.029. Max 5 per day: -0.018 / +0.056.
- **F tape-conditional exits.** Hold only when SPY is above VWAP: -0.074 / +0.067. 2R only when SPY is above VWAP:
  -0.070 / +0.072.
- **G pairs**, picked on TRAIN: entries A2, A6a, B2 x exits D1, F2. Best pair: B2 + F2, +0.010 / +0.094, Bear valid
  +11.5R (75% of the parent's is 13.9R). All fail the guard.
- **H rows, post-diagnosis.**
  | row | avg R train / valid | t |
  |---|---|---|
  | H1 QQQ <= VWAP | +0.092 / +0.141 | 2.27 |
  | H2 SPY <= VWAP | -0.042 / +0.150 | |
  | H3 buyPressure > 0.25 | +0.093 / +0.200 | 2.61 |
  | H4 QQQ <= VWAP or after 13:35 | +0.094 / +0.131 | 2.40 |
  - H1, H3 and H4 meet the merit rule.
  - H3 fails the up-day / Bear guard.
  - H1 and H4 pass it. H1 is proposed because it is a single layer. H4 adds a second rule (after 13:35 any tape) for
    14% more trades (610 vs 534) at a lower Bull-day average.

## Files
`PLAN.md`, `scripts/` (scan, paths, core simulator, parity, diag, variants, robust, live, live_h1, verify_module),
`parity.json`, `diag.csv`, `days.csv`, `variants.csv`, `robust.csv`, `mechanism_longs.csv`, `live_trades.csv`,
`live_h1.csv`, `counts.json`, `verify.json` (module = scan on 534/534 H1 and 1,035/1,035 P0 signals; fail-safe 0
signals without `qqq_vwap`), `modules/ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD.py`, `backlog_proposals.jsonl`.
