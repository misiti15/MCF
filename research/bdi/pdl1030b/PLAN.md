# pdl1030b (PDL-1b): beta hedge + early-break signal, pre-declaration

*Educational only — not financial advice.*

Written 2026-10-30, before any configuration is scored. Owner-approved task PDL-1b. Research only: no config/, mcf/,
ledger or backlog writes; nothing committed by this agent.

## Data and harness (same as pdl1030)
- Open two-year 5-minute frames via `scan_1019.build_paths` (head rows 09:35-09:45 + frames 09:50-15:00 + tail rows to 15:55).
- TRAIN = 2024-10, 2025-03..2025-12. VALID = 2026-01..03 + 2026-07..2026-09-15 (rows after 09-15 dropped at load).
- Never loaded: the locked block 2024-11-01..2025-02-28, HOLD months 2026-04..06 and 2026-09-16..10-07 (asserts).
- Kernel: CWT14 `S6.b3_any` (PD level, long, p, reclaim within 3 bars, no vr cap). Liquid base adv20 >= 95M, atr_d > 0,
  R1 = 0.25 x daily ATR. First signal per symbol-day. Entry at the signal-bar close (em=0, as the parent).
- Simulator: top5_1028 `sim` logic (stop-first, costs 1c + 1 bp per side x time-of-day multiplier 3.8/2.1/1.4/1.0,
  +2c on stop exits, x3 on the extended tier). Copied into `build.py` only to also return the scale-out row.
- Parent p05 exits: target 0.5 R1, scale half at 0.25 R1 (stop to break-even), stop 1 R1, flat 15:55.
- **S3** = stop at 3 R1 with the same $ risk (position 1/3), target/scale prices unchanged, r in 3R1 units.
- **cost5** = skip when the round-trip cost estimate > 5% of R1 (as symbol-quality Q08 / combo).

## Hedge leg (angle A, and B3/B8)
- At the stock's entry bar close, open an opposite SPY (or QQQ) position of notional = beta x stock notional
  (stock notional = shares x entry price; shares = $risk / stop distance).
- Exit the hedge with the stock: half at the scale-out bar when the stock scales, the rest at the stock's final exit bar.
- Hedge exit price, conservative: for intrabar exits (stop / target / moved stop / scale) the worse for the hedge of the
  ETF close of the bar before and of the exit bar; for clock / 15:55 exits the exit-bar close.
- Hedge costs: 1c/share + 1 bp per side, times the same time-of-day multiplier as the stock.
- Pair R = (stock P/L + hedge P/L - all costs) / stock $ risk.
- **beta1** = 1.0. **beta20** = OLS beta of the stock's daily close-to-close returns on SPY's (or QQQ's) over the prior
  20 sessions (only sessions before the trade date; returns across a gap > 5 calendar days are not used, so the
  locked block and HOLD months never enter); needs >= 15 returns, else beta 1.0; clipped to [0, 3].
  The first ~3 weeks of 2024-10, 2025-03 and 2026-07 therefore use beta 1.0 (disclosed).

## Configurations (23, all counted, including the two reference re-scores)
| id | rule |
|----|------|
| A0 | p05 parent, no hedge (parity reference: TRAIN -0.0677 / VALID -0.0675) |
| A1 | p05 parent + SPY hedge beta1 |
| A2 | p05 parent + SPY hedge beta20 |
| A3 | p05 S3 + cost5, no hedge (reference) |
| A4 | p05 S3 + cost5 + SPY hedge beta1 |
| A5 | p05 S3 + cost5 + SPY hedge beta20 |
| A6 | p05 S3 (no cost floor) + SPY hedge beta20 |
| A7 | p05 parent exits + cost5 + SPY hedge beta20 |
| A8 | p05 S3 + cost5 + QQQ hedge beta1 |
| A9 | p05 S3 + cost5 + QQQ hedge beta20 (beta vs QQQ) |
| A10 | p10 S3 + cost5 + SPY hedge beta20 |
| B1 | early reclaim long: b3_any p=0.05, signal bar 09:35-09:45, parent p05 exits |
| B2 | B1 with S3 + cost5 |
| B3 | B2 + SPY hedge beta20 |
| B4 | B1 with target 1.0 R1, no scale-out |
| B5 | early continuation short: first bar 09:35-09:45 that closes <= PDL - 0.05 ATR, stock opened above PDL; mirrored p05 exits |
| B6 | B5 with 0.10 ATR |
| B7 | B5 with S3 + cost5 |
| B8 | B7 + SPY hedge beta20 (long SPY) |
| B9 | B5 with target 1.0 R1, no scale-out |
| B10 | B5 without the opened-above-PDL condition (gap-under names included) |
| B11 | early reclaim long p=0.10, parent p10 exits (target 0.5, no scale) |
| B12 | B5 only when SPY is below its VWAP at the signal-bar close |

Nothing is added after scoring; any addition would be disclosed and counted.

## Lineage N and bar
Both angles are scored inside the CWT14 PDL lineage: A is the same signal with a hedge; B's reclaim long is the same
kernel in an earlier window and the continuation short is a mirror already explored by failed-reclaim-short.
No new lineage is claimed (conservative). N = 121,611 + 23 = 121,634.
BAR90 t >= 0.9 x max(1.5, sqrt(2 ln N)) = 4.356 (min 1.35).

## Pass rule (all required)
Day-clustered t on TRAIN+VALID >= bar; walk-forward >= 54% of months positive; avg R > 0 on TRAIN and on VALID;
avg R > 0 in SPY-up and SPY-down sessions (SPY session sign, descriptive split); >= 25 trades/session.
Reported per row: TRAIN / VALID avg R, t, trades/session, wf%, up/down-day R, avg R without the best day and its share.
A row that passes is checked against random same-window entries (rule 6) before anything is written.
