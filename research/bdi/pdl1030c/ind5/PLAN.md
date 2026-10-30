# pdl1030c / ind5: pre-declaration (written 2026-10-30, before any configuration is scored)

*Educational only — not financial advice.* Research only. Nothing is committed, and nothing is written to config/, mcf/, the ledger or the backlog.

Owner 2026-10-30: add ONE indicator, from the ones our live setups use most, to each of the two setups just demoted to the Graveyard:
CWT14-failbrk-pdl-p05-long ("p05", 153/session, 2-yr -0.068R) and CWT14-failbrk-pdl-p05-lowvol-long ("p05lv", 101/session, -0.095R).
Indicators in this study: **MarcoFlow heat (composite score)** and **Relative volume (volume ratio / climax)**. Lineage CWT14 PDL, N_prior 121,635.

## Overlap with earlier swarms (skipped, not re-scored)
- volumeRatio >= 1.5 on the signal bar (symbol-quality Q03/Q07/Q12/Q15/Q17). Skipped.
- volumeRatio < 1 on the poke bar IS the p05lv parent. Not re-scored as a filter.
- heat: no earlier PDL row used heat or any heat sub-score (grep of pdl1030*/, pdl1030b/, pdl1030c/). Nothing skipped.
- None of the rows below repeats an earlier row: the vr >= 2 *cross*, the 3-bar volume climax and rvol_day are new on these setups.

## Indicator definitions (all known at the signal (reclaim) bar's close)
- `heat` = frame column heat (MarcoFlow composite, about -75..+75) at the signal bar.
- `vr` = frame column volumeRatio at the signal bar; `vr_prev` = the prior bar of the same symbol-day (NaN on a head row -> "no cross").
- `vc3` = max(vol_climax) over the signal bar and the 2 bars before it in the same symbol-day (CWT05 live definition; NaN -> 0,
  as cwt_live_lib does). In these frames vol_climax equals volumeRatio (checked: identical distributions).
- `rvol_day` = mean volumeRatio over the symbol-day's frame rows from 09:50 through the signal bar (arena indicators.py definition).

## Configurations (14 counted; every one is scored and reported)
Exits are each parent's own: p05 target 0.5R + 0.25R scale-out; p05lv target 0.5R, no scale-out.
| id (p05 / p05lv) | added condition | source (how live setups use it) |
|---|---|---|
| H1-p05 / H1-lv | heat >= +20 | bullish mirror of the live short threshold heat <= -20 (RW3, RW1, RW7) |
| H2-p05 / H2-lv | heat > -20 ("not bearish" gate) | mirror gate of the same live threshold |
| H3-p05 / H3-lv | heat <= -30 (deeply bearish, washed out then reclaimed) | opposite direction: live short threshold (MF2-5, RW5, NM-MF3) |
| R1-p05 / R1-lv | vr crosses above 2.0 on the signal bar (vr >= 2 and vr_prev < 2) | ST6, ST8 |
| R2-p05 / R2-lv | vc3 >= 3 (volume climax on one of the last 3 bars) | CWT05 x4 |
| R3-p05 / R3-lv | rvol_day >= 0.84 (stock is active on the day) | PM-gapdn |
| S-p05 | p05 S3 + cost5 + the best H/R row for p05 (rule below) | |
| S-lv | p05lv S3 + cost5 + the best H/R row for p05lv (rule below) | |

S rows: among that setup's six H/R rows, take the one with the highest TRAIN avg R among rows with >= 25 trades/session;
if none has that many, the highest TRAIN avg R overall. VALID is not used to pick.
S3 = stop x3 (0.75 ATR) at the same $ risk, target/scale prices kept, r in 3R units (swarm15). cost5 = skip when the round-trip
cost estimate > 5% of 0.25 ATR (symbol-quality). Base references are printed for comparison but not counted (already scored):
p05 S3 + cost5 = symbol-quality Q08 (-0.0028 / -0.0084, 54.3/session); p05lv S3 + cost5 = ind1 B-lv (-0.0072 / -0.0188, 35.5/session).
Dropped to stay inside the cap: rvol_day <= 0.8 (AR-AM) and vc3 >= 5.

## Harness
ind1/build.py (= pdl1030/symbol-quality/build.py + p05lv) plus the heat / vr_prev / vc3 / rvol_day fields: kernel CWT14 S6.b3_any (PD, side +1),
adv20 >= 95M, signals 09:50-15:00, first per symbol-day, simulator top5_1028 sim, costs 1c + 1bp per side x ToD mult (+2c stops, x3 extended tier).
TRAIN = 2024-10, 2025-03..12. VALID = 2026-01..03, 2026-07..09-15. HOLD months (2026-04..06, 2026-09-16..10-07) and locked block
(2024-11..2025-02) never loaded (asserts). Parity first: p05 -0.0677 / -0.0675; p05lv TV -0.0950.

## Bar (rule 22, BAR90)
N = 121,635 + 5 x 14 = 121,705 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Also: walk-forward >= 54% months positive; avg R > 0 on TRAIN
and VALID; beats its parent on both splits; >= 25 trades/session.
Reported for every row: trades/session, % of parent trades kept, avg R w/o best day + its share, avg R w/o top-5 days + their share
(owner: is the record more than its best day(s)?), up-day / down-day R.
