# pdl1030 / time-bucket: pre-declaration (written before any configuration is scored)

*Educational only — not financial advice.*

Written 2026-10-30 ~05:30 UTC (01:30 ET, outside market hours; research only, with no writes to the repo, config/, mcf/, ledger or backlog).
Lineage: Failed Prior-Day-Low Break Longs (CWT14-failbrk-pdl-p05 / p05-lowvol / p10 / p10-lowvol). N_prior 121566.

## Family: time-of-day specialisation plus the best earlier piece
- Move Hunt: most big moves start before 09:50, but the live window starts at 09:50. So test an **earlier start (09:35)**.
  The 09:35-09:45 head rows (headtail.parquet, as cwt/live/verify.py adds them) already feed the kernel's look-back.
  What is new here is that those rows may now be signal bars.
- Live: 09:50-10:00 entries lose most (-0.22R), and 13:00-15:00 entries are slightly positive. So test skipping 09:50 and an afternoon-only window.
- Backtest time-of-day was flat (why notes). So the windows alone are not expected to fix the loss; they are layered
  on the **best earlier piece**, symbol-quality Q08 = swarm15 S3 (stop x3 at the same $ risk, target price kept)
  plus the cost floor (round-trip cost estimate <= 5% of the parent R = 0.25 ATR). Q08 was -0.003 / -0.008 at 54/sess.
- Window semantics: the setup is active only inside the window. The trade is the **first signal per symbol-day inside the window**,
  as a live module with that window would trade it.
- Cost estimate (known at entry: price, tier, bar time, ATR): (0.01 + c*1e-4) * mult(tod) + 0.01 + c*1e-4, times the tier, divided by R.
  mult is the simulator's own time-of-day multiplier (3.8 / 2.1 / 1.4 / 1.0), so 09:35-09:45 entries pay 2.1x on entry.
  For tod >= 09:50 this is identical to symbol-quality's cost_rt_R.
- All windows are bar times, known at entry. Signal = close of the reclaim bar (CWT14 b3_any). Entry is at that close.

## Harness
symbol-quality/build.py logic: CWT14 `S6.b3_any` kernel, adv20 >= 95M, top5_1028 `sim` with costs in
(1c + 1 bp per side x tod multiplier, +2c stop exits, x3 extended tier). Exits: P = parent (p05: up 0.5, dn 1, so 0.25;
p10: so 0), and S3 = dn 3 at the same $ risk (r / 3). Every flagged bar 09:35-15:00 is simulated, and the window and the
first-per-symbol-day pick are applied at scoring.
TRAIN <= 2025-12 (2024-10, 2025-03..12); VALID 2026-01..03 + 2026-07..09-15. HOLD months and the locked block are never loaded.
Parity first (not counted): p05 09:50-15:00 P must give -0.0677 / -0.0675, p10 TV -0.0880, and p05 S3+cost5 (Q08) -0.0028 / -0.0084.
All within 0.005R.

## Configurations (18; all scored, all reported)
| id | base | exit | cost floor | window (signal bar tod) |
|---|---|---|---|---|
| T01 | p05 | P | - | 09:35-15:00 |
| T02 | p05 | P | - | 09:35-09:45 |
| T03 | p05 | P | - | 10:00-15:00 |
| T04 | p05 | P | - | 11:30-15:00 |
| T05 | p05 | P | - | 13:00-15:00 |
| T06 | p05 | S3 | - | 09:35-15:00 |
| T07 | p05 | S3 | c5 | 09:35-15:00 |
| T08 | p05 | S3 | c5 | 09:35-09:45 |
| T09 | p05 | S3 | c5 | 09:35-10:30 |
| T10 | p05 | S3 | c5 | 10:00-15:00 |
| T11 | p05 | S3 | c5 | 10:30-15:00 |
| T12 | p05 | S3 | c5 | 11:30-13:30 (lunch) |
| T13 | p05 | S3 | c5 | 13:00-15:00 (afternoon) |
| T14 | p05 | S3 | c5 | 09:35-09:45 + 10:00-15:00 (skip the 09:50 bar) |
| T15 | p05 | S3 | c8 | 09:35-15:00 |
| T16 | p05 | S3 | c8 | 10:00-15:00 |
| T17 | p10 | S3 | c5 | 09:35-15:00 |
| T18 | p10 | S3 | c5 | 10:00-15:00 |

## Bar (rule 22, BAR90)
N = 121566 + 3 x 18 = 121620 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Also walk-forward >= 54% of months positive,
avg R > 0 on TRAIN and on VALID separately, beats p05 (-0.0677 / -0.0675) on both, and exposure >= 76.6/sess or >= 25/sess.
Reported for every row: train/valid avg R, day-clustered t, trades/session, wf%, up/down-day R, and avg R without the best day plus its share.
