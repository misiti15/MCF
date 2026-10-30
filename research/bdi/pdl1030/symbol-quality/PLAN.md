# pdl1030 / symbol-quality — pre-declaration (written before any configuration is scored)

*Educational only — not financial advice.*

Written 2026-10-30 ~05:20 UTC (before the US open; research only — no repo, config/, mcf/, ledger or backlog writes).
Lineage: Failed Prior-Day-Low Break Longs (CWT14-failbrk-pdl-p05 / p05-lowvol / p10 / p10-lowvol). N_prior 121512.

## Family: symbol quality known at entry. The 2-3 strongest from pdl1030/why NOTES only
1. **Relative strength** (U-shape, best at the strong end): stock > 0.5% above its own VWAP -0.026 (18/sess);
   stock fromOpen beats SPY fromOpen by > 0.5% -0.046. Known at the signal-bar close (vwapDistPct, fromOpen, SPY fromOpen at that bar).
2. **Relative volume on the reclaim bar**: the low-volume variants (vr <= 1) are worse than the parents
   (p05lv -0.095 vs p05 -0.068), so the high-volume reclaim is the side to test. `volumeRatio` = signal-bar volume /
   20-bar average volume, known at the signal-bar close.
3. **Gap down into PDL**: stock gap <= -3% was -0.010 but only 5.6/sess; use a looser -1.5% cut to keep exposure.
   Known at the open.
Not tested (no evidence in the why notes): prior-day trend vs 20-day average, round-number distance.

Because the why notes show that gross edge is ~0 and costs/beta drive the loss, the quality filters are also layered on
the two strongest known levers: swarm15 S3 (stop x3 ATR multiple at the same $ risk, target price kept, r in the new R)
and a cost floor (round-trip cost estimate <= 5% of the parent R = 0.25 ATR; same estimate as why/feat.py `cost_rt_R`,
known at entry from price, tier, time and ATR). These layers count as configurations here.

## Harness
why/feat.py logic (CWT14 `S6.b3_any` kernel, first signal per symbol-day, 09:50-15:00, adv20 >= 95M, top5_1028 `sim`,
costs in: 1c + 1 bp per side x time-of-day multiplier, +2c stop exits, x3 extended tier). TRAIN <= 2025-12 (2024-10,
2025-03..12); VALID 2026-01..03 + 2026-07..09-15. HOLD months and the locked block 2024-11..2025-02 are never loaded.
Parity first: p05 TRAIN/VALID -0.0677/-0.0675, p10 TV -0.0880, p05 S3 -0.0210/-0.0173 (swarm15) within 0.005R.

## Configurations (17; all scored, all reported)
| id | base | filter |
|---|---|---|
| Q01 | p05 parent exits | vd >= +0.5% |
| Q02 | p05 parent exits | rs = fromOpen - SPY fromOpen >= +0.5% |
| Q03 | p05 parent exits | volumeRatio >= 1.5 |
| Q04 | p05 parent exits | gap <= -1.5% |
| Q05 | p05 S3 | vd >= +0.5% |
| Q06 | p05 S3 | rs >= +0.5% |
| Q07 | p05 S3 | volumeRatio >= 1.5 |
| Q08 | p05 S3 + cost5 | (none: layer reference) |
| Q09 | p05 S3 + cost5 | vd >= +0.5% |
| Q10 | p05 S3 + cost5 | vd >= 0 |
| Q11 | p05 S3 + cost5 | rs >= +0.5% |
| Q12 | p05 S3 + cost5 | volumeRatio >= 1.5 |
| Q13 | p05 S3 + cost5 | gap <= -1.5% |
| Q14 | p05 S3 + cost5 | vd >= +0.5% or rs >= +0.5% |
| Q15 | p05 S3 + cost5 | vd >= +0.5% and volumeRatio >= 1.5 |
| Q16 | p10 S3 + cost5 | vd >= +0.5% |
| Q17 | p10 S3 + cost5 | volumeRatio >= 1.5 |

## Bar (rule 22, BAR90)
N = 121512 + 3 x 17 = 121563 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Also walk-forward >= 54% of months positive,
avg R > 0 on TRAIN and on VALID separately, beats p05 (-0.0677 / -0.0675) on both, exposure >= 76.6/sess or >= 25/sess.
Reported for every row: train/valid avg R, day-clustered t, trades/session, wf%, up/down-day R, avg R w/o best day.
