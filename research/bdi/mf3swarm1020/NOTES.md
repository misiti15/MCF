# mf3swarm1020 - MF3 "Early Sellers into a Pop": live autopsy + pre-declared swarm (2026-10-20)

*Educational only - not financial advice. History = backtest on the open 2-year frames at production cost; live = paper
(rule 7). The locked block 2024-11-01..2025-02-28 was never loaded. No holdout was scored.*

## Failures first
- **No variant qualified.** 87 configurations, exactly as declared in PLAN.md. **0 of 87 have positive expectancy on
  train**; 2 of 87 are positive on valid. Nothing beats the parents on train and valid with valid t >= 1.5 at exp > 0, so
  there are **no candidate modules**; nothing clears the study bar (t >= 2.99) or the MF-family lineage bar (4.86).
- **Why: MF3 is a down-tape bet.** Every one of the 87 configurations loses in up sessions (-0.17 to -0.52R) and most win
  in down sessions (-0.04 to +0.20R). The parent FD: up -0.285R (n 3,512), flat -0.036R, down +0.093R (n 3,472). The
  "bouts of success" are the down days. No point-in-time filter at entry fixes the up-day losses: with QQQ < 0 at
  entry the up-session result is still -0.30R.
- **The exits do not fix it.** t05s1, t1s05, t05s05, hold, holdtr, the 30/60-minute time stops and r_atr_frac 0.1875
  were all worse than or equal to the parent. A wider stop at the same $ risk (r 0.5) was least bad (-0.043R overall), but
  it was still negative on train and valid.
- **Refire is worse** (-0.057R valid). The parents already take one entry per symbol per day.
- The live autopsy has n = 125 over 9 sessions, is in-sample and has an SE of about 0.08R. Its strongest splits come from
  4-5 market days.

## 1. Live autopsy (paper, 2026-10-08..10-20, Primary + Testing 1, 125 trades) - autopsy_out.txt, live_trades.csv
| split | n | avg R (costs in) | win |
|---|---|---|---|
| all | 125 | -0.129 (SE 0.084) | 51% |
| W 950-1100 / FD 950-1500 | 35 / 90 | -0.116 / -0.135 | 51% / 51% |
| entry 09:50-10:15 / 10:15-11:00 / 11:00-13:00 / 13:00-15:00 | 44 / 39 / 21 / 21 | -0.43 / -0.21 / +0.36 / +0.15 | 34/46/67/81% |
| QQQ < 0 at entry / QQQ >= 0 (shorting against the index) | 78 / 47 | +0.02 / -0.38 | 60% / 36% |
| QQQ session down / flat / up | 55 / 30 / 40 | +0.03 / -0.41 / -0.14 | |
| gap <= 0 / gap > 0 | 35 / 90 | +0.30 / -0.30 | |
| below VWAP / above | 42 / 83 | +0.09 / -0.24 | |
| adv20 tercile low / mid / high | 42 / 41 / 42 | -0.35 / -0.14 / +0.09 | |
| flowsell bp <= -0.5 / -0.5..-0.35 / -0.35..-0.25 | 12 / 45 / 68 | -0.56 / +0.08 / -0.19 | |
| RSI5 70-80 / 80-90 / 90+ | 36 / 52 / 37 | -0.07 / -0.19 / -0.10 | |
- Never worked (MFE < +0.2R): 8.8%. Median MFE +0.64R, median MAE -0.66R. 21 of 60 losers had reached +0.5R first
  (give-back), and stop exits average -1.14R after costs. The stop distance is 0.25 x daily ATR by construction, and
  stop/ATR terciles barely differ.
- Days: 10-12..10-15 were +0.18 to +0.68R. 10-16, 10-19 and 10-20 were -0.19, -0.42 and -0.28R, with 83 of the 125 trades.
- **History check of the autopsy splits (P-FD base, valid):**
  - The directions mostly hold: gap <= 0 (-0.036 vs -0.051R), QQQ < 0 (-0.053R, but better on train), high adv (1B:
    +0.009R valid, -0.120R train).
  - The early window is the worst (950-1015: -0.122R overall).
  - **Below VWAP is worse on history** (-0.093R valid), which contradicts the live sample.
  - **The extreme-flow cut does nothing** (bp band -0.047R).

## 2. Swarm (87 configs, PLAN.md; results.csv has every row, scan_out.txt the table)
Simulator check: sim t1s1 on P-FD is -0.0765R vs frame outcome + gates.prod_r -0.0752R (n 10,564). It matches swarm1017's
-0.075R.

| config | train n / exp / t | valid n / exp / t | trades/day | up / down sess. | xs vs random (t) |
|---|---|---|---|---|---|
| P-W (parent, 950-1100) | 2,382 / -0.124 / -3.07 | 1,754 / -0.034 / -0.78 | 9.7 | -0.30 / +0.14 | -0.006 (-0.31) |
| P-FD (parent, 950-1500) | 5,662 / -0.099 / -4.05 | 4,902 / -0.051 / -2.05 | 24.8 | -0.29 / +0.09 | -0.004 (-0.30) |
| **qqq<0 & gap<=0** (best near-miss) | 991 / -0.010 / -0.27 | 1,108 / -0.010 / -0.20 | 4.9 | -0.26 / +0.09 | +0.037 (1.76) |
| spy<0 & gap<=0 | 938 / -0.043 / -0.93 | 1,118 / +0.001 / 0.02 | 4.8 | -0.35 / +0.09 | +0.033 (1.50) |
| FD adv>=1B | 371 / -0.120 / -2.23 | 373 / +0.009 / 0.17 | 1.7 | -0.31 / +0.10 | +0.016 (0.52) |
| FD gap<=0 | 2,205 / -0.058 / -1.77 | 2,127 / -0.036 / -1.02 | 10.2 | -0.29 / +0.12 | +0.020 (1.35) |
| FD r0.5 (wider stop, same $) | 5,662 / -0.062 / -3.36 | 4,902 / -0.020 / -1.08 | 24.8 | -0.21 / +0.12 | -0.007 |
| win1100-1500 | 3,496 / -0.087 / -3.22 | 3,282 / -0.061 / -2.16 | 15.9 | -0.27 / +0.07 | -0.004 |
| FD t05s05 | 5,662 / -0.103 / -8.81 | 4,902 / -0.058 / -4.47 | 24.8 | -0.17 / -0.03 | -0.001 |
| FD heat<=-40 (worst) | 1,568 / -0.163 / -4.63 | 1,156 / -0.113 / -2.90 | 6.0 | -0.35 / +0.01 | -0.072 (-3.6) |

- 35 of 87 beat P-FD on both train and valid. Every one of them is still negative on train.
- **Plateau:** no neighbourhood is positive on train and valid, so the plateau score is 0 everywhere.
- **Random entries:** the index-down and no-gap-up filters beat same-minute random shorts by about +0.02 to +0.04R (t up
  to 1.76). Random shorts are themselves negative after costs, so the filters make MF3 "less bad", not profitable.

## 3. Near-miss (NOT a candidate) - `modules/NM-MF3-qqqdn-gapdn-FD.py`
- **Name:** "MF3-qqqdn-gapdn-FD", Early Sellers into a Pop (index down, no gap up). Its rule is the parent plus
  `qqq_fo < 0` and `gap <= 0`.
- **History:** about breakeven (-0.010R train and valid, 2,099 trades, ~4.9/day). The parent FD is -0.077R. It fails the
  regime gate (up sessions -0.26R) and walk-forward (0.47).
- **Live:** in-sample paper, 18 trades on 5 days, +0.62R. The filter was suggested by these trades, so this is not evidence.
- The module reproduces the scan exactly (2,099 trades, -0.0102R).
- **Use:** forward observation in Testing only, if the owner wants it, judged on >= 20 sessions / 60 trades.
- **Proposed YAML (not applied):**
```yaml
  NM-MF3-qqqdn-gapdn-FD:          # near-miss, mf3swarm1020: forward observation, NOT a candidate
    enabled: true
    type: lab
    module: research/bdi/mf3swarm1020/modules/NM-MF3-qqqdn-gapdn-FD.py
    context: [qqq_fo]
    min_adv: 95000000
    window: [950, 1500]
    scale_out_r: null
    tags: [near-miss, mf3swarm1020, forward-observation]
```
(The parents run without refire, so no refire keys are set.)

## Files
- PLAN.md: the pre-declaration.
- autopsy_fetch.py, autopsy.py, autopsy_out.txt, live_trades.csv: the live autopsy.
- build.py: the history superset and the same-minute random baseline. Scratch, deleted.
- scan.py, results.csv, candidates.csv (empty), scan_out.txt: the swarm.
- modules/: the near-miss module.
- backlog_proposals.jsonl: proposals only. research/backlog.jsonl was not edited.

Educational only — not financial advice.
