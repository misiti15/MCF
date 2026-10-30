# pdl1030c / ind1: pre-declaration (written 2026-10-30 14:22 UTC, before any configuration is scored)

*Educational only — not financial advice.* Research only. Nothing is committed, and nothing is written to config/, mcf/, the ledger or the backlog.

Owner 2026-10-30: the two setups just demoted to the Graveyard are CWT14-failbrk-pdl-p05-long ("p05") and
CWT14-failbrk-pdl-p05-lowvol-long ("p05lv"). This study adds ONE indicator, taken from the ones our live setups use most, to each of them.
Two indicators are tested here: **Move from open** (`fromOpen`) and **VWAP position / cross** (`vwapDistPct`).
Lineage is CWT14 PDL with N_prior 121,635.

## Overlap with earlier swarms (skipped, not re-scored)
- rs = fromOpen - SPY fromOpen >= +0.5% (symbol-quality Q02/Q06/Q11/Q14). Skipped.
- vd >= +0.5% and vd >= 0, i.e. the stock above its VWAP (Q01/Q05/Q09/Q10/Q14/Q15/Q16). Skipped.
- SPY vs VWAP (why, tape-flip, combo K1/K3/K6). Skipped.
- No row below repeats any of these. Raw fromOpen, a VWAP reclaim on the signal bar, and "below VWAP with room" were never tried.

## Indicator definitions (all known at the signal-bar close)
- `fo` = the stock's fromOpen (%) on the signal bar.
- `vd` = the stock's vwapDistPct on the signal bar. `vd_prev` = the same value on the prior bar of the same symbol-day.
  VWAP price = close / (1 + vd/100).
- `vwap_room_atr` = (VWAP - close) / atr_d.

## Configurations (13 counted; every one is scored and reported)
Exits are the parent's own: p05 has target 0.5R and a 0.25R scale-out. p05lv has target 0.5R and no scale-out.
| id | base | added indicator | where it comes from in live setups |
|---|---|---|---|
| F1-p05 / F1-lv | parent | fo > 0 (green on the day) | the 0 line (NM1, HL-T75 use < 0) |
| F2-p05 / F2-lv | parent | fo > +2 | the long/up threshold (NS1, NS4, LD1, LD7, RWN4) |
| F3-p05 / F3-lv | parent | fo < -2 (washed out, then reclaimed) | the down threshold (NS3, RW4, RWN3/5, RWR3) |
| V1-p05 / V1-lv | parent | VWAP reclaim on the signal bar: vd > 0 and vd_prev <= 0 | NS3/NS4/RW4/RWN3/RWN5/RWR3 cross |
| V2-p05 / V2-lv | parent | below VWAP with room: vwap_room_atr >= 0.5 (2 x 0.25 ATR R) | LIQ PDL-sweep long room-to-VWAP |
| S-p05 | p05 S3 + cost5 | the best F/V row for p05 (rule below) | |
| S-lv | p05lv S3 + cost5 | the best F/V row for p05lv (rule below) | |
| B-lv | p05lv S3 + cost5 | none: the base reference for S-lv (p05's base is symbol-quality Q08, not re-counted) | |

Rule for picking the S rows, fixed now: among that setup's five F/V rows, take the one with the highest TRAIN avg R
among rows that have >= 25 trades/session. If no row has that many, take the highest TRAIN avg R overall. VALID is not used to pick.
S3 = stop x3 (0.75 ATR) at the same $ risk, with the target and scale prices kept and r in 3R units (swarm15).
cost5 = skip a trade when the round-trip cost estimate is > 5% of 0.25 ATR (symbol-quality).
The third-threshold VWAP variant (within 0.5 ATR of VWAP) was dropped to stay inside the 14-config cap with the B-lv reference.

## Harness
The harness is symbol-quality/build.py unchanged, plus p05lv (vr <= 1.0, so = 0.0, from why/feat.py):
- kernel CWT14 `S6.b3_any` (PD level, side +1)
- adv20 >= 95M, signals 09:50-15:00, first signal per symbol-day
- simulator top5_1028 `sim`
- costs 1c + 1 bp per side x the time-of-day multiplier, +2c on stop exits, x3 on the extended tier

Splits: TRAIN = 2024-10 and 2025-03..12. VALID = 2026-01..03 and 2026-07..09-15. The HOLD months (2026-04..06, 2026-09-16..10-07)
and the locked block (2024-11..2025-02) are never loaded.
Parity comes first: p05 must give TRAIN -0.0677 and VALID -0.0675; p05lv must give TV -0.0950; p05 S3 must give -0.0210 / -0.0173.

## Bar (rule 22, BAR90)
N = 121,635 + 5 x 13 = 121,700, so the bar is t_TV >= 0.9 x sqrt(2 ln N) = 4.355.
A row also needs:
- walk-forward >= 54% of months positive
- avg R > 0 on TRAIN and on VALID
- a beat over its parent on both splits (p05 -0.0677 / -0.0675; p05lv uses its own parity values)
- >= 25 trades/session

Reported for every row: trades/session, % of the parent's trades kept, avg R without the best day and that day's share,
and up-day and down-day R.
