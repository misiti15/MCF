# OPP 2026-10-15: recurring loser patterns tested as opportunities (RW2 never-worked, ST2 wrong-side). FAILED, 0 of 65

*Educational only - not financial advice.*

- Owner idea (2026-10-14): a loser pattern that recurs should be tested as a trade, not only as a filter.
- Backtests on the open two-year history (2024-10 + 2025-03..2026-10-07), production costs in (1c + 1 bps per side,
  +2c stops, time-of-day entry multiplier, x3 extended tier). Stop-first, entry at the signal bar's close, flat 15:55.
- The rule-19 locked block (2024-11-01..2025-02-28) was **never loaded**; the head/tail file was read with per-open-month
  date filters. No holdout was scored.
- `PLAN.md` was written before any configuration was scored. Nothing was added after scoring.

**Configurations scored: 65** (Part A 23, Part B 42). **Testing bar met: 0. Study bar (t >= 2.89): 0. Lineage bar
(A t >= 5.24 at N 934,993; B t >= 4.84 at N 120,542): 0.** 8 of 65 have exp > 0. All 8 are the next-day EOD
rebound, and April 2025 carries them.

## Failures first

### Part A: RW2-exhaustion-noon-adv150-short-FD "never worked" -> opposite / continuation. 0 of 23 positive
- 22,187 RW2-FD first signals (adv >= $150M). The base short t1s1 is -0.062R (t -3.60). The re-simulation equals the
  frame outcome (corr 1.000). 40% are stopped, and 47% of the stops "never worked" (MFE < 0.25R before the stop).

| config | n | exp R | t | win | up / down | excess vs same-minute (t) |
|---|---|---|---|---|---|---|
| A1 long at the RW2 signal, t05s1 (best A1) | 22,187 | -0.051 | -4.48 | 64% | +0.003 / -0.140 | +0.025 (3.10) |
| A2 long at the RW2 stop, all stops, t05s1 (best A2) | 8,761 | -0.074 | -4.08 | 61% | -0.027 / -0.150 | +0.020 (1.94) |
| A3 long at a never-worked stop, t05s1 (best A3) | 4,142 | -0.070 | -3.56 | 62% | -0.031 / -0.140 | +0.024 (1.78) |
| A4 continuation short, LL (all stops), t1s1 (best A4) | 7,574 | -0.064 | -3.09 | 49% | -0.173 / +0.131 | +0.006 (0.41) |
| A4 continuation short, VL (all stops), t1s1 | 2,505 | -0.118 | -1.95 | 46% | -0.336 / +0.087 | +0.012 (0.47) |

- **Both sides of the RW2 signal lose after costs.** The signal has no direction. The long side is only slightly
  better than a random long at the same minute (+0.02R), and not by enough to cover costs.
- "Never worked" does not mark a better reversal: A3 equals A2 within noise.
- A4 is pure regime: positive in down sessions, negative in up sessions, with no excess over the control.

### Part B1: ST2 skipped stocks (down >= X% from the open), same-day rebound long. 0 of 24 positive
- Universe adv >= $95M, trigger 10:30-15:00, first trigger per symbol-day.
- Base rate (every bar of the same down-X universe in the window): -0.035 to -0.053R.

| config | n | exp R | t | win | up / down | WF | excess vs same-minute (t) |
|---|---|---|---|---|---|---|---|
| VW (VWAP reclaim) down >= 3%, t1s1 (best by exp) | 22,818 | -0.024 | -1.05 | 51% | +0.182 / -0.180 | 0.47 | +0.056 (4.02) |
| VW down >= 3%, t05s1 | 22,818 | -0.029 | -2.15 | 64% | +0.088 / -0.126 | 0.47 | +0.041 (4.41) |
| H5 (5-min high reclaim) down >= 4%, t05s1 | 22,118 | -0.046 | -2.74 | 64% | +0.029 / -0.075 | 0.12 | +0.023 (2.07) |
| MR (H5 + 0.5 ATR below VWAP) down >= 4%, t05s1 | 7,996 | -0.041 | -1.92 | 66% | -0.018 / -0.033 | 0.18 | +0.002 (0.17) |

- The VWAP reclaim is the only trigger with a real relative edge. It beats a random long at the same minute by
  +0.04 to +0.066R (t 2.2-4.4 across X), and the same-universe base rate by about +0.02R. It is still negative after
  costs and flips sign with the session (WF 0.24-0.47).

### Part B2/B3: next-day rebound long after a day closing >= X% below its open. 8 of 16 positive, none passes

| config | n | exp R | t | win | train / valid | up / down | WF | ex-best-day | excess vs universe (t) |
|---|---|---|---|---|---|---|---|---|---|
| **09:50 entry, EOD, down >= 6% (best)** | 6,123 | **+0.462** | **1.44** | 54% | +1.006 / +0.027 | +1.514 / -0.447 | 0.53 | +0.143 | +0.205 (2.59) |
| 09:50 entry, EOD, down >= 5% | 9,542 | +0.446 | 1.42 | 54% | +1.015 / -0.005 | +1.506 / -0.454 | 0.53 | +0.131 | +0.191 (2.69) |
| 09:50 entry, EOD, down >= 3% | 26,608 | +0.269 | 1.35 | 53% | +0.657 / -0.024 | +1.223 / -0.553 | 0.47 | +0.078 | +0.123 (2.77) |
| open entry, EOD, down >= 6% | 6,125 | +0.406 | 1.18 | 53% | +0.883 / +0.025 | +1.604 / -0.651 | 0.47 | +0.063 | +0.198 (2.16) |
| 09:50 entry, t1s1, down >= 3% (best t1s1) | 26,608 | -0.055 | -1.71 | 50% | -0.026 / -0.077 | +0.176 / -0.294 | 0.29 | -0.068 | +0.025 (1.36) |
| open entry, t1s1, down >= 3% | 26,625 | -0.178 | -6.30 | 47% | | | | | |
| B3 gap-fade reference (gap <= -2%), open, EOD | 24,300 | -0.028 | -0.17 | 50% | -0.108 / +0.032 | +1.113 / -1.200 | 0.35 | -0.096 | +0.108 (1.49) |
| B3 gap-fade reference, open, t1s1 | 24,300 | -0.215 | -6.68 | 46% | | | | | |

R is 0.25 x ATR, so an EOD hold has a very wide R distribution, and t stays low despite large means.

- **Concentration (rule 5).** April 2025, the tariff crash and rebound, carries B2.
  - 09:50 EOD, down >= 5%: April 2025 gives +3.82R per trade over 968 trades, 87% of the total R.
  - The other 8,578 trades average **+0.066R**.
  - Valid (2026) is about 0 in every row.
- It fails the Testing bar on t (< 2.0), the down regime (< 0), WF (< 0.6) and valid.
- The excess over the same-day universe (+0.12 to +0.21R, t 2.2-2.8) is a real cross-sectional reversal effect. It
  is market-direction dependent and does not survive as an absolute trade.
- **Next-day gap split.** Names that gap down the next day rebound more: down >= 5%, open EOD gives +0.64 when they
  gap down (n 4,597) and +0.15 when they gap up (n 4,949). The generic gap-fade (B3) is ~0 / negative, so the prior
  day's loss matters more than the gap. The same April caveat applies.
- Stops at 1R (t1s1) turn every next-day variant negative. The open entry also pays the x3.8 opening spread.

## Bars and counts
- **Configurations: 65** (A 23 + B1 24 + B2 16 + B3 2), plus the A0 base reference, which is not counted.
- **Testing bar:** exp > 0, day-clustered t >= 2.0, train and valid > 0, up and down > 0, WF >= 0.6,
  ex-best-day > 0, excess > 0, plateau. **0 met.** The closest is B2 09:50 EOD down >= 6% at t 1.44, which also fails
  down, WF and valid.
- **Lineage bars:**
  - RW2 / exhaustion: N 934,970 + 23 = 934,993, t >= 5.24.
  - ST2 / stack1009: N 120,500 + 42 = 120,542, t >= 4.84.
  - The study-only bar is 2.89. **0 met.**

## Proposed changes
- **None.** No Testing config entry is proposed, and no config diff.
- Rework ideas are recorded in the backlog (rule 18) and are not tested here. Each would count as a new lineage step.
  1. B2 next-day rebound with a market-regime gate known at the entry, e.g. SPY's prior day <= -2% or SPY above its
     open at 09:50, checked ex-April-2025 first.
  2. B1 VW reclaim with an index-up gate.

## Backlog (`add_backlog.py`; `research/BACKLOG.md` regenerated, 400 entries; tag `owner-opportunity`)
| id | parent | status | configs |
|---|---|---|---|
| `opp1014-rw2-opposite-long` | bdi1014-rw2-extension-floor | failed | 11 |
| `opp1014-rw2-continuation-short` | bdi1014-rw2-extension-floor | failed | 12 |
| `opp1014-st2-skipped-sameday-rebound` | bdi1014-st2-wrong-side | failed | 24 |
| `opp1014-st2-skipped-nextday-rebound` | bdi1014-st2-wrong-side | failed | 18 |

The two parent filter ideas (`bdi1014-rw2-extension-floor`, `bdi1014-st2-wrong-side`) are still `idea`. They were not
scored here.

## Files
- `PLAN.md`: the pre-declaration.
- `opp1014.py` writes `results.csv` (every configuration, with controls, base rates, regime, WF and pass flags) and
  `summary.json`. The scratch trade files (33 MB) were deleted after scoring. Re-running rebuilds them in about 8 minutes.
- `add_backlog.py`: the backlog entries.
