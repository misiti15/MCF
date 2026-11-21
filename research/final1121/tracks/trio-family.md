Educational only — not financial advice.

# Trio-family (gap-down short) expansion: overnight 2026-11-21

Research only. I made no setup, exit, config, account or ledger change, and the PROT-06/07/09/26 parents are untouched. **20 configurations tried** in 10 sibling ideas (round 1: 7 ideas / 14 configs; round 2: 3 ideas / 6 configs). WB2 bar for N=20: max(1.5, sqrt(2 ln 20)) = **2.45**. The locked block 2024-11-01..2025-02-28 was never read; bench10's guards and asserts stayed on.

## Engine and validation
- **Engine:** research/ultimate_1119/top10/bench10.py functions, used unchanged: chain, 1-minute walk, LR8 costs plus 1.2 bp borrow, and the testing book (cap 100, cf 0.15R, 3 lots/symbol, $5, ETB >= 0.9).
- **Validation:** a reference row REF-L3 (the live L3-fromopen mask) reproduces benchmark.json's testing-rules numbers exactly. FIT: 4,926 trades at -0.068. CHECK: 8,183 at -0.071. T2: 1,975 at +0.045.
- **Periods:** FIT = 2024-10 + 2025-03..09 (170 sessions). CHECK = 2025-10-01..2026-11-04 (276 sessions), scored once and only for finalists. T2 = 2023-01..2024-09 (427 sessions, 469 symbols).
- **Selection rule (pre-registered):** best FIT config per idea; dropped if FIT avg <= -0.05 with t <= -2.
- **Important caveat:** in this engine the parents are negative as well. REF-L3 T1 combined is -0.070 with t -2.29, which is PLAN.md's REALLY BAD definition. The earlier src_value study found that off-live sources have no skill at ranking setups. Read every level below as relative to the parents, not as an absolute verdict.

## Results: finalists (CHECK and T2 scored once)
| sibling | T1 combined n / avg / w/o best / w/o top2 / t | CHECK n / avg / w/o best / t | T2 n / avg / w/o best / t | overlap with trio raw / booked symbol-days | verdict |
|---|---|---|---|---|---|
| **R2c L3-atrrec-k0.9** (gap <= -2.657, slope > 0.3724, fromOpen <= 3.46, recovery >= 0.9 ATR) | 606 / **+0.132** / -0.088 / -0.107 / 0.85 | 224 / -0.017 / -0.039 / -0.21 | 220 / **+0.087** / -0.006 / 0.78 | 55% / 37% | **Tier B candidate** (debatable / derived from L3-fromopen) |
| **R2b L3-smallgap-f2.5** (-2.657 < gap <= -1.5, slope > 0.3724, fromOpen > 2.5) | 15,930 / -0.076 / -0.086 / -0.094 / -1.93 | 11,025 / -0.0485 / -0.060 / -1.44 | 2,793 / -0.024 / -0.043 / -0.46 | **1.4% / 1.3%** | near-miss (Tier B by the letter of PLAN.md; not recommended to force) |
| R2a L3-midrec (2.0 < fromOpen <= 3.46) | 6,370 / -0.107 / -0.116 / -0.126 / -2.47 | 3,979 / -0.086 | 1,172 / -0.069 | 53% / 20% | fail (REALLY BAD) |
| S6 PDL-reject (gap <= -2, rsi5 > 70, bounce to the prior-day low) | 10,069 / -0.095 / -0.105 / -0.114 / -2.43 | 6,931 / -0.081 | 1,810 / -0.111 (t -3.19) | 17% / 8% | fail (REALLY BAD) |
| *REF-L3 (parent, reference only)* | 13,109 / -0.070 / -0.076 / -0.082 / -2.29 | 8,183 / -0.071 | 1,975 / +0.045 | 100% | parent |

R2c is a one-day record. 2025-04-07 is 144% of its T1 total R, and its T2 best-day share is 105%. That fails the owner's one-big-day check, so it must be called out wherever it is shown. It also trades rarely: 0.8 trades/session on CHECK and 0.5 on T2.

## Results: dropped on FIT (CHECK not scored)
| idea | configs | FIT avg / t (best config) | lesson |
|---|---|---|---|
| S1 RW3 mask on ADV 20-95M | 2 | -0.096 / -2.25 | 2nd-tier liquidity does not carry RW3's edge |
| S2 L3 with the slope layer inverted | 2 | -0.104 / -2.97 | the uptrend layer carries L3 |
| S3 RSI5 pop without RW's flow conditions | 2 | -0.139 / -3.11 | the flow-sell layer matters (as RSI did in RW3S) |
| S4 pop then turn (enter after rsi5 rolls over) | 2 | -0.119 / -2.81 | waiting for the turn does not help |
| S5 sector/index ETF gap-down pop | 2 | -0.227 / -3.16 | ETFs do not fade the same way |
| S6 b0.15 (PDL band) | 1 | -0.128 / -1.73 | (b0.30 was the finalist) |
| S7 trio signal delayed 15/30 min | 2 | -0.093 / -2.27 | delaying the trio's own entry does not improve it in backtest |
| R2a f2.7, R2b f3.46, R2c k0.6 | 3 | -0.143 / -0.157 / -0.039 | R2c k0.6 is the higher-activity version (6.2 trades/session), FIT unbooked +0.084, booked w/o best day -0.129 |

## Matched random-entry nulls (unbooked, same filters, 5 reps each)
- **L3-family entries beat a random bar on the same symbol-day by a wide margin.**
  - REF-L3: CHECK day t +15, T2 +11.
  - R2b: +14.5 / +12.6.
  - R2c: +4.0 / +3.4.
  - So picking the bar after a strong recovery adds value compared with a random time that day.
- **They are level with a random entry 1 to 6 bars later,** the same as the live null study found.
- **S6 and the RW-side ideas are level with both nulls.**

## Primary fit
- **R2b:** in the live window (10-06..11-04, 22 days), its backtest daily R correlates -0.18 with live Primary. It makes +41.9R on Primary's 16 red days (9 helped) and +2.7R on green days. That is the best "red-day" profile found. Over the full CHECK, though, it loses on the trio's red days as well (-1,044R).
- **R2c:** correlation -0.38, +2.2R on red days (tiny size). Correlation with the trio's backtest days is about 0.
- **S6 / R2a:** both have positive correlation with Primary and lose on red days.

## Recommendation
1. **R2c (L3-gap-slope-atrrec-k09-short)** is the only sibling worth testing-arena exposure, as Tier B (debatable / derived from L3-fromopen-FD). It takes L3-style stock-days that L3 rejects only because 3.46% is too large a move for lower-volatility names. Do not judge it before about 15 active days; its backtest rests on one day.
2. **R2b** could go to the backlog as a Workbench copy only if slots are free. It is the cleanest "new stock-days" expansion (1.4% overlap), but it is negative on every period and heavy (40 trades/session). Do not force it.
3. **Stop expanding the RW side.** Tier-2 liquidity, dropping the flow layer, ETFs, pop-fail and delayed entry all failed on FIT. RW3/RW5's live edge does not generalise in this engine.

## Rule-change context
- **Backtests:** today's rules apply to every session, so no rule change falls inside them.
- **Live Primary comparison window (10-06..11-04):**
  - Primary ~$4k slots and per-setup cap 30 (10-28);
  - -2R latch (10-29);
  - L3-fromopen moves (10-20, 10-22, 10-30);
  - L3-rsi5hi in Primary (10-30).

## Files
All files are in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/trio-family/ (about 120 MB):
- Code: gd.py, gd_t2.py, score.py, combo.py, diag.py
- Pre-registration: prereg.json (round 1)
- Scores: score_fit_trades_fit.json, score_fit_r2_trades_fit.json, score_check_trades_check.json, score_t2_trades_t2.json, combined.json
- Draft modules: modules/L3-gap-slope-atrrec-k09-short.py, modules/L3-smallgap-slope-fromopen-f25-short.py

Educational only — not financial advice.

## Robustness

null