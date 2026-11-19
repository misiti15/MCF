Educational only — not financial advice

# ULT-23 COLLAPSE-BASKET — ST7 one-bar RSI collapse on equity-basket ETFs and mega caps, LONG (round 3, D2)

**Tier: B (near miss, never deployed).** The pick holds up on CHECK: +0.139R a trade, +0.104 without the best day,
signal minus random +0.197. But it makes only **0.275 trades/session** (76 trades in 276 sessions), far below the 2.0
TIER A bar, and its day-clustered t is 1.75 against the 3.68 BEATS bar. No config in the grid reached 2/session on fit
or check. The highest-volume cell (QM RMAX35) makes 0.37/session on fit and 0.94 on check. **CHECK-INFORMED** (ST7 parameters and the
ULT-13 one-bar collapse, PLAN sec. 0.5 ii).

Research only: no setup, exit, config or account change. Nothing committed.

## What was built
- Live module `research/ultimate_1119/modules/ULT-23.py` (+ `ULT-23_symbols.json`). It is the ULT-13 / ST7 interface for the
  live LabStrategy (`context: [spy_fo]`, `symbols: module`, YAML `min_adv`). Smoke test
  `round3/ULT-23/test_module.py`: 3 tests pass. They cover:
  - it runs under LabStrategy and gives t1s1 / t05s1 levels;
  - a slow slide does not fire;
  - the universal SPY filter and the fail-safe with no SPY context;
  - the ATR-scaled from-open threshold;
  - the universe flags;
  - the point-in-time truncation test, which also covers the mask.
- The module is set to the frozen pick: UNIV "M", RMAX 30, EXIT "T".
- Rule as pre-registered:
  - Trigger: RSI14[prev] >= 50 and RSI14 <= RMAX within one 5-min bar.
  - Down from the open by at least min(1.0%, 0.30 x atr_d%), with atr_d% = atr_d / decision close x 100.
  - buyPressure over 19 bars > 0.
  - Universal long filter and window 10:15-15:00.
  - Intake: price >= $10, |gap| < 20%, cost_r <= 0.08.
  - Universes: Q = EQB with ADV20 >= $30M; M = non-fund stocks with point-in-time ADV20 >= $1B and price >= $20.
- Universe file. It is built from names and fund lists only, before any scoring:
  - FUNDS = ULT-20 ETF list + EQB + ULT-21 exclusions.
  - STOCKS = lab symbols minus FUNDS.
  - A first draft built STOCKS from one month's symbol list, which left out later listings (CRCL, CRWV, BMNR). This
    was fixed before scoring by using every non-locked month's names.
- Live gap: the live frame has no `symbol` / `adv20` column. Live **M** = one YAML entry with `min_adv: 1e9` and
  `symbols: module`; the mask applies price >= $20 to every row. QM would need two entries. This is not needed for the pick.
- Backtest `round3/ULT-23/bt.py`, adapted from round2/ULT-13/bt.py:
  - The chassis is unchanged: entry at the next 1-min open with LR8 costs, a 1-min walk with stops checked first, a
    45-min cap, flat by 15:50.
  - One lot per symbol, refire >= 30 min after the exit, at most 2 per symbol-session, day cap 30.
  - Long only, so there is no borrow fee. Locked block never read (no_locked asserts; MCF_HIST_ALLOW_LOCKED refused).

## Configurations
| | |
|---|---|
| Grid | 12 (23a..23l: universe {Q, M, QM} x RMAX {30, 35} x exit {t1s1 cap45, t05s1 cap45}) |
| Bias diagnostic | 1 (signal-close fill) |
| This candidate | 13, as budgeted in PLAN sec. 4. No amendment, no extra configurations. |
| Cumulative N | **880**, t floor sqrt(2 ln 880) = **3.68** |

## FIT grid (170 sessions; selection = fit total R minus the best fit day, among configs with >= 2.0/session)
| cfg | label | tr/sess | avg R | w/o best day | total R | total w/o best | A | B |
|---|---|---|---|---|---|---|---|---|
| 23a | Q-30-t1s1 | 0.006 | -0.325 | – | -0.33 | 0.00 | -0.325 | – |
| 23b | Q-30-t05s1 | 0.006 | -0.325 | – | -0.33 | 0.00 | -0.325 | – |
| 23c | Q-35-t1s1 | 0.065 | -0.026 | -0.127 | -0.29 | -1.26 | -0.028 | -0.020 |
| 23d | Q-35-t05s1 | 0.065 | -0.020 | -0.069 | -0.22 | -0.69 | -0.091 | +0.171 |
| **23e** | **M-30-t1s1** | 0.088 | **+0.326** | +0.225 | +4.89 | +2.92 | +0.525 | +0.152 |
| 23f | M-30-t05s1 | 0.088 | +0.174 | +0.126 | +2.60 | +1.64 | +0.315 | +0.049 |
| 23g | M-35-t1s1 | 0.300 | +0.027 | -0.030 | +1.36 | -1.46 | +0.015 | +0.038 |
| 23h | M-35-t05s1 | 0.300 | -0.014 | -0.042 | -0.71 | -2.03 | -0.042 | +0.014 |
| 23i | QM-30-t1s1 | 0.094 | +0.285 | +0.186 | +4.56 | +2.60 | +0.418 | +0.152 |
| 23j | QM-30-t05s1 | 0.094 | +0.142 | +0.094 | +2.28 | +1.31 | +0.235 | +0.049 |
| 23k | QM-35-t1s1 | 0.365 | +0.017 | -0.030 | +1.07 | -1.74 | +0.004 | +0.032 |
| 23l | QM-35-t05s1 | 0.365 | -0.015 | -0.038 | -0.93 | -2.24 | -0.054 | +0.030 |

- **Eligible (>= 2/session): none.** As the rule says, the best by score, 23e, was carried. It cannot reach TIER A.
- Frozen in `fitsel.json` at 2026-11-19T07:57:10Z, before any check frame was built.
- Volume is the problem. Expected was Q 0.5-1.5, M 1-3 and QM 1.5-4 a session; actual is 0.006-0.37 on fit.
- Funnel on 2025-06 universe bars (diagnostic, no outcomes read):
  - cost_r <= 0.08 removes ~74% of ETF / mega rows. Broad-index ETFs carry too little ATR% for the cost cap.
  - Of 27,315 universe bars with RSI14[prev] >= 50, only 93 collapse to <= 35 in one bar.
  - The from-open threshold cuts that to 29, and buyPressure > 0 cuts it to 8.
  - The one-bar collapse is a single-name, high-volatility event. Low-volatility baskets rarely produce it.

Fit pick 23e:
| Measure | Value |
|---|---|
| Trades | 15 (12 sessions) |
| Win rate | 0.60 |
| Avg R | +0.326 |
| Avg R w/o best day | +0.225 |
| Best day | 2025-04-07, share 40% |
| t | 2.07 |
| Sub-halves | A +0.525 (n 7), B +0.152 (n 8) |
| **Avg R without 2025-04-03..04-09** | **+0.225** (n 13) |
| Same-name random control | +0.053, signal minus random **+0.273** (n 15) |
| Signal-close fill diagnostic | +0.327 |

## CHECK — scored ONCE on 23e (276 sessions, 2025-10-01..2026-11-04)
| Measure | Value |
|---|---|
| Trades (traded sessions) | 76 (60) |
| Trades / session | **0.275** (TIER A bar 2.0: fails) |
| Win | 0.618 |
| Avg R (actual risk = 0.25 dATR unit) | **+0.139** |
| Avg R w/o best day | **+0.104** (best day 2026-06-17, +2.99R, share 28%, no 1-day tag) |
| Total R / R per session | +10.59 / +0.038 |
| Worst day / per trade-session | -1.93 / -1.527 (bar >= -2.152: passes) |
| Day-clustered t | **1.75** (bar 3.68: fails) |
| SPY up / flat / down (EOD label) | +0.065 (20) / +0.123 (37) / +0.250 (19) |
| Avg R without 2025-04-03..04-09 | +0.139 (check has no such dates) |
| Check first / second half | +0.219 / +0.072 |
| Same-name random control (same symbol-sessions, random bar 10:15-15:00, same exit) | -0.057, **signal minus random +0.197** (n 76) |
| Signal-close fill (bias diagnostic) | +0.143 (the next-1-min-open fill costs only ~0.004R) |
| Median hold / exit mix | 45 min / 57 time, 13 target, 6 stop |
| By universe | all 76 trades are M (Q was not in the pick) |

Bars:
- check avg > 0: yes.
- w/o best day > 0: yes.
- fit avg > 0: yes.
- No look-ahead: module truncation test and forbidden columns dropped.
- **>= 2.0 trades/session: NO.** So this is not TIER A.
- Not BEATS: it fails volume, and t is 1.75 < 3.68. Avg and w/o-best-day are above the benchmark, but on only 76 trades.
- TIER B: fit > 0 and check > -0.02. A near miss, never deployed.

## Check plateau (diagnostic only, never used to re-select)
| cfg | tr/sess | avg R | w/o best | best share | t |
|---|---|---|---|---|---|
| 23a Q-30-t1s1 | 0.065 | +0.099 | +0.043 | 58% | 0.66 |
| 23b Q-30-t05s1 | 0.065 | +0.114 | +0.072 | 44% | 0.96 |
| 23c Q-35-t1s1 | 0.214 | +0.032 | -0.003 | >100% | 0.28 |
| 23d Q-35-t05s1 | 0.214 | +0.035 | +0.005 | 86% | 0.35 |
| 23e M-30-t1s1 | 0.275 | +0.139 | +0.104 | 28% | 1.75 |
| 23f M-30-t05s1 | 0.275 | +0.107 | +0.091 | 18% | 1.69 |
| 23g M-35-t1s1 | 0.721 | +0.058 | +0.033 | 43% | 1.11 |
| 23h M-35-t05s1 | 0.721 | +0.013 | +0.001 | 92% | 0.33 |
| 23i QM-30-t1s1 | 0.341 | +0.132 | +0.103 | 24% | 1.76 |
| 23j QM-30-t05s1 | 0.341 | +0.108 | +0.093 | 19% | 1.84 |
| 23k QM-35-t1s1 | 0.935 | +0.052 | +0.025 | 53% | 0.99 |
| 23l QM-35-t05s1 | 0.935 | +0.018 | +0.005 | 74% | 0.44 |

- All 12 configs are positive on check. RMAX 30, the sharper collapse, is clearly better than RMAX 35 in every universe.
- t1s1 is at least as good as t05s1 at RMAX 30.
- The edge sits in the mega-cap rows. The Q basket rows are thin and noisy.
- Read: the sharper the one-bar collapse in an index-driven mega cap, the better it reverts. That fits the thesis, but
  the event is rare, and at most ~1/session even at RMAX 35.

## Honest read and next step
- The thesis is supported **in direction**. Mega-cap one-bar collapses revert, and signal minus random is about +0.2R
  in both halves. That compares with about 0.03-0.08 for the same trigger on stock bases (ULT-13).
- It cannot be a high-volume setup on this pipeline. The trigger is too rare in low-volatility names, and the 0.08
  cost cap removes most ETFs.
- The candidate is FAIL for "the goal" and TIER B overall.
- It is a good **component** for a confluence or book: the ULT-24 TL-B trigger on the BM-L base is the same idea.
  It could also be a low-rep setup for Explore / Live Lab exposure if the owner wants forward data. At 0.3/session it
  would need about a year live to say anything.
- Do not deploy as a stand-alone setup (owner: no weak setups).

Caveats:
- Today's symbol list (survivorship bias, which flatters longs); signal minus random is the survivorship-neutral read.
- Long only, so no borrow issue.
- Fills are at the next 1-min open, not the signal close; the diagnostic shows a negligible difference.
- CHECK has been read by earlier rounds (PLAN sec. 0.5).

Rule-change context: both halves are scored with one fixed rule set (today's LR8 costs, round-3 chassis). No live
rule change falls inside them. The live ledger changes listed in round-1 RESULTS.md (11-12 LR8 cost model, 10-28
Primary sizing, 10-30 Testing cost filter, 11-17 TSZ1 / SPYEXIT) do not affect these numbers.

Files (all under research/ultimate_1119/):
- modules/ULT-23.py
- modules/ULT-23_symbols.json
- round3/ULT-23/bt.py
- round3/ULT-23/test_module.py
- round3/ULT-23/fit_grid.json
- round3/ULT-23/fitsel.json
- round3/ULT-23/fit_random.json
- round3/ULT-23/check_once.json
- round3/ULT-23/check_plateau.json
- round3/ULT-23/fit_trades.csv.gz
- round3/ULT-23/check_trades.csv.gz

Educational only — not financial advice.
