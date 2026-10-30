# pdl1030c / ind4: pre-declaration (written 2026-10-30 14:40 UTC, before any configuration is scored)

*Educational only — not financial advice.* Research only. Nothing is committed, and nothing is written to config/, mcf/, the ledger or the backlog.

Owner 2026-10-30: add ONE indicator, from the ones our live setups use most, to each of the two setups just demoted to the Graveyard:
CWT14-failbrk-pdl-p05-long ("p05", 153/session, 2-yr -0.068R) and CWT14-failbrk-pdl-p05-lowvol-long ("p05lv", 101/session, -0.095R).
Indicators in this study: **Gap (open vs prior close)** and **5-min SMA50 (position / cross)**. Lineage CWT14 PDL, N_prior 121,635.

## Overlap with earlier swarms (skipped, not re-scored)
- gap <= -1.5% on p05 parent exits (symbol-quality Q04) and on p05 S3 + cost5 (Q13). Skipped.
- gap <= -3% (symbol-quality exploration note, 5.6/session). Not repeated.
- B10 (pdl1030b): continuation SHORT on any open incl. gap-under-PDL. Different trade (short); not repeated.
- SMA50: no earlier PDL row used it (grep of pdl1030*/ and pdl1030b/). Nothing skipped.
- None of the rows below repeats an earlier row: the gap thresholds (-2.657%, > 0, -0.41 ATR) and every SMA50 rule are new on these setups.

## Indicator definitions (all known at the signal (reclaim) bar's close)
- `gap` = frame column gap (%), open vs prior close; day-constant, known from 09:30.
- `gap_atr` = (open - prior close) / atr_d, with open = close / (1 + fromOpen/100) and prior close = open / (1 + gap/100)
  (same definition as mcf/research/arena/indicators.py gap_atr).
- `sd` = frame column sma50_dist_pct (close vs 5-min SMA50, %) at the signal bar.
- SMA50 cross up on the signal bar: sd > 0 and the prior 5-min bar's close <= the SMA50 value at the signal bar
  (SMA = close / (1 + sd/100)). The prior bar is the previous row of the same symbol-day (a 09:45 head row for a 09:50 signal).
  Using the signal bar's SMA for the prior bar is a disclosed approximation (the SMA moves 1/50 of a bar's change);
  it uses only data known at the signal-bar close.

## Configurations (14 counted; every one is scored and reported)
Exits are each parent's own: p05 target 0.5R + 0.25R scale-out; p05lv target 0.5R, no scale-out.
| id (p05 / p05lv) | added condition | source (how live setups use it) |
|---|---|---|
| G1-p05 / G1-lv | gap <= -2.657% | live direction, gap down: L3 cut (x3) |
| G2-p05 / G2-lv | gap > 0 (opened above prior close, then swept the PDL) | opposite direction (ST3/ST6 gap up, NM-MF3 no gap up) |
| G3-p05 / G3-lv | gap_atr <= -0.41 | second live threshold, ATR-scaled gap down (AR-AM) |
| M1-p05 / M1-lv | sd > 0 (reclaim bar closes above the SMA50) | live: close above SMA50 (NS3, RW4, RWN3/5, RWR3, ST5) |
| M2-p05 / M2-lv | SMA50 cross up on the signal bar | live: SMA50 cross (RW6G1, RWN4, RWR4) |
| M3-p05 / M3-lv | sd < 0 (still below the SMA50, oversold) | opposite direction (NS5 below-SMA50 flush long) |
| S-p05 | p05 S3 + cost5 + the best G/M row for p05 (rule below) | |
| S-lv | p05lv S3 + cost5 + the best G/M row for p05lv (rule below) | |

S rows: among that setup's six G/M rows, take the one with the highest TRAIN avg R among rows with >= 25 trades/session;
if none has that many, the highest TRAIN avg R overall. VALID is not used to pick.
S3 = stop x3 (0.75 ATR) at the same $ risk, target/scale prices kept, r in 3R units (swarm15). cost5 = skip when the round-trip
cost estimate > 5% of 0.25 ATR (symbol-quality). Base references are not re-scored here: p05 S3 + cost5 = symbol-quality Q08
(-0.0028 / -0.0084, 54.3/session); p05lv S3 + cost5 = ind1 B-lv (-0.0072 / -0.0188, 35.5/session).

## Harness
ind1/build.py (= pdl1030/symbol-quality/build.py + p05lv) plus the gap / gap_atr / sma50 fields: kernel CWT14 S6.b3_any (PD, side +1),
adv20 >= 95M, signals 09:50-15:00, first per symbol-day, simulator top5_1028 sim, costs 1c + 1bp per side x ToD mult (+2c stops, x3 extended tier).
TRAIN = 2024-10, 2025-03..12. VALID = 2026-01..03, 2026-07..09-15. HOLD months (2026-04..06, 2026-09-16..10-07) and locked block
(2024-11..2025-02) never loaded (asserts). Parity first: p05 -0.0677 / -0.0675; p05lv TV -0.0950.

## Bar (rule 22, BAR90)
N = 121,635 + 5 x 14 = 121,705 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Also: walk-forward >= 54% months positive; avg R > 0 on TRAIN
and VALID; beats its parent on both splits; >= 25 trades/session.
Reported for every row: trades/session, % of parent trades kept, avg R w/o best day + its share, avg R w/o top-5 days + their share
(owner: is the record more than its best day(s)?), up-day / down-day R.
