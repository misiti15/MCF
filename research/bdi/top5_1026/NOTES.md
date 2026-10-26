# Top-5 setup execution tune, 2026-10-26 (ninth run): FAILED the Testing bar, 0 of 86; 20 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-20..10-26 (rule 7). They are a diagnosis, not evidence.
  10-26 started ~10:39 ET (missed schedule), so that day has no 09:50-10:39 trades.
- History numbers are **backtests** on the open two-year history, production + time-of-day costs and x3 on the
  extended tier in, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was
  **never loaded**. No holdout was scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 86** (pdl-p05-long 16, NS3-FD 18, MF2-FD 17, MF4-FD 18, L3-rsi5hi-FD 17), plus 5 parent
  reference runs. Study bar max(1.5, sqrt(2 ln 86)) = **2.98**; setup bars 2.35-2.40.
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.** 20 variants beat
  their parent, and every one still loses after costs in at least one period. Only 4 of 86 variants have exp > 0 over
  both periods pooled. Only 2 are positive in TRAIN and VALID separately (NS3-FD E05 stop x1.5 +0.019 / +0.003R, and
  NS3-FD E12 window end 13:00 +0.017 / +0.081R). Neither beats its parent at the bar (t 2.26 and 0.78 vs 2.40), and
  both lose in up sessions.
- config/, mcf/ and workflows are untouched. 25 `top5-tune` lines appended to research/backlog.jsonl (5 grids, status
  failed; 20 beats-parent, status rework); BACKLOG.md re-rendered.

## Failures first

| setup (acct) | variants | beat parent | parent exp TRAIN / VALID (t VALID) | best variant (d R; t) | best variant TRAIN / VALID |
|---|---|---|---|---|---|
| CWT14-failbrk-pdl-p05-long, Failed Prior-Day-Low Break Long (shallow) (T1) | 16 | 7 | -0.068 / -0.068 (-6.12) | C02 stop x2.0: +0.037 (11.9) | -0.033 / -0.028 |
| NS3-failed-vwap-reclaim-short-FD, Big Loser VWAP Reclaim Fade (all day) (T2) | 18 | 1 | -0.004 / -0.018 (-0.55) | E04 stop x1.25: +0.015 (2.59) | +0.013 / -0.006 |
| MF2-open-rsimidhi-flowsell-FD, Early Sellers, Mid-High RSI (all day) (**Primary**) | 17 | 2 | -0.055 / -0.194 (-3.13) | E05 stop x1.5: +0.074 (2.63) | +0.006 / -0.105 |
| MF4-h40-open-flowsell-FD, Early Sellers, Strong Heat (all day) (**Primary**) | 18 | 8 | -0.119 / -0.071 (-2.84) | E05 stop x1.5: +0.034 (5.80) | -0.076 / -0.052 |
| L3-gap-slope-rsi5hi-FD (T2; no display name in setup_names.yaml) | 17 | 2 | -0.084 / +0.011 (0.30) | E04 stop x1.25: +0.020 (3.24) | -0.055 / +0.017 |

**Every parent is a market-direction bet** (backtest, SPY up / down sessions, TRAIN+VALID): pdl-p05-long -0.010 /
-0.115; NS3-FD -0.107 / +0.046; MF2-FD -0.360 / +0.000; MF4-FD -0.197 / -0.011; L3-rsi5hi-FD -0.078 / +0.003. No
execution knob turns the losing side positive. Same finding as the last eight runs.

**Flag for the owner (FYI, not a decision from this routine):** both Primary setups scored tonight lose over two years
as run: MF2-FD **-0.117R/trade** (4,049 trades, VALID t -3.13), MF4-FD **-0.101R/trade** (5,807, VALID t -2.84). MF2-FD's
live record (+1.07R on 33 paper trades) is one day: 10-22 gave +29.6R of its +35.2R (84%); without it, +0.56R on 10
trades. MF4-FD's live +0.08R is 103% one day (10-20); without it, -0.005R. Primary is not changed here.

**Recurring live loser patterns tested:**
- **pdl-p05-long "never worked"** (live: 36 of 68 losers never reached +0.2R; bdi1026: CWT14 pdl/orl longs on 11 of
  the last 10-12 sessions). A 15-minute time stop (C05) gives d +0.001 / +0.004R TRAIN / VALID, t 1.10. It is not
  significant. In history 10,425 of 15,699 losers never work, and cutting them also cuts the slow winners.
- **pdl-p05-long 10:30-11:29 entries** (live: 46 trades, -0.18R). Skipping them (C15) beats the parent (d +0.016 /
  +0.009R, t 4.61). On two years that hour is the worst bucket (-0.086R vs -0.068R), but the setup stays at -0.065R.
- **Index-chase veto** (10-26: longs bought at the 11:02 index high). Skipping longs when SPY is up > 0.5% (C16) gives
  d +0.002 / +0.003R, t 1.61. Not significant.
- **NS3-FD give-back** (live: 10 of 32 losers reached +0.5R first). Breakeven after +0.5R (E07) is worse (d -0.047 /
  -0.014R, t -2.45), and the half scale-out at +0.5R (E06) is worse too (t -1.51). Win rate rises 10 points, but R per trade falls.
- **NS3-FD 10:00-11:29 entries** (live: 14 trades, -0.58R, 1 win). Window start 11:30 (E18) is worse (t -1.61). On two
  years the morning is NS3-FD's *best* time (10:00-10:30 +0.168R). The live cluster is a session effect (10-21: 26
  trades, -11.3R).
- **MF4-FD 11:30-13:00 entries** (live: 11 trades, -0.23R). Window end 11:30 (E18) beats the parent (d +0.044 /
  +0.043R, t 4.51), but the setup still loses: -0.131 / -0.049R.

## Selection
Live paper trades 10-20, 21, 22, 23, 26 (run_id 1; S6 and GEN-* out; `live_rank.csv`). Account membership comes from
`docs/live/assignments.json` (last change 10-25 21:30 ET). Graveyard setups are out (pdh-p10-short 75,
pdh-p05-lowvol-short 54).

- **Rotated out: tuned in top5_1021 / 1022 / 1023, no change since.** L3-fromopen-FD (149), coil-k4 (104), pdl-p05-lowvol
  (102), pdl-p10 (88), RW7-FD (57), RW5-FD (51), pdl-p10-lowvol (49), coil-k6 (48), MF3-FD (44), exhaustion-FD (43),
  RW3-FD (34), RW4-FD (33).
- **Cannot be backtested: CWT13-vwapstretch-z05-long** (39; Stretched Below VWAP Bounce; Primary since 10-26). It is not
  in the two-year signal cache (it needs 09:35-09:45 head rows), and the top-5 harness has no CWT13 kernel. The next
  setup was taken instead.
- **Scored:** pdl-p05-long (211, T1; last tuned top5_1020), NS3-FD (45, T2; cited but not tuned in 1021 / 1023),
  MF2-FD (33, Primary), MF4-FD (33, Primary), L3-rsi5hi-FD (32, T2). The last three have never been top-5 tuned.

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | live w/o best day (share) | bt win / BE win / exp | bt w/o best day | live losers never > +0.2R |
|---|---|---|---|---|---|---|---|---|
| pdl-p05-long | 211 | 67.8 / 66.0% | +0.45 / -0.88 | +0.023 | -0.068 (10-20, 338%: **1 day**) | 70.6 / 76.6% / -0.068 | -0.069 | 36 of 68 |
| NS3-FD | 45 | 28.9 / 55.3% | +0.40 / -0.50 | -0.240 | -0.328 (total < 0) | 50.7 / 51.5% / -0.011 | -0.029 | 8 of 32 |
| MF2-FD | 33 | 72.7 / 34.0% | +1.82 / -0.94 | +1.067 | +0.560 (10-22, 84%: **1 day**) | 37.1 / 41.5% / -0.117 | -0.138 | 2 of 9 |
| MF4-FD | 33 | 66.7 / 60.3% | +0.48 / -0.73 | +0.078 | -0.005 (10-20, 103%: **1 day**) | 61.0 / 68.3% / -0.101 | -0.105 | 5 of 11 |
| L3-rsi5hi-FD | 32 | 90.6 / 62.3% | +0.57 / -0.94 | +0.429 | +0.399 (10-26, 59%: **1 day**) | 66.5 / 69.6% / -0.047 | -0.066 | 3 of 3 |

- **Conversion problem.** pdl-p05-long with its 0.25R scale-out needs 77% wins in the backtest and gets 71%. The
  t05s1 shorts (MF4, L3-rsi5hi) need 70% and get 61-67%. NS3-FD is close to break-even (50.7 vs 51.5%). MF2-FD's 2:1
  geometry needs 41.5% and gets 37%.
- **Live exits:** NS3-FD closed 35 of 45 trades at the 15:55 flatten (-0.16R avg). Only 3 hit the target. That is
  partly the 10-21 cluster (26 trades). In the backtest 48% of NS3-FD trades are flattened (-0.045R).
- **Random control** (same minute, same mechanics): pdl-p05-long -0.009R and MF4-FD -0.017R are *worse* than random.
  NS3-FD +0.054R, MF2-FD +0.060R and L3-rsi5hi-FD +0.012R beat random shorts, but the random shorts themselves lose
  after costs.

## 2. Grid readout (all 91 rows in `results.csv`)

| knob | d range (t) | note |
|---|---|---|
| **stop x1.25 / x1.5 / x2.0 at the same $ (C01 C02 E04 E05)** | +0.015..+0.074 (2.26-11.9) | beats the parent on all 5 except NS3 E05 (t 2.26). Win rate +2-14 pts. Same finding as every run since 10-19. MF2 x1.5 is +0.006 TRAIN / -0.105 VALID |
| windows / skips (C08-C10 C15, E11-E13, E18) | -0.010..+0.046 | beat the parent on pdl-p05-long and MF4. All still -0.05..-0.13R |
| SPY filters (C11 C16 E14) | +0.002..+0.056 (0.70-3.29) | MF4 E14 beats the parent (keeps 49% of trades) and still loses; elsewhere flat |
| stock-crash filter (C12) | +0.005 (4.10) | beats the parent on pdl-p05-long; still -0.069R |
| time stops (C05 C06 E01 E02 E15) | -0.018..+0.008 (-2.95..1.10) | flat to worse; worse on NS3 (t -2.3..-3.0) |
| scale-out / breakeven (E06 E07) | -0.035..+0.020 (-2.45..2.61) | MF4 E06 (scale half at +0.25) beats the parent (t 2.61), -0.081R; worse on NS3 and L3 |
| targets (C03 C04 E08 E09) | -0.018..+0.022 | pdl-p05-long target 0.75R clearly worse (t -12.4) |
| tighter stop x0.85 (E03) | -0.018..+0.036 (-4.60..2.11) | worse on NS3 / MF4 / L3; MF2 t 2.11 (< bar) |
| limit entry 0.1 better (C14 E17) | per parent trade | fills 54-66%; R per trade worse on all 5 except NS3 (+0.008, t 0.80) |
| re-entry cd15 (C13), wait one bar (E10), clock exit 14:00 (C07 E16) | -0.020..+0.011 (-8.38..2.26) | flat to worse; MF4 clock exit t 2.26 < bar |

## 3. Bars
- **Beats parent (20):**
  - pdl-p05-long: C01 C02 C08 C10 C11 C12 C15.
  - NS3-FD: E04.
  - MF2-FD: E04 E05.
  - MF4-FD: E04 E05 E06 E11 E12 E13 E14 E18.
  - L3-rsi5hi-FD: E04 E05.
- **Testing bar** (exp > 0 on TRAIN and VALID, VALID t >= 2.98, up and down sessions > 0, ex-best-day > 0, beats
  random): **0 met it.** No Testing proposal; no Primary change proposed. No holdout scored.
- NS3-FD E05 (stop x1.5, same $) is the same idea as NS3V1-am-widestop-short (ns3var1022 V1, already in Testing 2 since
  10-22). Tonight's all-day version is +0.011R (t VALID 0.12) and -0.069R in up sessions, so it adds nothing to V1.

## Queued (not scored tonight)
- CWT13-vwapstretch-z05-long needs a CWT13 kernel in the history harness (09:35-09:45 head rows) before it can be tuned.
- The stop-width curve on pdl-p05-long is still rising at x2.0 (-0.031R). That is the same as the queued CWT14 pdl x2.5-x3.0
  round from top5_1023. One paired round covers all CWT14 pdl longs.

## Files
- `live_rank.py` (top5_1023's, new dates) -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `build_cache.py`: rebuilds gates1021's live-shaped signal cache (scratch) for the 4 short setups (the 10-21 cache was
  gone). It uses gates1021 `scan.month_job` unchanged and takes ~2.5 min.
- `scan_1026.py`: pdl-p05-long entries come from the top5_1019 kernels; short entries come from the rebuilt cache. Exits
  use the top5_1023 simulator. **Parity:** each short parent's simulated R equals the cached production R on all rows
  (NS3 17,762 / MF4 7,273 / L3-rsi5hi 10,006 / MF2 5,235; mean |d| <= 0.00004R, 100% within 0.01R). The cache stores
  MF2 R in units of 0.25 ATR (half its stop), so MF2 rows and its random control are rescaled to units of the live
  stop. The pdl-p05-long parent (-0.0649R on all open months) matches top5_1020 (-0.0648R). The scan takes ~3 min, and
  the scratch trades file was deleted.
- `report_1026.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`. `make_proposals.py` ->
  `backlog_proposals.jsonl`.
- Short MFE / MAE in `results.csv` and `hist_parent_detail.txt` are in units of 0.25 ATR (for MF2 that is half a stop).

Educational only - not financial advice.
