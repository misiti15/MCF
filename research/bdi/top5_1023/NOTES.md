# Top-5 setup execution tune, 2026-10-23 (eighth run): FAILED the Testing bar, 0 of 80; 22 variants beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-19..10-23 (rule 7). They are a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history, production + time-of-day costs and x3 on the
  extended tier in, TRAIN (<= 2025-12) + VALID (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was
  **never loaded**. No holdout was scored, because nothing reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored; nothing was appended afterwards.
- **Configurations scored: 80** (2 CWT14 x 14, 3 short setups x 17, + 1 RW5 loser-pattern row), plus 5 parent reference
  runs. Study bar max(1.5, sqrt(2 ln 80)) = **2.96**; setup bars 2.30 (CWT14) / 2.38 (L3, RW3) / 2.40 (RW5).
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change.** 22 variants beat
  their parent, and every one of them still loses after costs in at least one period. Only 2 of 80 variants have
  exp > 0 over both periods pooled, both L3-FD wider stops. Only 1 (L3-FD E05) is positive in TRAIN and in VALID
  separately, and it does not beat its parent at the bar (t 2.05 < 2.38).
- config/, mcf/ and workflows are untouched. 27 `top5-tune` lines appended to research/backlog.jsonl (5 grids, status
  failed; 22 beats-parent, status rework); BACKLOG.md re-rendered.

## Failures first

| setup (acct) | variants | beat parent | parent exp TRAIN / VALID (t VALID) | best variant (d R; t) | best variant TRAIN / VALID |
|---|---|---|---|---|---|
| CWT14-failbrk-pdl-p05-lowvol-long (T2) | 14 | 7 | -0.095 / -0.095 (-5.38) | C02 stop x2.0: +0.052 (11.2) | -0.044 / -0.041 |
| L3-gap-slope-fromopen-FD (T1) | 17 | 1 | -0.023 / -0.006 (-0.10) | E13 skip 10:00-10:29: +0.009 (2.41) | -0.013 / -0.001 |
| CWT14-failbrk-pdl-p10-long (T2) | 14 | 7 | -0.086 / -0.091 (-5.37) | C02 stop x2.0: +0.046 (9.2) | -0.044 / -0.040 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (**Primary**) | 18 | 4 | -0.054 / -0.078 (-1.78) | E04 stop x1.25: +0.016 (3.06) | -0.036 / -0.064 |
| RW3-gapdn-rsi5pop-flowsell-short-FD (**Primary**) | 17 | 3 | -0.095 / -0.041 (-1.05) | E05 stop x1.5: +0.035 (3.76) | -0.050 / -0.024 |

**Every parent is a market-direction bet** (backtest, SPY up / down sessions, TRAIN / VALID):
- pdl-p05-lowvol long: up +0.006 / -0.015, down -0.185 / -0.153.
- pdl-p10 long: up +0.003 / -0.027, down -0.164 / -0.137.
- L3-FD short: up -0.035 / -0.078, down +0.003 / +0.150.
- RW5-FD short: up -0.212 / -0.241, down +0.132 / +0.060.
- RW3-FD short: up -0.230 / -0.199, down +0.046 / +0.059.

No execution knob turns the losing side positive. Same finding as the last seven runs.

**Flag for the owner (FYI, not a decision from this routine):** the two Primary setups scored tonight, RW5-FD and
RW3-FD, are among Primary's best live performers on 10-19..10-23 (paper: +0.40R on 54 trades, +0.54R on 43). Their
two-year as-run backtests are **-0.063R and -0.076R per trade** (4,499 and 4,800 trades). The live result also rests on
one day: 10-22 gave RW5 +19.7R of its +21.5R and RW3 +24.3R of its +23.0R. Primary is not changed here.

**Recurring live loser patterns tested:**
- **pdl-p05-lowvol, 09:50-09:59 entries** (live: 16 trades, -0.29R). Skipping them (C09) beats the parent (d +0.005 / +0.010R
  TRAIN / VALID, t 3.44) but the setup is still -0.094R. On two years that bar is about average (-0.105R vs -0.095R). This is the same
  config as top5_1019 E09; it was re-scored and counted.
- **"Never worked" losers** (pdl-p05-lowvol: 21 of 44 live losers never reached +0.2R; L3-FD: 15 of 35). A 15-minute
  time stop when best < +0.1R (C05 / E15) gives d +0.000..+0.007R on CWT14 (t 0.5-0.9) and is worse on L3-FD
  (-0.002 / -0.012R TRAIN / VALID; it cuts the slow winners).
- **L3-FD give-back to the 15:55 flatten** (58 of 114 live trades ended there). A 14:00 clock exit (E16) is clearly worse
  (d -0.040 / -0.045R TRAIN / VALID, t -1.71): the afternoon carries much of L3's winning drift.
- **RW5-FD 14:00+ entries** (live: 6 trades, -0.29R). Window end 14:00 (E18) d +0.015 / +0.007R, t 2.07 < 2.40 - not
  significant. The window end 13:00 (E12) does beat the parent (t 2.59), but the setup is still -0.051R.
- **Limit entry 0.1R better** (new knob, all 5) fills only 50-69% of signals, and R per trade is worse on all 5
  (e.g. pdl-p05-lowvol -0.131 vs -0.095R). It keeps the trades that run against you at once (adverse selection).

## Selection
Live paper trades 10-19, 20, 21, 22, 23 (run_id 1; S6 and GEN-* out; `live_rank.csv`). Account membership comes from
`docs/live/assignments.json` at 16:00 ET 10-23; Graveyard setups are out.

- **Rotated out - tuned in top5_1020 / 1021 / 1022, no change since:** CWT14 pdl-p05-long (226), RW7-FD (62),
  coil-k4 (59), MF3-FD (57), pdl-p10-lowvol-long (55, Primary), exhaustion_short-FD (46), RW4-FD (46), coil-k6 (40).
- **Cited, not redone:** NS3-failed-vwap-reclaim-short-FD (62). ns3var1022 scored 95 configurations on it on 10-22, and
  its V1 decision (NS3V1 + twin group) was applied the same day.
- **Scored:** pdl-p05-lowvol-long (115, T2; last tuned top5_1019), L3-gap-slope-fromopen-FD (114, T1; first top-5 tune,
  l3_1022 reviewed it), pdl-p10-long (99, T2; last tuned top5_1019), RW5-FD (54, Primary), RW3-FD (43, Primary).
- The CWT14 pair got only knobs that top5_1019 had not scored, so its 18 rows are not repeated. The exception is C09,
  which is declared as a re-score.

## 1. Live (paper) vs backtest

| setup | live n | live win / BE win | live avg win / loss | live avg R | bt win / BE win / exp | live losers never > +0.2R |
|---|---|---|---|---|---|---|
| pdl-p05-lowvol-long (t05s1) | 115 | 61.7 / 64.8% | +0.48 / -0.89 | -0.042 | 63.4 / 69.8% / -0.095 | 21 of 44 |
| L3-fromopen-FD (t1s1) | 114 | 69.3 / 48.3% | +0.72 / -0.68 | +0.294 | 54.1 / 55.0% / -0.017 | 15 of 35 |
| pdl-p10-long (t05s1) | 99 | 78.8 / 64.3% | +0.56 / -1.01 | +0.228 | 64.5 / 70.3% / -0.088 | 13 of 21 |
| RW5-FD (t1s1) | 54 | 74.1 / 47.9% | +0.79 / -0.73 | +0.398 | 48.6 / 52.6% / -0.063 | 5 of 14 |
| RW3-FD (t1s1) | 43 | 81.4 / 49.6% | +0.85 / -0.83 | +0.535 | 48.0 / 52.6% / -0.076 | 4 of 8 |

- **Conversion problem:** the CWT14 t05s1 longs need about 70% wins after costs (avg win +0.45R vs avg stop -1.14R).
  The backtests win 63-65%. pdl-p05-lowvol is under break-even live too. The t1s1 shorts need about 53% wins and win
  48-54% in the backtests.
- **Where live winners and losers cluster:** concentration on single days. L3-FD made +33.8R on 10-20; the other 4 days
  made -0.3R. RW5-FD and RW3-FD are mostly 10-22, a down day for longs. pdl-p05-lowvol lost on 10-19 (-10.2R) and 10-22
  (-4.8R). The history detail (`hist_parent_detail.txt`) shows no time-of-day bucket that is positive for any parent.
  Session direction dominates.
- **Random control** (same bar, random symbols, same mechanics): CWT14 pdl-p05-lowvol -0.014R and pdl-p10 -0.008R are
  *worse* than random longs. L3 +0.009R, RW5 +0.018R and RW3 +0.011R beat random shorts slightly.

## 2. Grid readout (all 85 rows in `results.csv`)

| knob | d range (t) | note |
|---|---|---|
| **C01 / C02 stop x1.5 / x2.0 (same $), CWT14** | +0.027..+0.054 (8.9-11.2) | beats parent on both. Win +5-8 pts. The curve still rises at x2.0, but the setups stay at -0.04R |
| **E04 / E05 stop x1.25 / x1.5 (same $), shorts** | +0.011..+0.045 (2.05-3.76) | beats parent on RW3 and RW5. L3 E05 becomes positive (+0.016R, TRAIN +0.010 / VALID +0.025) but t 2.05 < 2.38, VALID t 0.55, up sessions -0.016 |
| C10 skip 10:00-10:29 (CWT14) | +0.020..+0.025 (5.0) | beats parent on both. Mostly because later same-day signals replace the skipped first ones (first per symbol-day); still -0.083 / -0.091R |
| C08 / C09 / C11 / C12 windows and crash filters (CWT14) | +0.004..+0.019 (2.3-3.6) | all beat parent on both; all still -0.09R |
| E14 skip shorts while SPY up | -0.021..+0.070 | beats parent on RW3, RW5 (keeps 44-49% of trades, still negative); hurts L3 (TRAIN) |
| E12 window end 13:00 | -0.050..+0.032 | beats parent on RW5 only |
| E13 skip 10:00-10:29 | -0.012..+0.011 | beats parent on L3 only (t 2.41) |
| time stops (C05 / C06 / E01 / E02 / E15) | -0.019..+0.016 (-0.9..1.6) | flat |
| targets (C03 / C04 / E08 / E09) | -0.023..+0.009 | flat to worse |
| scale-out / breakeven (E06 / E07) | -0.077..+0.017 | win rate +12-14 pts, no better R; breakeven worse |
| clock exit 14:00 (C07 / E16) | -0.045..+0.021 | worse on L3, flat elsewhere |
| re-entry cd15 (C13) | -0.009 (-4.6 / -4.8) | worse on both CWT14 |
| limit entry 0.1R (C14 / E17) | -0.011..+0.023 (d is per parent trade) | R per trade worse on all 5; fills 50-69% |
| wait one bar (E10) | -0.011..+0.007 | flat |
| stop x0.85 (E03) | -0.031..-0.010 (-2.5..-3.7) | worse on all 3 |

## 3. Bars
- **Beats parent (22):**
  - pdl-p05-lowvol: C01 C02 C08 C09 C10 C11 C12.
  - pdl-p10: C01 C02 C08 C09 C10 C11 C12.
  - L3-FD: E13.
  - RW5-FD: E04 E05 E12 E14.
  - RW3-FD: E04 E05 E14.
- **Testing bar** (exp > 0 on TRAIN and VALID, VALID t >= 2.96, up and down sessions > 0, ex-best-day > 0, beats
  random): **0 met it.** No Testing proposal; no Primary change proposed. No holdout scored.

## Queued (not scored tonight)
- **CWT14 pdl longs, stop x2.5-x3.0 at the same $** as one paired round (rule 18), since the x1.25 -> x2.0 curve is still
  rising. They stay below zero at x2.0 (-0.04R), so this needs to add about +0.045R to break even.
- **L3-FD wide stop**: E05 (x1.5) and l3_1022 X2 (x2.0) both turn positive but are not significant and depend on one
  day (2025-04-07). Wait for forward data; no rework round proposed.

## Files
- `live_rank.py` (top5_1022's, new dates) -> `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`, `live_out.txt`.
- `scan_1023.py`: CWT14 entries come from the top5_1019 kernels; short entries come from gates1021's cached live-shaped
  signals. Exits use a copy of the top5_1019 simulator, with a limit-entry mode, a clock exit only for trades opened
  before it, and x3 extended-tier costs.
  - Parity on 2025-06: shorts 973 / 973 trades, mean |d| 0.0000R vs the cached production R. CWT14 parent counts
    1,722 / 1,558 match top5_1019's lab parity.
  - The scan takes ~3 min; the 34 MB scratch trades file was deleted.
- `report_1023.py` -> `results.csv`, `summary.json`, `hist_parent_detail.txt`; `make_proposals.py` ->
  `backlog_proposals.jsonl`.

Educational only — not financial advice.
