# pdl1030c / ind3: pre-declaration (written 2026-10-30 14:35 UTC, before any configuration is scored)

*Educational only — not financial advice.* Research only. Nothing is committed, and nothing is written to config/, mcf/, the ledger or the backlog.

Owner 2026-10-30: add ONE indicator, from the ones our live setups use most, to each of the two setups just demoted to the
Graveyard: CWT14-failbrk-pdl-p05-long ("p05") and CWT14-failbrk-pdl-p05-lowvol-long ("p05lv"). This agent tests
**RSI(5)** (`rsi5`) and **index context** (SPY/QQQ). Lineage CWT14 PDL, N_prior 121,635.

## Overlap with earlier swarms (skipped, not re-scored)
- SPY fromOpen > 0 / < 0 at the signal bar (tape-flip TA). Skipped ("SPY > open" short filter direction is the same column).
- SPY above/below VWAP (tape-flip TB, combo K1/K3/K6, regime-day C1). Skipped.
- SPY gap (combo, regime-day), SPY/QQQ hedges (pdl1030b), rs = stock fromOpen - SPY fromOpen (symbol-quality Q02/Q06/Q11/Q14,
  which also covers RWN5 "stock fromOpen < SPY fromOpen" from the other side). Skipped.
- RSI(5): never a scored filter in any PDL swarm (why/feat.py carried it descriptively only); ind2 tests RSI(14), not RSI(5).
- New here: RSI(5) rows, QQQ at/below its VWAP (ST7Q long), and the index dip-then-turn gate (LD/IDX family).

## Indicator definitions (all known at the signal (reclaim) bar's close; 5-minute frame bars incl. head rows 09:35-09:45)
- `rsi5` = frame RSI(5) at the signal bar. `rsi5_prev` = same symbol-day, prior bar. `rsi5_min3` = min of rsi5 over the
  3 bars before the signal bar (same symbol-day), i.e. the bars where the poke below PDL happened (b3_any: reclaim within 3 bars).
- `qqq_vd` = QQQ vwapDistPct at the same date/tod.
- Index running low: for SPY / QQQ, the minimum over that day's bars up to and including the signal bar of
  (bar low / day open - 1) x 100, day open = close / (1 + fromOpen/100). `idx_fo` = that ETF's fromOpen at the signal bar.

## Configurations (14 counted; every one is scored and reported)
Parent exits = each setup's own (p05: target 0.5R + scale 0.25R; p05lv: target 0.5R, no scale).
| id (p05 / p05lv) | added indicator | live source |
|---|---|---|
| R1-p05 / R1-lv | rsi5_min3 <= 20 (oversold at the poke) | ST4, LD4 (rsi5 <= 20) |
| R2-p05 / R2-lv | rsi5_prev <= 20 and rsi5 > 20 (crosses back above 20 on the reclaim bar) | ST3 |
| R3-p05 / R3-lv | rsi5 > 70 on the reclaim bar (short-term pop; opposite of oversold) | L3-rsi5hi, MF3, MF5, NM-MF3 |
| X1-p05 / X1-lv | QQQ at or below its VWAP (qqq_vd <= 0) | ST7Q long |
| X2-p05 / X2-lv | SPY dip-then-turn: SPY running low <= -0.15% and SPY fromOpen >= running low + 0.10 pts | LD2/3/6/7/8, IDX dip-bounce |
| X3-p05 / X3-lv | QQQ dip-then-turn: QQQ running low <= -0.30% and QQQ fromOpen >= running low + 0.10 pts | LD/IDX second threshold (-0.30) |
| S-p05 | p05 S3 + cost5 + the best of R1..X3 for p05 (rule below) | |
| S-lv | p05lv S3 + cost5 + the best of R1..X3 for p05lv (rule below) | |

Rule for the S rows, fixed now: among that setup's six parent-exit rows, the highest TRAIN avg R among rows with >= 25
trades/session; if none has 25/session, the highest TRAIN avg R overall. VALID is not used to pick.
S3 = stop x3 (0.75 ATR) at the same $ risk, target/scale prices kept, r in 3R units (swarm15). cost5 = skip when the
round-trip cost estimate > 5% of 0.25 ATR (symbol-quality). Base references are NOT re-scored (cap): p05 S3+cost5 =
symbol-quality Q08 (-0.0028 / -0.0084, 54.3/sess); p05lv S3+cost5 = ind1 B-lv (-0.0072 / -0.0188, 35.5/sess).

## Harness
pdl1030c/ind1/build.py (= symbol-quality/build.py + p05lv) plus the columns above: kernel CWT14 `S6.b3_any` (PD, long),
adv20 >= 95M, signals 09:50-15:00, first signal per symbol-day, simulator top5_1028 `sim`, costs 1c + 1 bp per side x
time-of-day multiplier, +2c stop exits, x3 extended tier. TRAIN = 2024-10, 2025-03..12; VALID = 2026-01..03, 2026-07..09-15.
HOLD months and the locked block are never loaded (asserts). Parity first: p05 -0.0677 / -0.0675, p05lv TV -0.0950.

## Bar (rule 22, BAR90)
N = 121,635 + 5 x 14 = 121,705 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Also WF >= 54% months positive, avg R > 0 on TRAIN
and VALID, beats its parent on both, >= 25 trades/session. Every row reports trades/session, % of parent kept, avg R w/o
best day and its share, avg R w/o top-5 days and their share, up/down-day R.

## Data note (added 14:40 UTC after a one-month build check, still before any configuration is scored)
The head rows (09:35-09:45) carry no rsi5, so rsi5_prev is missing for 09:50 signals and rsi5_min3 for 09:50-10:00 signals.
R1/R2 treat a missing value as "condition not met" (the trade is not taken); this is disclosed, not changed.
