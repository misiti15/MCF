# Diagnosis — Late-Day ETF Dip Buy `NM-ETF-late-dip-di-long` (Primary, TEAM-6; LONG)
Educational only — not financial advice. Mechanic, 2026-11-16 (built 13:10-13:45 ET during market hours: research files only, no config touched).

Engine: `NM-ETF-late-dip-di-long_engine.png` (P1..P25, blueprint `NM-ETF-late-dip-di-long.md`).
Live evidence = **all 21 live trades** (11 sessions, 2026-10-19..11-13: Testing 2 10, Live Lab 8, Primary 3) and 25 live
signals. That is too few to diagnose by itself, so **this job leans on the 2-year backtest** (480 trades, 156 sessions;
module-parity with the arena record: train 281 trades, valid 190 lab trades reproduced exactly) and uses the live trades
only to point at parts. The live record is NOT used in the pass decision (owner 2026-11-16).
Context: the Research Guild (OBS-LATEDIP, research/guild/1114/obs-latedip/NOTES.md) called this edge "a lead at most":
no index-level late-day rebound (SPY/QQQ/IWM analog <= 0 without April 2025), live R tracks the index move during the
hold (corr 0.82), and the half-R target / 1R stop gives a high win rate by construction. If an edge exists it is
cross-sectional (which ETF dips, and in what context). This diagnosis looks for exactly that.

Rule-change context inside the live window (research/ledger.jsonl): moved Testing 2 -> Live Lab 2026-11-05 (ROLL1) ->
Primary 2026-11-11 (TEAM-6); Primary slot ~$5k -> ~$4k 10-28; Primary -2R per-setup latch 10-29; LR1 / LR3 / LR5 / LR7
from 11-12 and LR8 cost allowance from 11-12 (live R before 11-12 uses the old cost allowance). The backtests below use
LR8 costs throughout, so they are not mixed.

## The 5 worst and 5 best live trades (only 5 losers exist: every loser is a 15:55 flatten, no live stop ever hit)
Sensor values recomputed from SIP bars with the module's own indicator code (replay frames; parity 30/30 signals).
ret12 = 60-minute return % at the signal bar (includes the 15-minute dip). WB1 = the recommended copy (ret12 >= +0.5%).

| Trade (chart) | What happened | Part behind it | Catalogue part | What a small tweak does to THIS trade |
|---|---|---|---|---|
| worst1 TECL 11-04 −0.56R (`_worst1_TECL_2026-11-04.png`) | 14:25 signal (ret3 −0.82%), bought 164.96; ETF was under VWAP and sliding all afternoon (ret12 −0.71%); MFE only +0.12R; P25 flatten 15:55 @ 162.70 | P10 fires on any 15-min drop, even one that is just the next leg of a falling hour | Sensors | WB1: skipped (ret12 < +0.5) → +0.56R. Target / stop tweaks: still a flatten loser |
| worst2 SOXL 10-22 −0.14R | 14:40 signal (ret3 −1.23%) after an hour down −2.12%; MAE −0.87R, flattened 15:55 | P10 (same pattern: falling hour) | Sensors | WB1: skipped → +0.14R |
| worst3 SOXL 11-06 −0.10R | 14:30 signal (ret3 −0.94%) inside an up-hour (ret12 +2.58%); MFE +0.30R then drift; flatten | P23 target (+0.5R) not reached; P25 | Target / Time exit | WB1 KEEPS it (−0.09R in replay). Target 0.4R would not have filled either (MFE 0.30R) |
| worst4 LABD 11-13 −0.07R | 14:20 signal (ret3 −1.00%), falling hour (ret12 −0.86%); MFE +0.16R; flatten | P10 | Sensors | WB1: skipped |
| worst5 SOXL 11-04 −0.05R | 14:25, ret3 −1.78%, hour −2.01%; MFE +0.13R; flatten | P10 | Sensors | WB1: skipped |
| best1 TECL 11-05 +0.69R | 14:30, ret3 −1.92%, hour −0.19%; target in 10 min | works as designed | — | WB1 MISSES it (ret12 −0.19) — the filter costs some winners |
| best2 SOXS 10-19 +0.68R | 14:10, ret3 −0.83%, hour +1.46%; target 13 min | works | — | WB1 keeps (WB2/WB3 miss it: ret3 only −0.83) |
| best3 TZA 10-22 +0.59R | 14:20, hour −0.41%; target 17 min | works | — | WB1 MISSES it |
| best4 SOXL 11-10 +0.54R (`_best4_SOXL_2026-11-10.png`) | 14:25, ret3 −0.91%, hour +2.61% — a pullback inside a strong up-hour; target 15:52 | works | — | WB1 keeps |
| best5 SOXS 11-02 +0.53R | 15:00, hour +1.81%; target 15:30 | works | — | WB1 keeps |

**Live read:** 4 of the 5 losers were dips that continued a falling hour; WB1 drops 4 of the 5 worst (−0.82R) but also 2 of
the 5 best and 15 of 21 trades in all. On these 21 live trades WB1 keeps 6 at +0.395R avg (+2.37R) and drops 15 at +0.277R
(+4.16R): better per trade, less total R. The live sample is too small to decide anything — hence the 2-year test.

## All trades, component by component (2-year backtest, 480 trades; train ..2025-12 / valid 2026-01..10-16)
- **Exits (P22 / P23 / P25):** target 307 (64%) +0.446R; time 114 (24%) −0.116R (median MFE +0.24R, only 16% ever reached
  +0.4R); stop 59 (12%) −1.075R (27% had touched +0.3R first). Every exit tweak tested (target 0.4 / 0.6 / 0.75R, stop
  0.75 / 1.25 / 1.5R, 1R 0.20 / 0.30 ATR, flat 15:30 / 15:45, max hold 45 / 60 min, breakeven at +0.3R, lock +0.1R after
  +0.35R, exit at 45 min if MFE < 0.2R) loses on the 2-year test or the replay. The exhaust is not where it bleeds.
- **Sensors (P10 / new P10b) — the clearest pattern.** The context of the dip decides the trade. Quartiles of the
  60-minute return at the signal bar: <= −0.32% −0.007R (train +0.088 / valid −0.087), −0.32..+0.58% +0.026R
  (+0.114 / −0.053), +0.58..+1.55% +0.189R (+0.275 / +0.011), > +1.55% +0.293R (+0.298 / +0.280). Same story from VWAP
  (above VWAP by > 0.17 ATR +0.311R, train +0.337 / valid +0.229) and day position (top of the day's range +0.304R).
  A 15-minute dip inside an up-hour (a pullback) mean-reverts; a dip that extends a falling hour does not. The parent's
  DI(7) filter (P11) was meant to catch this but is too loose (di quartiles: +0.08 / +0.18 / +0.11 / +0.12R, no trend).
  Depth (P10 ret3): shallowest quartile (−0.80..−0.88%) +0.029R (valid −0.121), deeper ones +0.13..+0.17R.
- **Intake (P5 symbols / P12 ATR):** inverse ETFs +0.078R vs others +0.147R; 3x funds +0.092R vs 1x +0.235R (valid
  ≈ 0 for both); ATR% quartiles show no monotone pattern. A no-inverse universe helps train but not valid.
- **Timer (P6):** 14:15-14:30 −0.021R and 14:45-15:00 +0.092R (valid −0.187R) are the weak slots, but moving the window
  either way (start 13:30, end 14:45) loses.
- **Gates / caps (P13-P16):** 3.1 trades per session on average but up to 52 (2025-04-10); the best day (2025-04-09,
  +18.7R) is 31% of all R and April 2025 is 41R of 60R (w/o April 2025: +0.060R). A 5-per-day cap removes crash-day
  winners (−0.031R). Market gate measured after 09:50 (owner direction rule): SPY since 09:50 >= 0 lifts the 2-year test
  (+0.213R) but not the replay (+0.315R, w/o best day −0.002R).
- **Day type (end-of-day label, diagnostic only):** up +0.244R, flat +0.093R, down +0.061R.
- **Removed vs kept by WB1 (2-year):** removed 217 trades at +0.003R (train +0.116, valid −0.091), kept 263 at +0.220R
  (Welch t 4.0). The new sensor removes dead weight, not the edge.

## Candidate tweaks (one part each) → spawned
1. **WB1 — new sensor P10b: ret12 >= +0.5%** (buy the 15-minute dip only inside an up-hour). Monotone in the threshold
   (`_wb1_ret12_curve.png`: −0.5 → +1.5%: 2-year +0.17 → +0.27R, valid +0.06 → +0.32R); +0.5% is the middle of the curve.
2. **WB2 — P10 ret3 <= −0.90%** (drop the shallowest dips).
3. **WB3 — WB1 + WB2** (combo, counted as its own config).
Results and the decision: RESULTS.md.
