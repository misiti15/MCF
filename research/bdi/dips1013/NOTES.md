# Oversold-turn longs (A) and open-dip longs (B) (BDI, owner request 2026-10-13)

*Educational only - not financial advice. These are backtests on the open two-year history (426 sessions,
2024-10..2026-10-07, 386,047 eligible symbol-days with adv20 >= $95M), with production costs in, including the
time-of-day entry multiplier: x2.1 at 09:45 and x1.4 from 09:50 to 10:25.*
- Nothing here is paper or live.
- The rule-19 locked block was never loaded, and no holdout was scored.
- The grid was pre-declared in `PLAN.md` before scoring. Amendment A1 (plateau neighbours) was written before
  scoring.

**Configurations scored: 80,187**, which is exactly the declared N.

| | configurations | try-count bar |
|---|---|---|
| Part A | 9,600 + 20 random controls = 9,620 | 4.28 (lineage `dips1013-ost`) |
| Part B | 70,560 + 7 random controls = 70,567 | 4.80 (lineage + longs1013-flush 31,454 = 102,021) |
| Study | 80,187 | 4.75 |

## Failures first
- **0 of 80,187 configurations pass the research gate.**
  - No configuration with n >= 150 reaches the study t bar on absolute expectancy. The best has open t 2.03.
  - `gates.verdict` returns "keep" for 0 of 26 finalists.
- **0 of 26 finalists clear the pre-declared Testing-1 bar.** So no LabStrategy module was built, and nothing is
  proposed for Testing 1.
  - Two finalists, the same trade set under two names, clear every criterion except runnability. They are covered
    below.
- **Part A: oversold, then a turn up, has no edge, absolute or relative.**
  - The median open expectancy is -0.094R, against -0.075R to -0.108R for random longs in the same windows.
  - The median excess over random longs at the same minute is -0.007R.
  - Only 142 of 9,190 configurations with n >= 150 are positive.
  - Every oversold family and every turn trigger sits at -0.07 to -0.13R.
  - Waiting for the turn adds nothing:

    | trigger | median R |
    |---|---|
    | PBH | -0.091 |
    | HL | -0.091 |
    | EMAR | -0.094 |
    | VWR | -0.097 |
    | RSIX | -0.098 |
- **Part B: a big dip at the open, then long, loses after costs.**
  - The median open expectancy is -0.096R. The random 09:45-10:15 long loses -0.096 to -0.117R.
  - The dip-only lines (filter none, gap any) are negative on every capped exit:
    - 0.75% below the open, entered at 09:50: t1s1 -0.084R (n 74,550, 175 a day), SL-VWAP -0.083R;
    - 2% below the open: t1s1 -0.119R.
  - Deeper dips are not better: the median is -0.10R at 0.75%, 1.0%, 1.5% and 2.0%.
  - The only positive dip-only lines are hold-to-close lines measured from the prior close. These are beta:
    - PC 2% at 09:45, HTC: +0.075R, t 0.57, **up sessions +1.14 / down sessions -0.85**, excess t 1.51.
- **The "support" filters do not stop the further drop.**
  - Median open R by filter:

    | filter | median R |
    |---|---|
    | capd | -0.073 |
    | C3 | -0.079 |
    | qqqmid | -0.085 |
    | none | -0.086 |
    | spymid | -0.090 |
    | idio | -0.090 |
    | spyup | -0.092 |
    | trend | -0.093 |
    | sect | -0.099 |
    | spynl | -0.101 |
    | capr | -0.103 |
    | vix | -0.104 |
    | pcl | -0.108 |
    | C1 | -0.117 |
    | C4 | -0.146 |
  - Market support (SPY or QQQ holding, VIX calm, sector not weaker) changes the sign of nothing.
  - Neither gap class helps:

    | gap class | median R |
    |---|---|
    | gap-and-fade (gup) | -0.119 |
    | open-then-flush (flat) | -0.087 |
    | gap-down (gdn) | -0.083 |
- **The positive absolute numbers are market beta again,** as longs1013 found.
  - Every finalist with open exp > +0.1R is a hold-to-close or wide-stop line, positive in up sessions and negative
    or about 0 in down sessions.
  - B gdn-VR-spyup HTC: up +0.61 / down -0.99.

## What is real: a relative (not absolute) reversion right after 09:45
- Stocks down >= 0.75-1% from the open at the 09:45 close beat a random long entered at the same minute.
  - B-B-p0.75-any-E945-capd-t1s05 (capd = opening-volume climax that is now fading):
    - excess +0.055R, t 5.42;
    - train t 4.54, valid t 3.37;
    - up +0.058 / down +0.064.
  - It survives a next-bar-open entry: excess +0.046R, t 4.59.
  - 14 configurations clear the study bar of 4.75 on excess. All are E945 dip lines or Part A streak-HL-pm lines,
    and all are listed in `summary.json`.
- **It is still not tradable.**
  - Absolute expectancy is -0.048R (t -2.45) at t1s05 and -0.013R at t1s1, because the open's spread costs (x2.1)
    exceed a +0.04-0.08R relative edge.
  - It decays within one bar. Entered at the 09:50 close, the same dip line's excess falls to +0.022R (t 2.47), and
    to +0.008R with no filter.
  - Part A's streak-HL-pm excess (+0.014R, t 7.3, n 188k) is economically tiny. Absolute: -0.086R.
- Backlog idea (not tested here):
  - A market-hedged version (long the 09:45 dip, short SPY beta) would keep the relative edge but pay a second
    spread.
  - At about +0.05R gross relative against about 0.10R in round-trip costs at 09:45, it is unlikely to clear costs.
  - Listed for the backlog owner. Not added to `research/backlog.jsonl` by this study.

## Finalists (every one, PLAN section 4)
How to read the table:
- R = 0.25 x daily ATR, production costs in.
- "excess" is the edge over a random long at the same minute.
- up / down = universe up / down sessions.
- B-O and B-B rows inside the gdn class are the same trades, because a gap-down makes the prior-close condition
  redundant. They are shown once.

| config | train n / exp / t | valid n / exp / t | open n / exp / t | excess (t) | up / down exp | up / down excess | WF | plateau | next-open exp | fails |
|---|---|---|---|---|---|---|---|---|---|---|
| A-vwap-1.0-L3-RSIX-none-pm-t05s1 | 870 / +0.071 / 1.33 | 453 / -0.095 / -2.08 | 1323 / +0.014 / 0.31 | -0.021 (-0.70) | -0.04 / +0.04 | -0.10 / +0.01 | 0.44 | -0.037 | +0.014 | t, valid, excess, ex-best, busiest, plateau |
| A-bb-2.5-L1-EMAR-none-mid-HTC | 451 / +0.210 / 1.26 | 328 / -0.022 / -0.26 | 779 / +0.112 / 1.06 | +0.055 (0.84) | +0.44 / -0.33 | +0.02 / +0.02 | 0.69 | -0.013 | +0.124 | t, valid, excess, plateau, runnable |
| A-vwap-1.0-L3-RSIX-pcl-pm-t05s1 | 465 / +0.058 / 1.15 | 233 / -0.198 / -2.98 | 698 / -0.027 / -0.58 | -0.040 (-1.07) | -0.06 / -0.02 | -0.10 / -0.02 | 0.27 | -0.059 | -0.020 | exp, t, valid, excess, ex-best, plateau |
| A-vwap-1.0-L1-RSIX-none-am-SW-VWAP | 168 / +0.277 / 1.13 | 70 / +0.545 / 0.89 | 238 / +0.356 / 1.43 | +0.406 (1.84) | +0.19 / +0.52 | +0.33 / +0.49 | 0.33 | -0.023 | +0.390 | t, busiest 13%, plateau |
| A-dfh-1.5-L1-VWR-spynl-pm-t1s1 | 646 / +0.244 / 1.12 | 424 / +0.034 / 0.49 | 1070 / +0.161 / 1.05 | +0.052 (1.37) | +0.47 / -0.19 | +0.05 / +0.05 | 0.56 | +0.043 | +0.181 | t, ex-best, busiest, runnable |
| A-dfh-1.5-L3-VWR-spynl-pm-t1s1 | 860 / +0.250 / 1.11 | 532 / +0.050 / 0.83 | 1392 / +0.174 / 1.09 | +0.075 (2.23) | +0.50 / -0.18 | +0.08 / +0.07 | 0.63 | +0.013 | +0.194 | t, ex-best, busiest, runnable |
| A-vwap-1.0-L1-RSIX-none-pm-t05s1 | 730 / +0.061 / 1.10 | 373 / -0.105 / -2.27 | 1103 / +0.005 / 0.11 | -0.036 (-1.11) | -0.02 / +0.04 | -0.07 / -0.01 | 0.25 | -0.028 | +0.009 | t, valid, excess, ex-best, busiest, plateau |
| A-dfh-1.5-L3-VWR-none-pm-t1s1 | 877 / +0.244 / 1.10 | 543 / +0.041 / 0.70 | 1420 / +0.166 / 1.06 | +0.069 (2.07) | +0.50 / -0.18 | +0.08 / +0.06 | 0.44 | +0.014 | +0.188 | t, ex-best, busiest |
| A-vwap-1.0-L1-RSIX-none-pm-t1s05 | 730 / +0.060 / 1.09 | 373 / -0.025 / -0.51 | 1103 / +0.031 / 0.73 | +0.054 (1.10) | -0.09 / +0.06 | -0.12 / +0.11 | 0.44 | -0.066 | +0.038 | t, valid, excess, busiest, plateau |
| A-dfh-1.5-L1-VWR-none-pm-t1s1 | 663 / +0.234 / 1.08 | 432 / +0.021 / 0.32 | 1095 / +0.150 / 0.99 | +0.044 (1.18) | +0.47 / -0.19 | +0.05 / +0.04 | 0.56 | +0.045 | +0.173 | t, ex-best, busiest |
| A-vwap-1.0-L3-PBH-none-pm-t05s1 | 871 / +0.046 / 0.82 | 542 / -0.000 / -0.00 | 1413 / +0.028 / 0.61 | -0.018 (-0.50) | -0.14 / +0.06 | -0.23 / +0.03 | 0.31 | -0.031 | +0.031 | t, valid, excess, busiest, plateau |
| A-vwap-1.0-L1-HL-none-pm-t1s1 | 800 / +0.050 / 0.57 | 454 / +0.095 / 1.21 | 1254 / +0.066 / 1.08 | +0.040 (0.65) | -0.11 / +0.08 | -0.26 / +0.11 | 0.50 | -0.031 | +0.050 | t, busiest, plateau |
| B-O-a0.5-gdn-VR-spyup-SL-VWAP (= B-B) | 324 / +0.501 / 3.62 | 352 / -0.218 / -1.50 | 676 / +0.127 / 0.96 | +0.057 (0.61) | +0.36 / -0.75 | +0.01 / -0.25 | 0.40 | -0.011 | +0.115 | t, valid, excess, busiest, plateau, runnable |
| B-O-a0.5-gdn-VR-spyup-SL-HTC (= B-B) | 324 / +0.501 / 3.62 | 352 / -0.218 / -1.50 | 676 / +0.127 / 0.96 | +0.046 (0.49) | +0.36 / -0.75 | -0.05 / -0.14 | 0.40 | -0.029 | +0.132 | as above |
| B-O-a0.5-gdn-VR-spyup-HTC (= B-B) | 324 / +0.635 / 3.25 | 352 / -0.164 / -1.01 | 676 / +0.219 / 1.33 | +0.049 (0.44) | +0.61 / -0.99 | +0.03 / -0.14 | 0.53 | -0.063 | +0.225 | as above |
| **B-O-a0.75-gdn-E945-trend-HTC (= B-B)** | 203 / +0.815 / 3.01 | 277 / +0.101 / 0.38 | 480 / +0.403 / 2.03 | +0.378 (2.29) | +1.48 / -0.14 | +0.62 / +0.46 | 0.69 | +0.306 | +0.396 | **runnable only** |
| B-O-a0.5-gdn-VR-trend-HTC (= B-B) | 247 / +0.704 / 2.79 | 374 / -0.440 / -2.14 | 621 / +0.015 / 0.07 | -0.074 (-0.54) | +0.51 / -0.40 | -0.18 / -0.05 | 0.57 | +0.141 | +0.012 | t, valid, excess, ex-best, busiest, runnable |
| B-B-a0.75-gdn-PBH-trend-HTC | 167 / +0.757 / 2.53 | 226 / -0.177 / -0.79 | 393 / +0.220 / 0.99 | +0.078 (0.53) | +0.85 / +0.00 | +0.04 / +0.21 | 0.50 | +0.069 | +0.226 | t, valid, excess, busiest, runnable |
| B-B-a0.75-gdn-E955-trend-HTC | 213 / +0.840 / 2.52 | 342 / +0.120 / 0.38 | 555 / +0.396 / 1.61 | +0.294 (1.84) | +1.32 / +0.05 | +0.44 / +0.43 | 0.54 | +0.213 | +0.393 | busiest 10.4%, runnable |
| B-B-a0.75-gdn-E950-trend-HTC | 213 / +0.891 / 2.50 | 342 / +0.127 / 0.42 | 555 / +0.421 / 1.70 | +0.323 (1.84) | +1.38 / +0.04 | +0.47 / +0.45 | 0.62 | +0.249 | +0.417 | busiest 10.4%, runnable |
| B-B-a1.0-gdn-HL-capd-SL-VWAP | 158 / +0.392 / 2.10 | 94 / -0.058 / -0.20 | 252 / +0.224 / 1.38 | +0.297 (2.00) | +0.81 / -0.09 | +0.46 / +0.18 | 0.67 | -0.056 | +0.203 | t, valid, plateau |

### The near-miss: B-O-a0.75-gdn-E945-trend-HTC (not proposed)
The setup:
- the stock gapped down 1% or more;
- it is still 0.75 ATR or more below the open at 09:45;
- its prior close was above its daily SMA20 and SMA50;
- buy at the 09:45 close and hold to 15:55 with no stop.

It clears every Testing-1 criterion except runnability. It is still not proposed:
1. **It is not runnable in LabStrategy.**
   - The window floor is 09:50.
   - The frame carries neither daily SMA20 nor SMA50 (DayContext has `sma20` only).
   - Running it needs an mcf/ hook, which this study does not make.
2. **The runnable 09:50 / 09:55 versions fail the pre-declared busiest-session test** (10.4% > 10%), and they still
   need the trend hook.
3. **The evidence is weak.**
   - Valid is +0.10R with t 0.38. Train carries it (t 3.0).
   - It is about 1.1 trades a day.
   - Its open t of 2.03 is far below the lineage bar of 4.80, and it is the maximum of 70,567 tries.
   - The positive excess in both up (+0.62) and down (+0.46) sessions is the one encouraging number.
   - It is the same family (gap-down, uptrend, hold) as longs1013's beta finalists.

If the lead wants it, the minimal hook request is: `window` floors below 950 for lab setups, plus `sma20`/`sma50` in
the frame. It would then go to Testing 1 as an experimental tag. **My recommendation is not to build the hook for
this evidence.**

## Proposed Testing 1 additions
**None.** No configuration clears the pre-declared bar, so `live/` was not created and no config entry is proposed.

## Files
- `PLAN.md`: the pre-declaration and amendment A1.
- `prep.py`: builds 5-minute bar arrays from the 1-minute cache, with the locked block dropped at read.
  - Parity with the frames: close exact on 100% of rows; VWAP distance p99 |diff| 1e-5; open p99 rel diff 5e-8.
  - Also produces the day table and the market / sector / VXX context from indexlink's ETF array.
- `engine.py`: the exit simulator, the costs, the same-minute control and fast statistics.
  - On t1s1 it matches the lab outcome exactly on 98% of trades.
  - The rest differ because a bar that opens through the stop fills at its open, which is stricter.
- `features.py` and `configs.py`: the grids.
- `score.py` writes `results.csv` (every configuration) and `counts.json`.
- `report.py` writes `finalists.csv` and `summary.json`.
- `data/` is git-ignored.
