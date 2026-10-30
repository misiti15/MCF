# rdt1030 / F6 index-native: results

*Educational only — not financial advice.*

**Verdict: no row passes. 18 configs were scored, all pre-declared in PLAN.md. No rework rows were added.**

Every row fails three gates by construction or by size:
- **Trade rate:** at most 0.6 trades per session, against a bar of 3.
- **t-stat:** the best day-clustered t is 1.17, against a bar of 3.52.
- **Market direction:** every row has the wrong sign on one side of the SPY up/down-day split.

The `passes_all_but_rate` column is False for every row, so no row would pass even with an owner exception on trade
rate.

## What the index version shows
This family runs the post's futures-native ideas on the index ETFs: QQQ and SPY signals, traded in TQQQ/SQQQ or SPXL/SPXS
with the levels scaled ×3 by percentage, plus the requested QQQ/SPY/TQQQ/SQQQ-only row.

- **Same failure as on stocks.** Results split entirely by market direction:
  - Longs make +0.18 to +0.43R on SPY up days and lose 0.35 to 1.15R on down days.
  - Shorts are the mirror image.
  - The FVG-at-the-break entry adds no edge that survives the day's direction.
- **The best rows are shorts, but the samples are tiny.**
  - **F6-08** (Nasdaq 5-min ORB with Gap, break-even, 2 tries, short via SQQQ): +0.162R over 41 trades, t 1.11, TRAIN
    +0.048, VALID +0.294.
  - **F6-02** (the as-posted 15-min ORB with Gap, short via SQQQ): +0.077R over 53 trades, t 0.57.
  - **F6-18**, the same signal as F6-02 traded in QQQ itself: +0.080R.

  All three lose 0.44-0.54R on SPY up days. This is short beta in a sample of about 50 trades, not an edge.
- **Leverage mapping sanity check:** F6-01 and F6-17 take the same QQQ signal, traded in TQQQ and in QQQ. They score
  -0.0035R and -0.0008R. F6-02 and F6-18 score +0.077R and +0.080R. The ×3 mapping only changes costs: median cost/R is
  about 0.03-0.05 in the 3x ETFs and about 0.05-0.06 in QQQ.
- **Liquidity sweep then 15-min gap (F6-09 to F6-14):** 5 to 21 trades in about 17 months. Too few to say anything.
  F6-14 (S&P PDH sweep, short via SPXS, +0.57R) is 6 trades, and one day carries 67% of its R.
- **1-min gap version (F6-05/06):** 19 and 29 trades, -0.29R and -0.11R. A gap of 0.05 ATR on 1-min bars is rare at the
  break.
- **Index-only row (F6-15/16)** on QQQ, SPY, TQQQ and SQQQ, each traded as itself:
  - Long: -0.050R over 190 trades. Short: +0.010R over 203 trades.
  - The four symbols are almost the same trade (TQQQ long ≈ SQQQ short ≈ QQQ long), so the extra trades are not
    independent.
  - The walk-forward share (80% long, 67% short) comes from few folds and does not matter with t ≈ 0.

## Harness
- **Entry code:** imported, not rewritten (`build.py` loads them with importlib, with the numba on-disk cache off):
  - F1-A `signals` from `../F1/build.py`
  - F3-A `trade1` / `trade2` from `../F3/build.py`
  - `sim`, `seg_arrays` and `run_signal` from `../F4/build.py`
- **Simulator:** F4's patched stop-first sim, the top5_1028 sim with the DESIGN 0.2 patches:
  - per-trade R and target
  - 1c + 1 bp × ToD multiplier on entry, 1c + 1 bp on every exit including targets, +2c on stop exits
  - ×3 on the extended tier
  - gap-through stop fill
- **ETF mapping:**
  - R_ETF = 3 × e_ETF × R_sig / e_sig, with the same target multiple.
  - A QQQ short is a long SQQQ.
  - The sim runs on the ETF's own 5-min bars to 15:55.
  - The 1R/2R switch, the risk guard and break-even use the signal symbol's ATR.
- **1-min variant (F6-05/06):**
  - Uses `frames_tf/1min` (price columns only; no outcome column was loaded).
  - OR15 comes from the 5-min head rows. A side is skipped if the 0950 5-min close is already beyond the OR.
  - The ETF path is 1-min bars to 15:00, then the 5-min tail rows.
  - `signals_step` is F1's signal function with step and start as parameters. With (5, 0955) it reproduces F1 on every
    symbol-day of 2025-06 with 0 mismatches over 7,805 signals (`python build.py check`).
- **F3 on QQQ:** trade 1's ETF exit time is mapped back to the QQQ row for the "trade 2 after exit" rule. Only 2 second
  trades occurred.
- **Random control:** 5 random lab-universe symbols at the same row, with the same side, the same R in ATR units of the
  traded instrument, the same target and the same break-even. The 1-min rows use 1-min core symbols at the same minute.
- **Splits:**
  - TRAIN: 2024-10 and 2025-03..12
  - VALID: 2026-01..03 and 2026-07..09-15
  - 348 sessions in total
  - The locked block and the HOLD months were never loaded (`_cut` and asserts as in F1/F3/F4).
- **Sanity check before scoring** (2025-06, signal features only):
  - 0.05-0.25 trades per session per row
  - median R/ATR 0.15-0.44
  - median cost/R 0.04-0.07
  - signals at 09:55-10:15 for the ORB rows
  - This is consistent with F1, which had 0.16 signals per liquid symbol-day.
- **Walk-forward:** WF% is NaN for most rows because no test fold reaches `gates.FOLD_MIN_N` trades. `months_pos_pct` is
  reported instead, and it is 30-53% on every row.
- **Bar:** N = 2,000 + 108 + 24 rework rows from F1-F4 = 2,132, so t_req = 3.524.

## Results (full columns in results.csv)
| id | setup | n | tr/sess | TRAIN | VALID | all | t_day | mo+% | win% | W/L | up-day | down-day | w/o best day | best-day share | control |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F6-01 | Nasdaq 15-min ORB with Gap, Long via TQQQ | 44 | 0.13 | -0.102 | +0.139 | -0.004 | -0.03 | 47 | 54.5 | 0.83 | +0.377 | -1.017 | -0.026 | n/a | -0.035 |
| F6-02 | Nasdaq 15-min ORB with Gap, Short via SQQQ | 53 | 0.15 | +0.103 | +0.038 | +0.077 | 0.57 | 40 | 54.7 | 0.97 | -0.442 | +0.264 | +0.060 | 24% | -0.128 |
| F6-03 | S&P 15-min ORB with Gap, Long via SPXL | 50 | 0.14 | -0.210 | -0.091 | -0.167 | -1.28 | 41 | 44.0 | 0.87 | +0.189 | -0.660 | -0.191 | n/a | -0.100 |
| F6-04 | S&P 15-min ORB with Gap, Short via SPXS | 54 | 0.16 | -0.183 | +0.016 | -0.113 | -0.82 | 33 | 48.1 | 0.86 | -0.588 | +0.145 | -0.133 | n/a | -0.047 |
| F6-05 | Nasdaq 15-min ORB with 1-min Gap, Long via TQQQ | 19 | 0.05 | -0.426 | -0.198 | -0.294 | -1.25 | 30 | 42.1 | 0.78 | -0.065 | -1.151 | -0.362 | n/a | -0.066 |
| F6-06 | Nasdaq 15-min ORB with 1-min Gap, Short via SQQQ | 29 | 0.08 | -0.298 | +0.191 | -0.113 | -0.60 | 31 | 48.3 | 0.86 | -0.898 | +0.367 | -0.151 | n/a | -0.086 |
| F6-07 | Nasdaq 5-min ORB with Gap, BE, 2 tries, Long via TQQQ | 40 | 0.11 | -0.005 | +0.044 | +0.014 | 0.09 | 53 | 55.0 | 0.84 | +0.410 | -1.030 | -0.011 | **178% (1 day)** | -0.133 |
| F6-08 | Nasdaq 5-min ORB with Gap, BE, 2 tries, Short via SQQQ | 41 | 0.12 | +0.048 | +0.294 | +0.162 | 1.11 | 43 | 58.5 | 1.00 | -0.537 | +0.487 | +0.142 | 15% | -0.107 |
| F6-09 | Nasdaq PDL Sweep then 15-min Gap, Long via TQQQ | 5 | 0.01 | +0.177 | -0.124 | +0.117 | 0.39 | 50 | 60.0 | 1.00 | +0.411 | -1.061 | -0.040 | **128% (1 day)** | +0.260 |
| F6-10 | Nasdaq PDH Sweep then 15-min Gap, Short via SQQQ | 5 | 0.01 | -0.213 | -0.411 | -0.292 | -1.42 | 40 | 40.0 | 0.23 | -0.548 | -0.121 | -0.416 | n/a | +0.024 |
| F6-11 | Nasdaq OR-Low Sweep then 15-min Gap, Long via TQQQ | 16 | 0.05 | -0.068 | -0.078 | -0.073 | -0.37 | 45 | 43.8 | 1.04 | +0.336 | -0.974 | -0.178 | n/a | +0.116 |
| F6-12 | Nasdaq OR-High Sweep then 15-min Gap, Short via SQQQ | 21 | 0.06 | -0.294 | +0.311 | -0.150 | -0.89 | 36 | 33.3 | 1.24 | -0.749 | +0.299 | -0.239 | n/a | -0.025 |
| F6-13 | S&P PDL Sweep then 15-min Gap, Long via SPXL | 6 | 0.02 | +0.091 | -0.515 | -0.111 | -0.37 | 50 | 50.0 | 0.68 | +0.433 | -0.655 | -0.347 | n/a | -0.150 |
| F6-14 | S&P PDH Sweep then 15-min Gap, Short via SPXS | 6 | 0.02 | +1.099 | +0.048 | +0.573 | 1.17 | 50 | 50.0 | 3.11 | -0.612 | +1.166 | +0.225 | **67% (1 day)** | -0.284 |
| F6-15 | Index ETFs (QQQ/SPY/TQQQ/SQQQ) 15-min ORB with Gap, Long | 190 | 0.55 | -0.138 | +0.084 | -0.050 | -0.56 | 53 | 50.5 | 0.88 | +0.182 | -0.349 | -0.067 | n/a | -0.076 |
| F6-16 | Index ETFs (QQQ/SPY/TQQQ/SQQQ) 15-min ORB with Gap, Short | 203 | 0.58 | -0.046 | +0.099 | +0.010 | 0.10 | 47 | 52.7 | 0.92 | -0.262 | +0.190 | -0.005 | **147% (1 day)** | -0.063 |
| F6-17 | Nasdaq 15-min ORB with Gap traded as QQQ, Long | 44 | 0.13 | -0.099 | +0.141 | -0.001 | -0.01 | 47 | 54.5 | 0.83 | +0.373 | -0.997 | -0.024 | n/a | -0.216 |
| F6-18 | Nasdaq 15-min ORB with Gap traded as QQQ, Short | 53 | 0.15 | +0.075 | +0.087 | +0.080 | 0.60 | 40 | 54.7 | 0.98 | -0.455 | +0.272 | +0.063 | 23% | -0.199 |

Notes on the table:
- "n/a" in the best-day-share column means total R is negative, so the share is undefined.
- Best-day shares at or above 50% are flagged in bold: the record rests on one day.

## Why no rework rows were added
Rule 18 allows rework rows after a failure, but each one is counted. The largest sample here is 41-53 trades for a single
instrument (190-203 for the four-ETF row). To reach t 3.52 on 50 trades, a row needs an average of about +0.5R at a
standard deviation of about 1R, which is more than 3× the best row. No neighbouring variant can clear the t-stat or the
trade rate, so adding rows would only raise N.

## What would be needed to go further
None of these is proposed now.
- Take the short side as a regime-conditioned idea. On the stock universe that is already F2-G4 (the QQQ gate) and
  F3-I (the SPY-VWAP gate).
- Get an owner decision on whether index-only setups may run below 3 trades per session (the IDX precedent). Even then,
  t ≈ 1 is far from evidence.

Scratch has been deleted. Nothing was committed, and config/, mcf/ and the ledger were not touched.
