Educational only — not financial advice

# GEN2 restart batch 2026-11-25 (Setup Generator, 10 setups) — review gates

Owner GEN2 (2026-11-25): "Start it but do 10 initially then 5 a week after that. The first generator parameters DID end
up producing a few quality setups... don't be too quick to change up its generation process."

**Generation = unchanged.** `python -m mcf.research.generator run --date 2026-11-25 --n 10 --apply` — the same command,
grammar, screen, ranking, pick rules and defaults as the 10-19..10-28 nightly runs (3,000 random specs + Setup lab seeds,
`--min-long 5`, seed = date, prior families avoided). 3,148 configurations scored (3,000 random + 148 seeds), 2,068
rankable, 25 tier 1, 10 picked (6 long / 4 short, 1 seeded). Runtime 847 s. Run report: `research/generator/runs/2026-11-25.json`.
Only the data moved: the open two-year panel now runs to 2026-11 (train <= 2025-12, valid 2026-01..2026-11; locked block
2024-11..2025-02 never read); the earnings-blackout file was taken from `origin/research-data` (2026-10-11 build).
Ledger `2026-11-25-gen-seed` (effective 2026-11-27; 11-26 is a market holiday).

The review gates below are **recorded only**. They did not change generation or the picks.

## Per setup: rule, mechanism note, screen (costs in), 11-19 admission check

| # | Setup | Mechanism note (why it might work; written after the pick) | Train n / avg R / t / days | Valid n / avg R / t / days | Up / down / quiet avg R | Exp. live/day |
|---|---|---|---|---|---|---|
| 01 | `GEN-261125-01-RSI2le15-Gaplem2-Since950ATRge0p44-OPEN-QQQgt0p6-t1s1-long` | A stock that gapped down 2%+ is recovering after 09:50 while QQQ runs up; buy the first short pullback (RSI(2) <= 15). Gap-fill with the market behind it. **Fragile: only 19 screen days.** | 655 / +0.043 / 5.08 / 7 | 67 / +0.478 / 2.18 / 12 | +0.086 / – / – | 0.0 |
| 02 | `GEN-261125-02-UpWickge0p71-Slope6ge0p03-PDLdistlem0p59-MID-BRvwlt0p5-t1s05-long` | Midday on a weak-breadth day, a stock well below its prior-day low turns up (rising 6-bar slope); buy the turn with a half-R stop. The long upper wick weakens the story. | 480 / +0.043 / 0.36 / 92 | 352 / +0.033 / 0.39 / 101 | +0.293 / +0.034 / −0.072 | 0.55 |
| 03 | `GEN-261125-03-RangeExpge1p9-Slope6lem0p043-LATE-BRopgt0p65-t1s1-long` | Late-day dip buy: a sudden wide red bar in a liquid stock while 65%+ of stocks are above their open. Strong-tape dips tend to get bought into the close. | 443 / +0.105 / 0.72 / 59 | 412 / +0.104 / 0.68 / 34 | +0.037 / – / +0.652 | 0.0 |
| 04 | `GEN-261125-04-Ret15mATRlem0p16-Flow3lem1-PDLdistle0p14-LUNCH-QQQgt0p3-hold-long` | Lunch capitulation flush into prior-day-low support (fast 15-min drop, heavy selling flow) while QQQ is up; hold to the close. **Valid edge near zero (+0.013).** | 4071 / +0.119 / 0.42 / 114 | 5375 / +0.013 / 0.17 / 110 | +0.397 / −0.593 / −0.076 | 0.0 |
| 05 | `GEN-261125-05-RSI2ge100-PDLdistlem0p043-SMA20slopelem0p45-LAM-SPYgt0p5-holdtr-long` | A downtrending stock below its prior-day low starts a sharp short-covering pop (RSI(2) = 100) on an up-SPY morning; ride it with a trailing stop. **Weak (t 0.16 / 0.25); RSI2 >= 100 is a boundary threshold.** | 1235 / +0.026 / 0.16 / 45 | 1776 / +0.025 / 0.25 / 46 | +0.137 / −0.465 / −0.240 | 0.0 |
| 06 | `GEN-261125-06-MACDhge0p12-BearDiv-PDHdistlem0p39-LATE-BRvwgt0p7-t1s1-short` | Late-day exhaustion short: a stock pushed 0.39+ ATR above its prior-day high makes a new 20-bar high on a bearish RSI divergence while breadth is very strong. Fade the extended breakout into the close. | 608 / +0.137 / 2.57 / 42 | 129 / +0.055 / 0.53 / 26 | +0.093 / +0.582 / +0.313 | 0.0 |
| 07 | `GEN-261125-07-Flow3ge1-MACDhlem0p078-Since950ATRlem0p25-LUNCH-QQQltm0p6-holdtr-short` | Failed bounce in a weak stock on a red QQQ day (down 0.6%+): a 3-bar buying burst inside a falling MACD; short the bounce (bear flag). | 831 / +0.120 / 0.73 / 55 | 829 / +0.273 / 1.52 / 49 | −0.510 / +0.252 / +0.243 | 0.0 |
| 08 | `GEN-261125-08-MACDhlem0p12-BarRngATRge0p18-ADX7ge57-LAM-BRvwlt0p3-holdtr-short` | Trend continuation short: a strong in-day downtrend (ADX(7) >= 57, falling MACD, wide bar) on a weak tape (< 30% of stocks above VWAP). Coverage idea for down days. | 2652 / +0.154 / 0.97 / 85 | 1450 / +0.115 / 0.40 / 47 | −0.754 / +0.166 / +0.205 | 0.0 |
| 09 | `GEN-261125-09-NewLOD-Gaplem2-FromOpenlem2-MID-SPYdn-t1s1-short` (seed: Setup lab discovery 2026-11-21) | Gap-down trend day: a stock down 2%+ at the open and 2%+ more from the open makes a new low midday while SPY is red; short the continuation. | 691 / +0.071 / 0.53 / 72 | 760 / +0.038 / 0.40 / 89 | −0.274 / +0.116 / −0.040 | 0.0 |
| 10 | `GEN-261125-10-ORBfailUp-VWAPatrge0p25-PM-QQQgt0p3-holdtr-long` | Second-attempt long: the opening-range breakout failed earlier, but in the afternoon the stock is back 0.25+ ATR above VWAP with QQQ up; buy the re-try and trail. **Valid edge ~0 (+0.005).** | 1913 / +0.049 / 0.64 / 107 | 1687 / +0.005 / 0.05 / 100 | +0.155 / −0.065 / −0.262 | 0.0 |

## 11-19 testing-admission check (reported, not applied)

CLAUDE.md "Testing admission (owner 2026-11-19)" is the bar for entering a **testing arena (Testing A–F)**. The Setup
Generator account admits by the owner's 10-19 rule, which is unchanged. The check, for the record:
- **Not "really bad":** all 10 pass. Train and valid avg R are > 0 for every pick, so none is <= −0.05 with t <= −2.
- **Derived from a promising parent:** **0 of 10.** All are machine-generated. GEN-261125-09 is seeded from the Setup lab
  discovery rules, which are not a live parent. So none would qualify for a Testing A–F admission on the debatable path.
- **Top-10 benchmark standard** (research/ultimate_1119/top10/PLAN.md, T1/T2 one-minute replay): **not run.** It needs
  the 1-minute bar cache, which is not in this workspace. As it stands, none is shown to meet the standard.
- **Other flags:**
  - 9 of 10 expect 0.0 live trades a day on the 60-session median (GX5; most fire on fewer than half the days), the same
    as the 10-29 batch.
  - Under ROT3 most will be tagged "rare" (< 0.5 signals per active day) and get the shadow fast lane.
  - Weak: #01 (19 screen days), #04 / #05 / #10 (valid t <= 0.25).
- **Guardrail note:** CLAUDE.md lists "GEN setups with no mechanism" under the C3 "Stop doing" guardrails. GEN2 is the
  owner's explicit override. The mechanism notes above are post-hoc hypotheses to review on the live record, not evidence.

Live verdicts follow the existing rules: C3-ROT (>= 15 active days and 30 trades), FOOTRACE-EXIT, the GYH V1 floor, and
the owner's 11-25 pre-consent that GEN setups meeting the floor / FOOTRACE-EXIT may move to the Graveyard.
