# swarm1017 / rework-ns — NOTES (2026-10-17)

*Educational only — not financial advice. Research only: no config, ledger or backlog edits. Backtest on the open 2-year
history (rule 7: not live, not paper). Nothing here was scored on any locked holdout.*

## Failures first
- **No configuration clears the lineage bar.** N_study = 77,364 (as declared in PLAN.md), N_lineage ~ 165,764, bar
  day-clustered t >= **4.90**. The best candidate reaches t 2.93. Deflated Sharpe at that N is ~0 for every finalist.
- **NS1 (rsidip-rsi5pop long) and NS4 (pm-vwap-reclaim-oversold short): 0 candidates** in 13,212 / 12,564 configurations
  (threshold neighbourhood, one and two filters, opposite side, 3 geoms, 6 windows, refire). Recommend no rework variants
  for these; the FD versions are -0.068R / -0.055R on history.
- **NS5 (sma50-flush-oversold long): 1 weak candidate** (FD window, t1s05, slope<0 & buyPressure>0, t 0.79, +0.04R) - not
  worth a module.
- Opposite side: 2 candidates of 90, both weak (t ~1). Flipping these setups does not create an edge.
- Exits beyond the lab geoms (scale-out, trailing) not scored: the frames hold no 1-min paths. t05s05 does not exist in the
  frames or LabStrategy.GEOMS. Hold-to-close / time exits are not supported live (code needed).

## Parent reproduction (matches the published history)
RW6G1 950-1130 n 424 +0.263R (published 424 / +0.26); NS2-FD -0.055 (-0.054); NS3-FD -0.028; NS1-FD -0.068; NS4-FD -0.055;
NS5-FD -0.043. RW6G1-FD (refire) -0.008R n 2,388. Parent-window NS2 +0.004R (train +0.036, valid -0.024).

## Funnel
screen (n_tr >= 150, n_va >= 50, n >= 200, exp > 0 on train and valid): 941 | regime gate 260 | walk-forward >= 0.6: 401 |
beats same-minute random (excess > 0 train and valid, excess t >= 2): 512 | ex-best-day > 0: 729 | Stage-A plateau 897 |
**all gates: 90** (NS2 46, NS3 21, RW6G1 22, NS5 1) | de-duplicated (>= 60% trade overlap): **12 finalists** (finalists.csv).
With 77k tries, ~3,900 configs would pass p = 0.05 by chance; 90 gate-passers and a best t of 2.93 are consistent with a
selection effect around a weak real tilt in the RW6G1/NS2 morning short.

## Finalists (train = 2024-10 + 2025-03..12, valid = 2026-01..2026-10-07; production cost; t is day-clustered, all < 4.90)
| # | module | parent | change | n | /day | exp | t | train | valid | up / down | WF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | RWN1-rw6g1-rsi65-k25-t05s1-short | RW6G1 | RSI>=65, guard k2.5, t05s1 | 372 | 0.87 | +0.221 | 2.93 | +0.239 (246) | +0.184 (126) | +0.28 / +0.12 | 0.78 |
| 1 | RWN2-ns2-wed-nearhod-t05s1-short | NS2 | Wed + near HOD, t05s1 | 485 | 1.14 | +0.142 | 2.47 | +0.166 | +0.114 | +0.18 / +0.22 | 0.69 |
| 2 | RWN3-ns3-spyup-early-short | NS3 | SPY > open, 950-1030 [live code] | 388 | 0.91 | +0.167 | 2.69 | +0.211 | +0.130 | +0.04 / +0.26 | 0.67 |
| 3 | RWN4-ns2-spyup05-notfri-t05s1-short | NS2 | SPY > +0.5%, not Fri, t05s1 [live code] | 899 | 2.11 | +0.115 | 2.29 | +0.101 | +0.144 | +0.10 / +0.43 | 1.00 |
| 4 | RWN5-ns3-mon-weakrs-short | NS3 | Monday + RS < SPY [live code] | 295 | 0.69 | +0.202 | 2.17 | +0.164 | +0.257 | +0.15 / +0.41 | 0.63 |
| 5 | RWN6-rw6g1-atrhi-short | RW6G1 | atrPct >= 0.50, refire cd1 | 444 | 1.04 | +0.283 | 2.43 | +0.348 | +0.073 | +0.35 / +0.06 | 0.63 |
| 6-11 | (no module: t < 2) | NS3/NS2/NS5 | see finalists.csv | | | +0.03..+0.10 | 0.8-2.0 | | | | |

Concentration (robust.json, per half-year): #0, #1, #3, #5 carry most of their train result in 2025H1 (the Mar-Jun 2025
selloff/rebound) and are flat-to-negative in 2025H2; #2 is ~0 in 2026H1. Day-of-week filters (#1, #4) have no known
mechanism and are most likely selection noise. **Only #0 (RW6G1 with a stricter RSI and a wider band) sits on a real
threshold plateau** (all one-step neighbours positive on train and valid; RSI>=65 row positive in valid for fo>2/3/4 and
k 1.5/2/2.5 at t05s1) - it is the one variant worth a Testing slot. It fires < 1/day.

Live week 2026-10-12..16 (paper, research/swarm1017/week, n small): NS2 -0.49R/54 (p), NS2-FD -0.44R/65, RW6G1 -1.07R/3,
RW6G1-FD -0.13R/9, NS3 -0.27R/19, NS3-FD -0.02R/23, NS1 +0.11R/9, NS1-FD -0.08R/10, NS5 +0.24R/13, NS5-FD -0.27R/9,
NS4 +0.91R/4, NS4-FD +1.80R/2. Not evidence either way (rule 7; n < 20 for most).

## Live implementability
All six modules are type: lab, using only bar-close features (no look-ahead), verified bar-for-bar against the scan on two
full months (verify.json: 12/12 equal) and the VWAP-band guard on 40 symbol-days (2,516/2,516 bars equal). LabStrategy loads
all six. #2, #3, #4 need SPY fromOpen ("spy_fo") in the live lab frame - **code needed**; without it the module returns no
trades (fail-safe). #0 and #5 need the live frame's `volume` column (present). Offline caveat: frames start at 09:50, so a
crossing at the 09:50 bar is not seen offline but would be live.

## Files
PLAN.md (pre-declared grid), build.py (superset), guard.py (VWAP-SD guard from 1-min cache), common.py, scan.py
(scan_all.csv.gz: all 77,364 configs), gate.py (results.csv: 941 screened with gates; finalists.csv; gate_summary.json),
robust.py (robust.json), gen_modules.py, verify.py (verify.json), modules/ (6 modules + index.json).
Scratch (superset/guard parquet) deleted after the run; rebuild with build.py + guard.py (~13 min).
