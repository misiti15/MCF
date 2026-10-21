# top5_1021 pre-declaration: execution variants of the top live setups (sixth run)

*Educational only - not financial advice.*

Written 2026-10-21 ~22:25 UTC after the live ranking (`live_rank.py`, live paper trades only) and **before any history
configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards.

## 1. Selection (live, rule 7: paper)
Sessions 2026-10-15, 16, 19, 20, 21; Primary + Testing 1 + Testing 2 reports (`origin/mcf-data*`), run_id 1, S6 and GEN-*
out, "-FD" copies are their own setup (`live_rank.csv`).

**Out - tuned in the last 3 runs (top5_1016 / 1019 / 1020) with no change since:** CWT14 pdl-p05 (177), pdh-p05-lowvol-short
(147, also N6), pdh-p10-short (131, also N6), pdl-p05-lowvol (106), pdl-p10 (106), RW7-FD (59).
**Out - in the Graveyard since 10-21 (no longer in Primary / T1 / T2):** the 4 CWT14 ORL longs, heat_fade_short(-FD),
heat_fade_long(-FD), RW2-FD, LIQ-orl, NS2(-FD), MF1-FD, ST1-FD, ST2-FD, RW6-FD, CWT09-gapdn-bounce.

**Top 5 eligible by live count:**

| setup | acct | live n | note |
|---|---|---|---|
| CWT12-coil-k4-long | T2 | 112 | tuned 10-15 / 10-16; the 10-16 run led to the live 0.35R scale-out (a change), so eligible |
| L3-gap-slope-fromopen-FD | P, T1 | 112 | **cited, not redone**: gates1021 scored 30 tweaks on it tonight, none pass |
| MF3-open-flowsell-rsi5hi-FD | P, T1 | 74 | **cited, not redone**: MF3 family swarmed 10-20 (mf3swarm1020); gates1021 G1 gate tonight. No execution harness for MF3 here tonight -> queued |
| NS3-failed-vwap-reclaim-short-FD | P, T1 | 62 | **cited, not redone**: gates1021 tweaks tonight; proposed for demotion (N5) |
| CWT14-failbrk-pdh-p10-lowvol-short | T2 | 60 | scored; **proposed for the Graveyard tonight (N6)** |

**Rotated in to replace the three cited setups (next eligible CWT, same harness):**
CWT14-failbrk-pdl-p10-lowvol-long (51, Primary since 10-21) and CWT12-coil-k6-long (49, T1 + T2).
**Scored here: 4 setups.**

Parents (live config): coil-k4 = `CL.b4a(nco=4)`, t05s1, [950,1130], scale-out 0.35R; pdh-p10-lowvol-short =
`b3(PD, p=0.10, lowvol, short)`, t05s1, [950,1500], no scale-out; pdl-p10-lowvol-long = `b3(PD, p=0.10, lowvol, long)`,
t05s1, [950,1500], no scale-out; coil-k6 = `b4a(nco=6)`, **t1s05** (target 1.0, stop 0.5 x 0.25 ATR), [950,1130], no
scale-out. min_adv 95M, flat 15:55, one trade per symbol-day.

## 2. Harness, data, costs, splits
`top5_1020/scan_1020.py` / `top5_1019/scan_1019.py` sim unchanged (stop first, management from next bar, costs: entry 1c +
1 bps x ToD, limits free, stops +2c, market exits 1c + 1 bps). Open months only; the locked block
2024-11-01..2025-02-28 is never loaded. TRAIN <= 2025-12; VALID 2026-01..03 + 07..09-15; HOLD scored once only for a
Testing candidate. Random control: 5 same-minute random symbols, seed 20261021. Stop-distance rows at the same $ risk
(target and scale prices fixed; r divided by stop / parent stop). Parity gate on 2025-06: kernels = live lib; P (no
scale-out parents) / R0 (coil-k4) = `gates.lab_trades` (mean |d| < 0.002R, >= 99% within 0.01R).

## 3. Grid (one knob per row; every row counts)
| id | knob | coil-k4 (scale 0.35) | no-scale parents (t05s1) | coil-k6 (t1s05) |
|---|---|---|---|---|
| R0 | scale-out toggle | no scale-out | scale half at 0.25 | scale half at 0.5 |
| E01 | time stop 30 min, best < +0.2 (units of 0.25 ATR) | yes | yes | yes |
| E02 | time stop 60 min, best < +0.25 | yes | yes | yes |
| E03 | tighter stop x0.85 (same $) | yes | yes | yes |
| E04 | wider stop x1.25 (same $) | yes | yes | yes |
| E05 | wider stop x1.5 (same $) | yes | yes | yes |
| E06 | scale-out alt 1 | 0.25 | 0.35 | 0.25 |
| E07 | scale-out alt 2 | 0.45 | 0.15 | 0.75 |
| E08 | wait one bar | yes | yes | yes |
| E09 | window start 10:00 | yes | yes | yes |
| E10 | window start 10:30 | yes | yes | yes |
| E11 | window end 11:00 | yes | yes | yes |
| E12 | skip after 10:30 against SPY's move | yes | yes | yes |
| E13 | re-entry, 30-min cooldown | yes | yes | yes |
| T1 / T2 | threshold -20% / +20% (b3 p; coil tightness 0.5) | yes | yes | yes |
| E14 | loser pattern (bdi1021 queue): breakeven after +0.25 units (= live +0.5R) | - | - | coil-k6 only |
| E15 | breakeven after +0.5 units (= live +1.0R) | - | - | coil-k6 only |

**N (study) = 16 x 3 + 18 = 66.** Study bar max(1.5, sqrt(2 ln 66)) = **2.89**; setup bar (N 16) 2.35, coil-k6 (N 18) 2.40.

## 4. Bars (fixed now, same as top5_1020)
- **Beats parent** (backlog, tag `top5-tune`): d > 0 on TRAIN and VALID and day-block bootstrap t_improve (1,000, seed
  20261021) >= setup bar.
- **Testing candidate:** beats parent, VALID day-clustered t >= 2.89 with exp > 0 on TRAIN and VALID, up and down
  sessions each > 0, ex-best-day > 0, excess over random > 0; then HOLD once. Otherwise no proposal.
- Every row reported in `results.csv`, failures first.
