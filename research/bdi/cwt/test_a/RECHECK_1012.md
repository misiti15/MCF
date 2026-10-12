# Package A re-check after the stop-side fix (2026-10-12)

*Educational only - not financial advice. These are lab backtests on the open two-year history (train, valid and
open sessions). The locked block 2024-11-01..2025-02-28 is never loaded and was not scored. Costs are in, and R =
0.25 x daily ATR.*

## Failures first

- **The verdict does not change: 566 of 566 configurations still fail.** No pass/fail verdict flips. No
  configuration reaches t >= 2 at n >= 150, and none passes its try-count t bar.
- **The bug inflated every configuration it touched.** 41 configurations move, and all 41 get worse or stay the same.
  One configuration changes sign: A7 gap<=-10 earn T2 S guest (cid 389) goes from +0.027 to -0.027.
- **The two A7 rows behind Testing 2 shrink.** cid 373 drops from +0.141 to +0.131 R (t 0.78 -> 0.70). cid 341 drops
  from +0.047 to +0.033 R (t 0.40 -> 0.27).

## The bug and the fix

`engine.sim` puts the stop first, and on the entry minute it fills at the stop price. A structural short whose entry
(the open of the minute after the signal bar) was already at or above its stop was therefore "stopped" at once at
the stop price. That price was below the entry, so the trade was booked as a gain. The mirror case did the same for
longs entered at or below their stop.

The structural exits now share one guard, `engine.stop_ok`. It requires the stop to be finite and
`side * (entry - stop) > 0`, which is the guard the live LabStrategy structural branch uses in
`mcf/strategies/setups.py`. Entries that fail it return NaN and are not emitted. The guard covers these exits:

- `exit_struct` (S);
- `exit_overnight` (ON);
- `exit_hold_days` (S2);
- `exit_half_2r` (A3 S).

The A3 S stop is always on the correct side by construction, so A3 does not move. The geometric exits (t1s1, t05s1,
t1s05) are unchanged, because their stop is always the entry +-kR.

The regression check is `check_stop_side.py`. It uses synthetic frames and no market data. It passes on the fixed
engine and fails on the old one with `AssertionError: ('S', -1, 9.9)`.

## Re-run: same grid, same gates

The grid and the gates are the same as before, with no configuration added or dropped: 566 configurations (A1 68,
A2 96, A3 72, A4 32, A5 18, A6 64, A7 64, A8 80, A9 72). Commands: `run.py` (1,226 symbols), then `score.py`. The
bar cache is unchanged since the original run.

The fix removes 1,640 trades: 2,476,458 before, 2,474,818 after. 41 configurations move, and the other 525 are
identical:

| family | moved | trades removed | largest exp change |
|---|---|---|---|
| A1 (S and ON, short) | 16 | 84 | -0.004 R |
| A6 (S, short and long) | 16 | 1,248 | -0.001 R |
| A7 (S, short) | 9 | 308 | -0.053 R |
| A2, A3, A4, A5, A8, A9 | 0 | 0 | - |

### Every moved configuration (before -> after)

| cid | config | n | exp R | t |
|---|---|---|---|---|
| 0 | A1 r3_30 T1 S full | 839 -> 825 | -0.301 -> -0.305 | -3.42 -> -3.41 |
| 1 | A1 r3_30 T1 S guest | 766 -> 752 | -0.302 -> -0.306 | -3.23 -> -3.22 |
| 2 | A1 r3_30 T1 ON full | 834 -> 820 | -0.298 -> -0.302 | -2.70 -> -2.69 |
| 3 | A1 r3_30 T1 ON guest | 762 -> 748 | -0.255 -> -0.258 | -2.22 -> -2.20 |
| 10 | A1 r3_30 T2 S full | 822 -> 820 | -0.328 -> -0.328 | -3.44 -> -3.44 |
| 11 | A1 r3_30 T2 S guest | 726 -> 724 | -0.330 -> -0.330 | -3.18 -> -3.17 |
| 12 | A1 r3_30 T2 ON full | 817 -> 815 | -0.377 -> -0.377 | -3.14 -> -3.13 |
| 13 | A1 r3_30 T2 ON guest | 722 -> 720 | -0.307 -> -0.307 | -2.42 -> -2.41 |
| 20 | A1 r3_50 T1 S full | 172 -> 169 | -0.144 -> -0.145 | -0.66 -> -0.66 |
| 21 | A1 r3_50 T1 S guest | 154 -> 151 | -0.189 -> -0.191 | -0.79 -> -0.79 |
| 22 | A1 r3_50 T1 ON full | 172 -> 169 | -0.031 -> -0.030 | -0.13 -> -0.12 |
| 23 | A1 r3_50 T1 ON guest | 154 -> 151 | -0.138 -> -0.139 | -0.52 -> -0.52 |
| 40 | A1 streak3_r5_50 T1 S full | 223 -> 221 | -0.328 -> -0.330 | -2.14 -> -2.13 |
| 41 | A1 streak3_r5_50 T1 S guest | 204 -> 202 | -0.277 -> -0.279 | -1.73 -> -1.72 |
| 42 | A1 streak3_r5_50 T1 ON full | 222 -> 220 | -0.266 -> -0.268 | -1.41 -> -1.40 |
| 43 | A1 streak3_r5_50 T1 ON guest | 203 -> 201 | -0.270 -> -0.272 | -1.40 -> -1.39 |
| 268 | A6 g0.3 pd short full | 39,452 -> 39,280 | -0.171 -> -0.172 | -5.98 -> -5.98 |
| 269 | A6 g0.3 pd short guest | 33,700 -> 33,528 | -0.184 -> -0.184 | -6.65 -> -6.65 |
| 276 | A6 g0.3 pd long full | 36,642 -> 36,527 | -0.146 -> -0.146 | -4.37 -> -4.36 |
| 277 | A6 g0.3 pd long guest | 31,245 -> 31,130 | -0.158 -> -0.159 | -4.74 -> -4.74 |
| 284 | A6 g0.3 d5 short full | 23,291 -> 23,173 | -0.208 -> -0.209 | -8.54 -> -8.52 |
| 285 | A6 g0.3 d5 short guest | 20,339 -> 20,221 | -0.215 -> -0.216 | -8.52 -> -8.51 |
| 292 | A6 g0.3 d5 long full | 19,936 -> 19,853 | -0.175 -> -0.176 | -3.91 -> -3.90 |
| 293 | A6 g0.3 d5 long guest | 17,154 -> 17,071 | -0.187 -> -0.187 | -4.32 -> -4.31 |
| 300 | A6 g0.5 pd short full | 15,888 -> 15,847 | -0.158 -> -0.158 | -2.99 -> -2.99 |
| 301 | A6 g0.5 pd short guest | 12,943 -> 12,902 | -0.181 -> -0.181 | -3.58 -> -3.58 |
| 308 | A6 g0.5 pd long full | 15,518 -> 15,489 | -0.139 -> -0.139 | -2.54 -> -2.53 |
| 309 | A6 g0.5 pd long guest | 12,589 -> 12,560 | -0.148 -> -0.148 | -2.56 -> -2.55 |
| 316 | A6 g0.5 d5 short full | 10,952 -> 10,922 | -0.210 -> -0.210 | -5.92 -> -5.92 |
| 317 | A6 g0.5 d5 short guest | 9,322 -> 9,292 | -0.225 -> -0.226 | -5.89 -> -5.88 |
| 324 | A6 g0.5 d5 long full | 10,711 -> 10,675 | -0.184 -> -0.184 | -2.90 -> -2.90 |
| 325 | A6 g0.5 d5 long guest | 9,017 -> 8,981 | -0.197 -> -0.198 | -3.11 -> -3.11 |
| 332 | A7 G5 out T1 S full | 3,663 -> 3,652 | -0.065 -> -0.066 | -0.33 -> -0.34 |
| 333 | A7 G5 out T1 S guest | 3,663 -> 3,652 | -0.065 -> -0.066 | -0.33 -> -0.34 |
| 340 | A7 G5 out T2 S full | 4,163 -> 4,156 | +0.069 -> +0.069 | 0.24 -> 0.24 |
| **341** | **A7 G5 out T2 S guest (Testing 2)** | **3,885 -> 3,695** | **+0.047 -> +0.033** | **0.40 -> 0.27** |
| 356 | A7 G5 earn T2 S full | 1,097 -> 1,096 | -0.299 -> -0.300 | -2.32 -> -2.32 |
| 357 | A7 G5 earn T2 S guest | 1,010 -> 962 | -0.140 -> -0.174 | -1.40 -> -1.68 |
| **373** | **A7 G10 out T2 S guest (Testing 2)** | **589 -> 566** | **+0.141 -> +0.131** | **0.78 -> 0.70** |
| 388 | A7 G10 earn T2 S full | 400 -> 399 | -0.219 -> -0.222 | -1.33 -> -1.34 |
| 389 | A7 G10 earn T2 S guest | 361 -> 345 | +0.027 -> -0.027 | 0.20 -> -0.21 |

### Changes in the gate columns

- **Verdicts:** probation passes go from 0 to 0. The plan and lineage t passes go from 0 to 0.
- **Regime pass:** 0 to 0. The 10 apparent changes are A8 rows with n = 0, where the value is NaN on both sides.
- **Fail-reason sets:** two configurations change, and both still fail:
  - cid 21 now also fails walk-forward (0.60 -> 0.50);
  - cid 389 now also fails exp <= 0 (walk-forward 0.333 -> 0.300).
- **A7 family row in NOTES.md section 2:** configurations with exp > 0 go from 7 to 6. The best t goes from 0.78 to
  0.70, with best n >= 150 for cid 373 at +0.131 R, t 0.70, up -0.29 / down +0.37. The median exp (-0.109) and the
  walk-forward count (2) are unchanged.
- **A1 family row:** the walk-forward >= 0.6 count goes from 13 to 12. The median exp goes from -0.141 to -0.142.
- **The other families' rows are unchanged.**
- **`results.csv`** has been regenerated with the fixed engine.

## The 4 A7 setups in Testing 2

The parity check `live/verify_a.py` was re-run against the fixed trades. Its output is saved to
`data/verify_a_1012.json`. `live/verify_a.json` and `verify.json` are left as shipped.

| setup | cid | scored n before -> after | module n | only-scored before -> after | match before -> after | exp scored before -> after |
|---|---|---|---|---|---|---|
| CWT09-gapdn-bounce-g10-lowerhalf-short | 373 | 589 -> 566 | 567 | 22 -> 0 (only-module 0 -> 1) | 95.8% -> 99.5% | +0.141 -> +0.131 |
| CWT09-gapdn-bounce-g5-lowerhalf-short | 341 | 3,885 -> 3,695 | 3,692 | 193 -> 8 (only-module 0 -> 5) | 94.5% -> 99.2% | +0.047 -> +0.033 |
| CWT09-gapdn-vwaploss-g10-short | 365 | 551 (unchanged) | 551 | 0 | 99.8% | +0.041 |
| CWT09-gapdn-vwaploss-g5-short | 339 (t1s05) | 3,663 (unchanged) | 3,663 | 0 | 99.8% | -0.031 |

- **Two of the four setups are affected: the T2 "lowerhalf" pair.** Their engine numbers now match the live-tradable
  figures in `live/NOTES.md`:
  - g10 (cid 373): n 566 / +0.131, against NOTES' n 567 / +0.131;
  - g5 (cid 341): n 3,695 / +0.033, against NOTES' n 3,695 / +0.032.
- **The two vwaploss setups are not affected.** The T1 S guest row (cid 365) did not move, and cid 339 is geometric.
- **The 13 trades that now differ (8 only-scored and 5 only-module, both pairs).** The live guard compares the stop
  with the signal bar's close. The engine compares it with the next minute's open, which is the actual entry. When
  price sits right at the stop, the two can disagree. The remaining other-bar rows (3 and 21) are unchanged from
  before the fix.
- **No change to `config/` or `mcf/` is needed.** The live module already skips these entries.

## Files

- `engine.py`: adds `stop_ok` and the guard in the S, ON, S2 and A3-S exits.
- `check_stop_side.py`: the regression check.
- `results.csv`: regenerated.
- `data/` (git-ignored): `trades.parquet`, `results.csv`, `run_1012.log`, `verify_a_1012.json`.
