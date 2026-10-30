# pdl1030c / ind3: one added indicator (RSI(5), index context) on the two demoted PDL longs

*Educational only — not financial advice.* These are backtests on the open two-year history. Nothing here was traded on paper or live.

**Result: 0 of 14 pre-declared configurations pass.** No row was added after scoring, and no module was written.
- Lineage CWT14 PDL: N = 121,635 + 5 x 14 = 121,705. The BAR90 bar is t >= 4.355.
- Data: TRAIN = 2024-10 and 2025-03..12. VALID = 2026-01..03 and 2026-07..09-15, 348 sessions in all.
  The HOLD months and the locked block were never loaded (asserts in build.py and score.py).
- **Every row loses money over TRAIN+VALID combined, and no row reaches t > 0.** Because total R is negative, the best-day and
  top-5-day shares are undefined. The "w/o" columns are still reported.
- Parity is exact.
  - p05: -0.0677 / -0.0675, n 53,326, 153.2/session.
  - p05-lowvol: -0.0951 / -0.0948, TV -0.0950, n 35,238, 101.3/session.
  - p05 S3: -0.0210 / -0.0173.
- Data limit, disclosed in PLAN.md before scoring: the 09:35-09:45 head rows carry no rsi5. R1 and R2 therefore cannot
  fire on the earliest signals (09:50, and for R1 also 09:55-10:00).

## Overlap skipped (already scored in earlier swarms)
- SPY fromOpen up/down (tape-flip TA).
- SPY vs VWAP (tape-flip TB, combo K1/K3/K6, regime-day C1).
- SPY gap (combo, regime-day).
- SPY/QQQ hedges (pdl1030b).
- Stock fromOpen vs SPY fromOpen (symbol-quality Q02/Q06/Q11/Q14). This also covers RWN5.

## Every row (avg R after costs; t is day-clustered over TRAIN+VALID)
| id | added indicator (exits) | TRAIN | VALID | t | /sess | % parent kept | WF% | up-day | down-day | w/o best day | w/o top-5 days |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1-p05 | rsi5 <= 20 at the poke (parent) | -0.0721 | -0.0798 | -8.05 | 60.7 | 39.6 | 12 | -0.003 | -0.131 | -0.076 | -0.081 |
| R2-p05 | rsi5 crosses above 20 on the reclaim bar (parent) | -0.0635 | -0.0639 | -7.06 | 41.3 | 26.9 | 12 | +0.001 | -0.118 | -0.065 | -0.070 |
| R3-p05 | rsi5 > 70 on the reclaim bar (parent) | -0.0779 | -0.0457 | -5.01 | 13.2 | 8.6 | 0 | -0.013 | -0.133 | -0.071 | -0.082 |
| X1-p05 | QQQ at/below its VWAP (parent) | -0.0805 | -0.0821 | -8.37 | 77.0 | 50.3 | 6 | +0.003 | -0.117 | -0.083 | -0.088 |
| X2-p05 | SPY dip-then-turn (parent) | **-0.0506** | **-0.0589** | -5.62 | **82.2** | 53.6 | 6 | +0.019 | -0.115 | -0.056 | -0.063 |
| X3-p05 | QQQ dip-then-turn (parent) | -0.0510 | -0.0715 | -5.86 | 76.1 | 49.7 | 12 | +0.021 | -0.116 | -0.061 | -0.068 |
| S-p05 | X2 on S3 + cost5 | +0.0021 | -0.0116 | -0.66 | 30.9 | 20.2 | 41 | +0.039 | -0.041 | -0.005 | -0.009 |
| R1-lv | rsi5 <= 20 at the poke (parent) | -0.0861 | -0.1087 | -6.86 | 40.5 | 40.0 | 6 | +0.022 | -0.194 | -0.098 | -0.106 |
| R2-lv | rsi5 crosses above 20 (parent) | -0.0690 | -0.1020 | -5.65 | 25.9 | 25.6 | 12 | +0.028 | -0.179 | -0.085 | -0.094 |
| R3-lv | rsi5 > 70 (parent) | -0.1070 | -0.0603 | -4.68 | 11.9 | 11.7 | 6 | +0.002 | -0.200 | -0.095 | -0.110 |
| X1-lv | QQQ at/below its VWAP (parent) | -0.1153 | -0.1067 | -7.72 | 50.1 | 49.5 | 6 | +0.022 | -0.170 | -0.115 | -0.123 |
| X2-lv | SPY dip-then-turn (parent) | -0.0831 | -0.0842 | -5.70 | 56.0 | 55.3 | 0 | +0.035 | -0.186 | -0.087 | -0.100 |
| X3-lv | QQQ dip-then-turn (parent) | -0.0855 | -0.0968 | -5.73 | 51.1 | 50.4 | 6 | +0.034 | -0.181 | -0.094 | -0.109 |
| S-lv | R2 on S3 + cost5 | +0.0096 | -0.0216 | -0.59 | 9.4 | 9.2 | 41 | +0.051 | -0.056 | -0.007 | -0.012 |

Dip-then-turn means the ETF's running low from its open is at or below -0.15% (SPY) or -0.30% (QQQ), and the ETF is now at
least 0.10 points above that low.

**Parents and bases (not re-counted):**
- Parents: p05 is -0.068 at 153/session. p05-lowvol is -0.095 at 101/session.
- p05 S3 + cost5 base is symbol-quality Q08: -0.0028 / -0.0084 at 54.3/session.
- p05-lowvol S3 + cost5 base is ind1 B-lv: -0.0072 / -0.0188 at 35.5/session.

**How the S rows were picked:** by the PLAN rule, the highest TRAIN avg R among rows with >= 25/session.
- For p05 the pick was X2.
- For p05-lowvol the pick was R2: 25.9/session, TRAIN -0.0690, edging X2-lv at -0.0831.

## What it means
- **RSI(5) does not help.**
  - Oversold at the poke (R1) and short-term pop (R3) are both worse than the parent or no better.
  - The ST3-style cross back above 20 (R2) moves p05 by only +0.004R. It hurts p05-lowvol on VALID.
- **QQQ at or below its VWAP (ST7Q style) hurts.** It selects more weak-tape trades, which is the beta problem again.
- **SPY dip-then-turn (X2) is the best volume-keeping lift found for p05.**
  - avg R goes from -0.068 to -0.054, +0.014R on both splits, at 82 trades/session (54% kept).
  - That is still a clear loss (t -5.6, 1 of 17 months positive).
- **On the S3 + cost5 base, the indicator adds nothing beyond noise and costs volume.**
  - S-p05: TV -0.004 at 31/session, against Q08's -0.005 at 54/session. VALID is worse.
  - S-lv: TV -0.005 at 9/session, against B-lv's -0.013 at 36/session. VALID is worse, and volume falls below 25.
- **Every row has the same split.** Each makes a little on SPY up days and loses on SPY down days (-0.04..-0.20R).
  Neither indicator, known at the signal close, removes that beta.
- **One-big-day / top-5 check:** no row has positive total R, so no record is being carried by its best day or best 5 days.
  Removing the top 5 sessions makes each row 0.005-0.015R worse. The losses are broad, not concentrated.

## Files
- PLAN.md: the pre-declaration.
- build.py: adds rsi5 / prior-bar rsi5 / SPY-QQQ running low, fromOpen and VWAP fields to the ind1 harness.
  The cache is in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030c/ind3/cache.
- score.py, score_out.txt, results.csv: all 14 rows.
