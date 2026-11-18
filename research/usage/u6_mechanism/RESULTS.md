Educational only — not financial advice

# U6 — Mechanism setups for missed moves: RESULTS (2026-11-18)

**Verdict: 0 of 5 pass. No Testing-copy proposal.** Pre-registered in PLAN.md (pushed before scoring), one config
each, costs in (Workbench/LR8 research model), next-minute-open fills, day-clustered t bar 2.43
(**19 configurations / looks**: 5 setups + 5 random controls + 9 side splits). Locked block not read. Research only:
nothing deployed, no config/code/runtime change. EARN-GO not duplicated (CHECK runs with the live earnings blackout).

## Failures first — per setup (both sides pooled)

| Setup | Category | FIT n (/sess) | FIT avg R (gross) | FIT t | FIT random | CHECK n | CHECK avg R (gross) | CHECK w/o best day (share) | CHECK random | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 U6-OD-drive | opening drive 09:35-09:45 | 3,096 (18.4) | -0.156 (+0.002) | -5.75 | -0.171 | 399 | -0.191 (-0.049) | -0.208 (total < 0) | -0.093 | FAIL |
| M2 U6-GAPGO-nonearn | gap-and-go, non-earnings | 1,541 (9.2) | -0.078 (+0.004) | -2.21 | -0.078 | 275 | +0.014 (+0.080) | -0.049 (430%) | +0.056 | FAIL |
| M3 U6-SECLAG | sector-move follower | 1,988 (11.8) | -0.093 (+0.019) | -2.40 | -0.105 | 340 | +0.026 (+0.121) | -0.026 (199%) | -0.077 | FAIL |
| M4 U6-LEVETF-drive | inverse/vol/lev ETF spike (long) | 184 (1.1) | -0.172 (-0.071) | -1.31 | -0.166 | 29 | +0.260 (+0.365) | -0.066 (121%, 11-05) | +0.045 | FAIL |
| M5 U6-PMTREND | afternoon trend continuation | 3,240 (19.3) | -0.084 (+0.019) | -3.97 | -0.115 | 548 | -0.153 (-0.065) | -0.180 (total < 0) | -0.059 | FAIL |

FIT totals: M1 -483.6R, M2 -119.5R, M3 -184.3R, M4 -31.7R, M5 -272.9R. Months positive (of 8): M1 0, M2 2, M3 2,
M4 2, M5 0. CHECK totals: M1 -76.1R, M2 +3.9R, M3 +8.8R, M4 +7.5R, M5 -83.7R; green days 23% / 42% / 48% / 83% (6
days) / 29%. Worst CHECK day: -10.7 / -13.7 / -9.9 / -5.6 / -12.1R.

**Why they fail:** gross edge is ~0 in the 2-year sample for all five (-0.07..+0.02R) — no setup beats its random
same-minute control by more than ~0.03R in FIT — and costs are 0.08-0.16R per trade (M1 highest: early-session
spreads). The mechanism stories do not show up as a gross edge on 168 sessions; the CHECK positives (M2, M3, M4) are
one-day-carried (best-day share 121-430%) and below or near their own random control except M3 and M4.

## Per side (descriptive, not verdicts)

| Setup side | FIT avg R (n) | CHECK avg R (n) | CHECK w/o best day | Note |
|---|---|---|---|---|
| M1 long / short | -0.180 (1,585) / -0.131 (1,511) | -0.283 (210) / -0.089 (189) | -0.326 / -0.148 | both negative |
| M2 long / short | -0.092 (929) / -0.056 (612) | -0.080 (127) / +0.095 (148) | -0.127 / +0.013 | short CHECK one-off; FIT short negative |
| M3 long / short | -0.087 (1,023) / -0.099 (965) | +0.142 (167) / -0.086 (173) | +0.074 (share 51%) / -0.199 | long CHECK t 1.19; FIT long negative |
| M4 long | -0.172 (184) | +0.260 (29) | -0.066 | 11-05 carries it |
| M5 long / short | -0.091 (1,636) / -0.078 (1,604) | -0.138 (272) / -0.167 (276) | -0.171 / -0.198 | both negative |

Regime (FIT, SPY open-to-close up / down sessions): every setup has at least one negative regime; the side that
"works" flips with the tape (e.g. M3 long +0.081 up / -0.309 down, M3 short -0.455 up / +0.114 down) — i.e. the
day's index direction, not the mechanism, decides the sign. Same pattern as P2/U5.

## Capture rate (Move Hunt, 12 sessions 10-29..11-17, 600 tradable top moves)

| Setup | Moves captured | New (live missed) | Capture 15.0% -> | R of captured trades | Setup's R on those 12 sessions (trades) |
|---|---|---|---|---|---|
| M1 | 13 | 10 (all opening drive) | 16.7% | +10.2R | -11.3R (115) |
| M2 | 6 | 5 (4 drive, 1 gap-go) | 15.8% | +6.3R | +12.7R (119) |
| M3 | 1 | 1 | 15.2% | +0.3R | +18.4R (106) |
| M4 | 3 | 3 (lev/inv ETF) | 15.5% | +5.3R | +6.2R (25) |
| M5 | 1 | 1 | 15.2% | +1.7R | -30.2R (184) |
| All five | 23 | 20 | **18.3%** (+3.3 pts) | +23.8R | -4.2R (549) |

Tradable-move mix: 325 opening drive (live caught 40), 96 lev/inv ETF (10), 35 gap-go (10), 11 afternoon (0),
133 other (30). The setups would have lifted capture by 3.3 points, but they buy those 20 captures with 549 trades
that net -4.2R on the same sessions (and -1,092R over the 168 FIT sessions): capture without selectivity. Higher
capture is not worth it at this cost.

## What can be salvaged (honest, no proposal)

- Nothing reaches WATCH (no setup passes either half). The two CHECK-positive sides — M3 long (sector-lagger catch-up,
  +0.142R, n 167, w/o best day +0.074, share 51%) and M2 short (non-earnings gap-down-and-go, +0.095R, n 148) — are
  negative over the 2-year FIT, so they are recorded as backlog notes only, not candidates.
- Main lesson for C3-MECH: at 0.4-0.5 ATR stops the cost floor is ~0.08-0.16R/trade; a mechanism needs a gross edge
  of > 0.15R on the 2-year bars before it is worth a live slot. Opening-drive entries pay ~2x the cost of later ones.
- The missed opening-drive and lev-ETF moves are mostly index-drive days (11-05, 11-09, 11-17); index direction, not
  a stock-level signal, decides them — which the guardrails already rule out as a switch/hedge project.

## Rule-change context

CHECK is a replay of new setups (live rules do not act on these trades). Live capture 15.0% is from the as-traded
journals under the ledger changes in 10-29..11-17: 10-29 -2R per-setup latch and BAR90; 11-05 ROLL1; 11-11 TEAM-6;
11-12 LR8 after-cost R, Testing D/E/F opened; 11-16 ROT1; 11-17 TSZ1, WB copies, promotion hold.

Per-setup effect on existing setups: none (new setups only; no existing setup changed). L3-gap-slope-fromopen-FD
untouched. Files: u6_results.csv, u6_verdicts.csv, u6_capture.csv, score_out.txt, code/day.py, code/score.py.
Scratch data deleted.
