Educational only — not financial advice.

# cap-etp: buying inverse/vol ETPs (and shorting bull leveraged ETPs) on a morning/midday index down-trend

**Result:** none of the 19 configs passes. The best one, A-vwhold-t1s1, is a near-miss. It technically meets the top-10 Tier A benchmark, whose medians are negative, but it fails the significance bar (WB2) and the up-day rule. Shorting bull ETPs is worse than buying inverse ETPs.

The locked block 2024-11-01..2025-02-28 was never read: the 1-minute bars were filtered at read and asserted, and the lab frames come only from open months. Nothing in the repo was changed.

## Setup
- **Configurations tried: 19.**
  - Round 1, 15 configs, declared in advance: three triggers (onset / brk / vwhold) × (A long inverse t1s1/t05s1, B short bull t1s1/t05s1, C long bull on UP t1s1).
  - Round 2, 4 configs, declared after FIT and before any CHECK/T2 read: SPY ≥0.30% strong-move filter, with and without the compass.
- **Significance bar:** WB2 bar max(1.5, √(2 ln 19)) = 2.43. The Testing bar (90% of it) is 2.18.
- **Engine:** my own copy of the bench10 method (scratch: engine.py, run.py, build.py).
  - 5-min features are built from the 1-minute caches.
  - ATR_d / ADV20 / gap come from the lab frames on T1, so the locked-gap boundary in early March is handled.
  - Entry at bar close; 1-min walk with stop checked first; target only when traded through by ≥ $0.01; flat 15:55.
  - LR8 costs with the time-of-day multiplier and the ×3 tier; 1.2 bp borrow on shorts.
  - Testing book: cap 100, ≤ 3 lots per symbol, price ≥ $5, cost filter 0.15R, shorts only when ETB ≥ 90%.
- **Periods:** FIT 2024-10 + 2025-03..09 (170 sessions). CHECK 2025-10-01..2026-11-04 (276 sessions), scored once per finalist (2 finalists). T2 2023-01..2024-09 from cache_fresh (no UVXY/VXX there).
- **Index state ("DN" / "UP"):** a W60-style compass computed from inputs available at the bar.
  - votes = sgn(SPY from open) + SPY VWAP side + QQQ VWAP side + SPY/QQQ/IWM agreement + 60-min persistence of SPY's from-open sign.
  - DN means votes ≤ −4 with persistence. Breadth is replaced by QQQ's VWAP side so T1 and T2 use the same inputs.
  - DN fires on 95 of 170 FIT sessions between 09:50 and 13:00, so it is a loose state.
- **Rule changes:** none fall inside the backtests (today's rules are applied to every session). The live overlap window 10-06..11-04 spans the 10-20/10-22/10-30 L3 moves, 10-23 latch, 10-28 sizing, 10-29 −2R latch, 10-30 cost filter and the 11-12 LR8 basis in Primary.

## FIT grid (avg R after costs; t = day-clustered)
| config | n | sess | avg | w/o best | w/o top-2 | t | up / flat / down |
|---|---|---|---|---|---|---|---|
| A-onset-t1s1 | 844 | 95 | −0.038 | −0.053 | −0.067 | −0.45 | −0.72 / −0.35 / +0.35 |
| A-onset-t05s1 | 844 | 95 | −0.091 | | | −1.45 | |
| B-onset-t1s1 | 598 | 95 | −0.081 | | | −0.90 | |
| B-onset-t05s1 | 598 | 95 | −0.116 | | | −1.74 | |
| C-onset-t1s1 | 849 | 113 | +0.010 | +0.000 | −0.011 | 0.13 | +0.48 / −0.45 / −0.85 |
| A-brk-t1s1 | 438 | 72 | +0.050 | +0.023 | −0.002 | 0.50 | |
| A-brk-t05s1 | 438 | 72 | −0.043 | | | −0.64 | |
| B-brk-t1s1 | 330 | 69 | −0.013 | | | −0.13 | |
| B-brk-t05s1 | 330 | 69 | −0.080 | | | −1.03 | |
| C-brk-t1s1 | 500 | 93 | +0.026 | +0.008 | −0.008 | 0.30 | |
| **A-vwhold-t1s1** | 402 | 80 | **+0.088** | +0.067 | +0.046 | 0.97 | −1.06 / −0.15 / +0.29 |
| A-vwhold-t05s1 | 402 | 80 | +0.052 | +0.042 | +0.030 | 0.85 | |
| **B-vwhold-t1s1** | 278 | 74 | **+0.107** | +0.084 | +0.061 | 1.08 | −1.10 / −0.05 / +0.35 |
| B-vwhold-t05s1 | 278 | 74 | +0.036 | +0.024 | +0.012 | 0.49 | |
| C-vwhold-t1s1 | 447 | 95 | −0.016 | | | −0.18 | |
| A2-vwhold-s30 | 263 | 48 | +0.058 | +0.025 | −0.010 | 0.49 | |
| B2-vwhold-s30 | 162 | 42 | +0.079 | +0.039 | −0.006 | 0.65 | |
| A3-nocomp-s30 | 299 | 49 | −0.009 | | | −0.08 | |
| B3-nocomp-s30 | 192 | 44 | +0.054 | +0.019 | −0.018 | 0.45 | |

**Matched random-day null** (symbol and entry time moved to a random FIT session, 20 draws):

| config | null avg R | actual avg R | percentile |
|---|---|---|---|
| A-vwhold | −0.044 | +0.088 | 100th |
| B-vwhold | −0.080 | +0.107 | 100th |
| A-brk | −0.071 | +0.050 | 100th |
| C-brk | −0.067 | +0.026 | 100th |

The index state turns a bleeding unconditional ETP trade into a small positive one. The edge is still small, and with every trade in a session being the same index bet, t stays near 1.

## Finalists: CHECK (once) and T2
| finalist | test | n | avg | w/o best | w/o top-2 | best-day share | t | months + | up / flat / down |
|---|---|---|---|---|---|---|---|---|---|
| A-vwhold-t1s1 | CHECK | 428 | +0.030 | +0.012 | −0.006 | 0.60 (1 day) | 0.44 | 7/13 | −0.49 / −0.27 / +0.37 |
| A-vwhold-t1s1 | T2 | 958 | −0.038 | −0.048 | −0.057 | – | −0.64 | 6/21 | −0.80 / −0.32 / +0.45 |
| A-vwhold-t1s1 | T1 combined | 830 | +0.058 | +0.048 | +0.037 | 0.18 | 1.03 | 11/21 | |
| B-vwhold-t1s1 | CHECK | 527 | −0.019 | −0.034 | −0.050 | – | −0.26 | 5/13 | −0.92 / −0.29 / +0.44 |
| B-vwhold-t1s1 | T2 | 445 | −0.101 | −0.118 | −0.133 | – | −1.34 | 8/21 | |

**Details for A-vwhold on CHECK:**
- By entry time: 09:50-10:29 +0.126 (118 trades); 10:30-11:29 −0.104 (146); 11:30-12:29 +0.008 (119); 12:30-13:00 +0.268 (45). No clean time-of-day pocket.
- Exits: 180 targets, 139 stops, 109 at 15:55. Median hold 95 min.
- By symbol on CHECK: UVXY −0.203 (57 trades), SPXS −0.109, SQQQ +0.098, SDS +0.164, SPXU +0.147, TZA +0.104. Reported only; no symbol pruning was done, because that would be a tune.

## Answers to the brief
1. **Morning/midday inverse/vol capture.**
   - The only mechanism with a positive FIT that survives CHECK is the VWAP-hold continuation, and only weakly (+0.030R, t 0.44, 1-day tag).
   - It fails on T2 (2023-24, a bull market).
   - Entering at DN onset loses. A stricter SPY ≤ −0.30% filter does not help: whether the day keeps falling stays a coin flip, consistent with the compass and rootcause_1119 findings.
2. **Short bull ETPs instead?** No. B is worse than A on CHECK (−0.019 vs +0.030) and on T2 (−0.101 vs −0.038), and it pays borrow and needs ETB. Buying the inverse fund is the better form, and it is allowed under INV-H1.
3. **Top-10 benchmark.** A-vwhold-t1s1 meets every Tier A threshold of the weak standard. It fails the WB2 / Testing t-bar (0.44 on CHECK against 2.18), the rule requiring positive expectancy in up and down sessions (up days −0.49 / −0.80), and T2 is negative.
4. **Fit with Primary.** The family is short-market exposure gated to down-trend sessions. It adds to Primary's down-day gains and does nothing for Primary's red days (up/quiet). The live overlap is 22 sessions with 6 fires — too small to judge.

## Verdict and suggestion
- No Primary candidate.
- A-vwhold-t1s1 is a near-miss.
  - If the owner wants inverse-ETP capture exposure, it could only go to a low-rep / testing home, on the grounds that it formally meets the top-10 Tier A standard. It should be tagged `testing-bar-fail`, `1 day` (CHECK) and `T2-negative`.
  - Expect correlated bursts of 2-5 inverse-ETP lots on DN sessions.
  - My read: don't force it.
- The B, C, onset, brk and strong-move variants are closed.

Files (scratch): /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cap-etp/build.py, engine.py, run.py, fit_grid_r1.csv, fit_grid_r2.csv, check_*.parquet, t2_*.parquet. The derived frames (≈116 MB, frames_T1/T2.parquet) can be deleted.

Educational only — not financial advice.

## Robustness

null