Educational only — not financial advice.

# etfstop_1123: does ETF-STOP50 restrict NM-ETF's gains? (research only, no config change)

Owner request 2026-11-23: a more thorough study of ETF-STOP50 before deciding. "I don't want to restrict any one setup from potential gains long term."

## The rule and how it was tested

**Rule (rules_1122 Q50).** An NM-ETF-late-dip-di-long lot entered in a burst uses half the stop distance, with the same share count. A burst means 4 or more NM-ETF lots within 10 minutes, same bar included.

**2-year backtest:**
- The rules_1122 part-D E4 simulator, with bench10 signals, 1-minute exits, LR8 costs and the Primary book (cap 30, at most 3 lots per symbol, −2R latch).
- The base reproduces bench10 exactly: FIT +57.78R, T2 −9.16R, CHECK +10.71R.
- Periods: FIT 2024-10 + 2025-03..09 (170 sessions), T2 2023-01..2024-09 (427), CHECK 2025-10..2026-11-04 (276). That is 3.46 years.
- The locked block 2024-11..2025-02 was never read.

**Live replay:** run-1 journals (LR8), re-walked on real SIP 1-minute bars for all 16 live NM-ETF-family days.

**Configurations tried: 21.**
- 6 stop fractions.
- 11 burst definitions.
- 4 variants.
- Bar: 2.47 for this study, 2.88 for the lineage (N = 63).

**Rule-change context:**
- The Primary −2R latch has applied since 10-29.
- NM-ETF moved to Primary on 11-11.
- LR8 costs apply from 11-12; earlier rows are re-costed.
- TSZ1 (half-size testing lots) from 11-17 changes $ but not R.
- WB1, WB4 and ULT-22 started between 11-17 and about 11-20.
- The burst brake started 11-23, after every live day studied, and never binds on NM-ETF.

## Failures and limits

- **No configuration improves R significantly.** The best day-clustered t is +0.36, for AV50.
- **Plain Q50 fails its pre-registered cost test.** It gives up 2.21R a year against a limit of 2R.
- **Walk-forward picks no rule.** A fraction chosen on FIT alone comes out at 1.0, meaning no half stop.
- **Live evidence is one event.** Bursts occurred only on 11-20, and the other 15 live days are unchanged under every configuration.
- **Q50's cost is mostly one day.** 2026-06-11 accounts for 6.51R of the 7.65R.

## 1. Harm to gains (Q50)

265 burst lots received the half stop.

| Effect | Lots | R |
|---|---|---|
| Winners stopped early (12% of burst winners; they had made +11.38R) | 24 | −24.82 |
| Losers that now lose half as much | 46 | +22.47 |
| Small losers that now hit the half stop | 10 | −3.43 |
| Unchanged | 185 | 0 |
| **Net** | | **−7.65** |

- **How deep winners dipped first:** 182 of 206 burst winners (+84.7R) never dipped close to the half-stop level.
- **Top-decile winners:** 94.6% kept, which meets the charter's 90% minimum.
- **Best days:** the 10 best days lose −7.58R between them. 2026-06-11 goes from +3.76R to −2.75R. The single best day, 2025-04-10 (+22.5R), is untouched.

## 2. Stability

**By year:**

| Year | dR | Worst day before → after |
|---|---|---|
| 2023 | +3.97 | −8.21 → −4.21 |
| 2024 | −5.98 | −5.95 → −4.13 |
| 2025 | −4.06 | −2.81 → −2.67 |
| 2026 | −1.58 | −6.06 → −3.20 |

**Index state at entry:**
- SPY below VWAP: dR +3.91 over 153 lots.
- SPY at or above VWAP: dR −9.69 over 112 lots. Dips in a rising tape tend to recover, so the tighter stop costs most here.

**Stop fraction, from 0.3 to 0.8:** the rule trades tail protection for R along a smooth curve. 0.5 is not a lucky point; it sits in the middle of that curve.

| Fraction | R per year | Worst day |
|---|---|---|
| 0.3 | −4.70 | −3.38 |
| 0.5 | −2.21 | −4.21 |
| 0.6 | −1.28 | −5.01 |
| 0.8 | −0.30 | −6.61 |

**Burst size:**
- k = 4 is a plateau, and the 5- / 10- / 15-minute window barely matters.
- k = 5 or 6 costs less but misses 2024-01-31.
- k = 3 costs about twice as much.

## 3. How robust is the tail cut (5,000-resample day bootstrap)

| Config | R per year | Worst day better in | dR median (5–95%) | Worst-5-day cut, median (5–95%) |
|---|---|---|---|---|
| Q50 | −2.21 (≈ −$232) | 98% of resamples | −7.3 (−27.1 … +11.0) | — |
| AV50 | +0.98 | 98% | +3.4 (−11.6 … +18.4) | — |
| Q50G2 | −0.53 | 98% | — | +10.4 (+1.8 … +16.4) |

- The tail cut is robust.
- The R cost cannot be pinned down: every config's band crosses zero.
- The rule acts on about 5 days a year.

## 4. Variants (stop fraction 0.5)

| Config | dR, all periods | Winners stopped | Top-decile kept | Effect on 10 best days | Worst-5-day cut |
|---|---|---|---|---|---|
| Q50 | −7.65 | 24 | 94.6% | −7.58 | +8.97 |
| **AV50** (only when SPY is below VWAP at entry) | **+3.38** | **12** | **98.6%** | **0.00** | +8.97 |
| AO50 (only when SPY is below its open) | −0.62 | 12 | 98.6% | 0.00 | +4.97 |
| F5_50 (5th lot onward) | −2.00 | 8 | 98.6% | −1.01 | +5.17 |
| Q50G2 (Q50 + close the rest after 2 stops) | −1.85 | 14 | 94.6% | −7.55 | +10.66 |

- AV50's AV50 gain comes only from CHECK.
- The same index-side split flipped sign in the final1121 study.
- AO50 misses 2023-02-07.

## 5–6. Live replay (all 16 live days; only 11-20 changes)

| | Base | Q50 / AV50 | Q50G2 |
|---|---|---|---|
| Primary, 11-20 | −12.57 | −6.36 | −3.73 |
| Whole family, 11-20 | −42.70 | −23.77 | −17.03 |

- The rule helps every copy that had a burst on 11-20: WB4, ULT-22 and Primary.
- Only 1 of the 48 live burst lots was a winner cut short.

## 7. Bottom line

The rule is **insurance, not an edge.** It makes the worst days about half as bad:

| Day | Before | After |
|---|---|---|
| 2023-02-07 | −8.2R | −4.2R |
| 2026-06-17 | −6.1R | −1.5R |
| 2024-01-31 | −6.0R | −4.0R |
| Live 11-20 (Primary) | −12.6R | −6.4R |

- **Plain Q50** costs about 2.2R a year, roughly 13% of NM-ETF's backtest R. About 85% of that cost is a single good day.
- **Recommendation: Optional.** If you want the protection, **AV50** is the best fit for "don't restrict gains":
  - It keeps the full tail cut and halves the winners stopped early.
  - It leaves every one of the 10 best days untouched.
  - Its R impact is about neutral. That rests on CHECK, and the index-side filter has flipped before.
- **Q50G2** gives the most protection, for about −0.5R a year, but it still cuts 2026-06-11.
- **Process:** any of these is a Primary exit change. It goes through the Friday epoch, the rule-27 skeptic review, the PROTECTED / WB-copy route and a ledger entry. A WB copy running AV50 in a testing account would gather forward evidence first.
