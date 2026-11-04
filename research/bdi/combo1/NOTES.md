Educational only — not financial advice

# COMBO1 — results (2026-11-03)

Plan: `PLAN.md` (committed before the run). Script: `combo1.py` -> `combo1_out.txt`, `combo1_results.csv`. Two-year
backtest on 5-minute bars (open frame, entries 09:40-10:15), 2024-10-01..2026-10-07, TRAIN 170 / VALID 256 sessions.
The locked block 2024-11-01..2025-02-28 was never read (open frame asserted, o5 / daily dropped at load). Costs:
production costs + 4.4 bps entry spread crossing, floor 0.10R per trade; the average came to **0.16-0.23R per trade**,
because the opening time-of-day multiplier is high and R = 0.25 ATR is small. Earnings blackout removed.

**Configurations counted: 6 this project + 9 in the 11-03 BDI pass = 15** (full bar 2.33, BAR90 2.09).
**0 pass BAR90, 0 pass the Live Lab light lane gate. Every config is a failure; none is a finalist.**

| config | n | /sess | avg R | t | ex-mkt | w/o best day (share) | TRAIN / VALID | up / down / quiet | WF + | vs random (t) |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 SCAN-PB t1s1 | 10,397 | 24.4 | -0.156 | -9.32 | -0.156 | -0.159 (n/a) | -0.196 / -0.133 | -0.124 / -0.169 / -0.178 | 5% | +0.028 (1.85) |
| C1 SCAN-PB h1030H | 10,397 | 24.4 | -0.190 | -11.56 | -0.188 | -0.193 (n/a) | -0.239 / -0.161 | -0.179 / -0.201 / -0.190 | 5% | +0.023 (1.53) |
| C2 SCAN-PB-GRP t1s1 | 4,618 | 10.8 | -0.134 | -4.79 | -0.135 | -0.139 (n/a) | -0.233 / -0.101 | -0.079 / -0.192 / -0.138 | 16% | +0.046 (1.87) |
| C2 SCAN-PB-GRP h1030H | 4,618 | 10.8 | -0.184 | -6.93 | -0.183 | -0.190 (n/a) | -0.296 / -0.147 | -0.190 / -0.206 / -0.159 | 5% | +0.023 (0.95) |
| C3 LAG-OF-SCAN t1s1 | 884 | 2.1 | **-0.102** | -2.28 | -0.098 | -0.113 (n/a) | -0.269 / **-0.050** | -0.166 / -0.031 / -0.094 | 32% | **+0.096 (2.32)** |
| C3 LAG-OF-SCAN h1030H | 884 | 2.1 | -0.140 | -2.70 | -0.136 | -0.156 (n/a) | -0.271 / -0.098 | -0.233 / -0.033 / -0.131 | 21% | +0.087 (1.70) |

"w/o best day (share)": share n/a because total R is negative. ex-mkt = BETA1 OLS on SPY's move over the window (t1s1:
entry -> SPY daily close, an approximation). Lane gate misses: C1/C2 TRAIN and VALID far below -0.02R (C1 also near the
25/session ceiling); C3 VALID -0.050R and TRAIN 1.25 trades/session (< 1.5).

## What it says
- **Before costs the combinations are small positives; after costs they all lose.** Gross avg R: C1 +0.014 / +0.022,
  C2 +0.030 / +0.021, C3 +0.083 / +0.087. Friction is 0.16-0.23R at 09:40-10:15, 2-10x the gross edge.
- **The parts still pick names.** Day-matched excess vs a random U name on the same bar and side is positive in 6 of 6
  (+0.02..+0.10R); C3 (laggards of a group led by scanned movers) has the strongest, +0.096R t 2.32, in line with MH4
  (bdi/1102). It is cross-sectional information, not a tradable absolute result.
- **The SPY hedge does not help** (h1030H worse than t1s1 in all 3): the beta leg costs more than the day risk it
  removes in a 15-50 minute hold, and the ex-market avg R is about the same as the raw avg R (the books are near
  beta-neutral already: about half long, half short).
- **Riding scanned movers on a pullback bar (C1) is the weakest**: the 09:35 scan finds names that move, but entries
  after a 0.5 ATR move with a fade bar earn ~0 gross. Group agreement (C2) adds +0.02R, not enough.
- Consistent with eu1103: the measurable edge is smaller than what we pay to trade it at the open. Cheaper execution
  (EXEC1) is the precondition for any of these.

## Near-miss parked
C3 LAG-OF-SCAN-t1s1 (best VALID, -0.050R; vs random +0.096R t 2.32) is parked with a frozen forward-shadow rule in
`research/bdi/swings/hypotheses.jsonl` (`combo1-C3-lag-of-scan`) and backlog `combo1-c3-lag-of-scan` (parent
`combo1-1103-open-scan-laggard-fade`, configs_tried 15).

**Rule-change context:** the two-year results are rule-fixed backtests; no live rule change applies to them. Live
changes near this date (research/ledger.jsonl): 11-03 MF3-FD / MF5-FD to the Graveyard, RW3S to Testing 2; from 11-04
NS5-FD / ST4-FD / RW6G1-FD to the Graveyard and **UNI1 (Testing 2 trades only the top 500 names)** — the same U block
as here, so UNI1's live record and this backtest share a universe rule.
