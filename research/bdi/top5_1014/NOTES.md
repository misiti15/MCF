# Top-5 setup tune, 2026-10-14 (first run of the owner's daily task): FAILED, 0 of 75

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions (rule 7): a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history (2024-10, 2025-03..2026-10-07), with production
  and time-of-day costs in. The rule-19 locked block (2024-11-01..2025-02-28) was **never loaded**.
- `PLAN.md` was written before any history configuration was scored, and nothing was appended to it afterwards.
- **Configurations scored: 75** (CWT14 44, heat_fade_short-FD 15, RW7-FD 16), plus 5 parent reference runs.
- **Passes: 0.** 0 variants have exp > 0, 0 beat their parent at the bar, 0 meet the Testing bar, 0 meet the
  research bar. No holdout was scored, because no variant qualified for one.
- **No Testing addition is proposed.** No config entry is written. config/ and mcf/ are untouched.

Files: `live_top5.py` (ranking and live stats: `live_rank.csv`, `live_top5.csv`, `live_top5_detail.txt`),
`scan_top5.py` (history scan; it checks the numba CWT14 kernel against `cwt_live_lib.b3` on 2025-06 first),
`report_top5.py` (`results.csv`, `summary.json`), `add_backlog.py`.
Runtime is about 8 minutes. The scratch trades file and the journal copies were deleted afterwards.

## Failures first

| setup (account) | variants | exp > 0 | beat parent at bar | improve on TRAIN and VALID | best improvement (t / bar) |
|---|---|---|---|---|---|
| CWT14-failbrk-orl-p05-long (T2) | 14 | 0 | 0 | 2 | V05 window from 10:30: -0.0824R vs -0.0933R, +0.011R (t 1.53 / 2.30) |
| CWT14-failbrk-orl-p05-lowvol-long (T2) | 16 | 0 | 0 | 1 | V05 window from 10:30: -0.0806R vs -0.0909R, +0.010R (t 1.47 / 2.36) |
| CWT14-failbrk-pdl-p05-long (T2) | 14 | 0 | 0 | 2 | V04 reclaim within 4 bars: -0.0840R vs -0.0865R, +0.002R (t 1.74 / 2.30) |
| heat_fade_short-FD (T1) | 15 | 0 | 0 | 1 | H09 above VWAP: -0.0238R vs -0.0304R, +0.007R (t 1.49 / 2.33) |
| RW7-gapdn-bounce-early-short-FD (T1) | 16 | 0 | 0 | 4 | R13 above VWAP: -0.0460R vs -0.0619R, +0.016R (t 1.18 / 2.36) |

In all, 10 of the 75 variants improve on both TRAIN and VALID (`results.csv`, columns `d_train` and `d_valid`), and
each of them is still negative.

**Why nothing could pass.** All 5 parents are negative after costs on history: CWT14 runs -0.086 to -0.092R
(t -9 to -10) and the two FD shorts run -0.03 to -0.06R. Their sign is set by the session regime:
- CWT14 longs are up +0.04..+0.05R and down -0.20R.
- heat_fade_short-FD is up -0.26R and down +0.14R.
- RW7-FD is up -0.30R and down +0.10R.

No one-knob change moves that split. Every variant's up/down pair stays within about 0.03R of its parent's, except
the exit-geometry variants, which widen the split. Walk-forward shares are 0.0-0.1 (CWT14), 0.2-0.4 (heat) and
0.1-0.3 (RW7), against a bar of 0.6.

## 1. The five setups, live (5 sessions, real trades, run 1)
Ranking (`live_rank.csv`): 2,428 real trades, S6 excluded. CWT14 setups take 3 of the top 5 places because Testing 2
started on 10-12 and trades many names. Testing 1 and 2 have only 3 sessions in the window (10-12, 13, 14).

| # | setup | acct | n | win | avg R | P/L | med MFE / MAE (R) | stop / target / flat | losers that never worked (MFE < 0.2R) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CWT14-failbrk-orl-p05-long | T2 | 191 | 58.6% | -0.106 | -$241.54 | 0.34 / 0.48 | 64 / 110 / 17 | 30 of 79 |
| 2 | CWT14-failbrk-orl-p05-lowvol-long | T2 | 190 | 55.8% | -0.202 | -$283.16 | 0.35 / 0.48 | 72 / 106 / 12 | 22 of 84 |
| 3 | heat_fade_short-FD | T1 | 156 | 45.5% | -0.039 | -$84.53 | 0.41 / 0.65 | 41 / 44 / 71 | 37 of 85 |
| 4 | CWT14-failbrk-pdl-p05-long | T2 | 132 | 49.2% | -0.250 | -$280.23 | 0.41 / 0.68 | 57 / 62 / 13 | 24 of 67 |
| 5 | RW7-gapdn-bounce-early-short-FD | T1 | 126 | 50.8% | +0.001 | +$46.34 | 0.61 / 0.61 | 28 / 41 / 57 | 21 of 62 |

**Live vs backtest** (parent, full open history, production costs, one trade per symbol-day):

| setup | live win / avg R | backtest win / exp (n, t) | backtest up / down sessions |
|---|---|---|---|
| CWT14 orl-p05 | 58.6% / -0.106 | 63.2% / -0.092 (105,023, t -9.9) | +0.044 / -0.204 |
| CWT14 orl-p05-lowvol | 55.8% / -0.202 | 63.6% / -0.089 (74,014, t -9.3) | +0.055 / -0.200 |
| heat_fade_short-FD | 45.5% / -0.039 | 49.2% / -0.033 (75,136, t -2.3) | -0.257 / +0.138 |
| CWT14 pdl-p05 | 49.2% / -0.250 | 63.9% / -0.086 (66,875, t -9.8) | +0.046 / -0.207 |
| RW7-FD | 50.8% / +0.001 | 49.0% / -0.058 (26,164, t -3.0) | -0.295 / +0.105 |

The up/down columns are computed on TRAIN+VALID. The backtest n matches the earlier studies exactly for heat FD
(75,136) and RW7-FD (26,164), and matches verify.json for CWT14 orl-p05 (105,023).

**Where the losers cluster** (`live_top5_detail.txt`)
- **CWT14 ORL (both versions)**
  - Most of the trades and losses come in the first ORL bars, 10:05-10:30: 120 of 191 trades at -0.187R, and 126
    of 190 at -0.240R for lowvol.
  - Live, 10:30 onwards is near flat or positive on small n.
  - On history, the matching variant (V05, start 10:30) is the best of the grid, but it is still -0.08R and below
    its bar.
  - Stops average -1.03R and targets +0.43R, so the t05s1 geometry needs a win rate of about 70%. History gives 63%.
- **CWT14 PDL**
  - 10-14 alone: 50 trades, 18% wins, -0.81R.
  - The 09:50 bar: 49 trades at -0.654R.
  - Skipping the first bar was already tested and failed tonight (nightly1014: -0.009..+0.003R), so it was not
    repeated.
- **heat_fade_short-FD**
  - Losses are worst at 10:30-11:30 (-0.21R, n 20) and 13:00-15:00 (-0.14R, n 51). 11:30-13:00 is about flat
    (n 82).
  - 71 of 156 trades ride to the 15:55 flatten (-0.08R).
  - 10-13 (split tape) lost -15.8R; 10-12 made +10.3R.
- **RW7-FD**
  - 14:00-15:00 entries run -0.147R with 31% wins (n 26).
  - 57 of 126 trades go to the flatten.
  - The 10-14 down day made +10.9R, and the other two days lost.
- In all 5 setups the live losers' mean give-back (MFE minus final R) is 1.0-1.35R. Most losers never got going:
  only 4-15 losers per setup ever reached +0.5R. So the exits are not the problem. The entries' direction is, and it
  follows the session.

**How each was originally built and backtested**
- CWT14: `research/bdi/cwt/TESTPLAN.md` section 3 and `test_b/` (package B, 96 configurations). Its verdict was
  "retire/rework". It is live in Testing 2 as an owner-directed forward test. Parity is in `cwt/live/verify.json`.
- heat_fade_short: the heat study 2026-10-06 (`research/heat/HEAT_STUDY.md`, regime_9; ledger 2026-10-06-heat).
  The full-day copy comes from `research/bdi/fullday` and `research/bdi/timeofday` (full day -0.032R).
- RW7: the rework1008 module (`bdi-rw-gapdn-bounce-early`, lineage N 82,964), with the full-day copy from timeofday
  (-0.058R).

## 2. Grid results (all 75 in `results.csv`)
For every variant, `results.csv` gives:
- n, win and exp on TRAIN, VALID and TRAIN+VALID, with the day-clustered t;
- ex-best-day, up / flat / down, and the walk-forward share;
- the excess over the same-minute random control, with its t;
- the change against the parent on TRAIN, VALID and TRAIN+VALID, with the day-block bootstrap t;
- the plateau check, the Testing-bar flag, and the research verdict at the lineage N.

What moved, and by how much:
- **Thresholds ±10-20%** (CWT p, reclaim bars, volumeRatio cap; heat SHORT_AT; RW7 heat, buyPressure, RSI band) move
  exp by less than 0.008R. The parents sit on a flat, negative plateau.
- **Exit geometry:**
  - t1s1 and t1s05 make every CWT14 parent worse, by 0.014-0.021R.
  - t05s1 and t1s05 make the FD shorts worse, by 0.002-0.007R.
- **Window:**
  - Starting at 10:30 helps ORL (+0.010-0.011R).
  - Ending at 13:00/14:00 hurts CWT, is neutral for heat, and gives +0.002R for RW7.
- **VWAP:**
  - For the FD shorts, "above VWAP" is the best filter (heat +0.007R; RW7 +0.016R, n 27/day).
  - For PDL, "above VWAP" gives +0.008R.
  - None of these crosses its bar, and all stay negative.
- **Same-minute random control:**
  - The two FD shorts beat random shorts at the same minute (heat +0.055R, t 8.2; RW7 +0.017R, t 1.8). Random
    shorts lose more, because names drift up after the minute they fire.
  - CWT14 is worse than random longs at the same minute (-0.008 to -0.013R).
  - The FD shorts carry some timing information, but not enough to pay for the session's direction plus costs.

## 3. Bars applied (PLAN section 4)
- **Beats parent:** improvement > 0 on TRAIN and VALID, and bootstrap t >= max(1.5, sqrt(2 ln N_setup)), which is
  2.30-2.36. 0 of 75 met it. The best t is 1.74.
- **Testing bar:** t >= 2.94, plus every other gate. 0 met it.
- **Research bar** (cumulative lineage N):
  - CWT14: 121,133, t >= 4.84
  - heat: 19,721, t >= 4.45
  - RW7: 82,980, t >= 4.76
  - 0 met it.
- The plateau checks for one-value knobs were not needed (no variant reached that step), so N stays 75.

## Backlog (tag `top5-tune`; `research/BACKLOG.md` regenerated, 396 entries)
One entry per setup's grid, all `failed`, with the numbers above. `configs_tried` is the cumulative lineage count.

| id | status |
|---|---|
| `top5-1014-CWT14-failbrk-orl-p05-long-tune` | failed |
| `top5-1014-CWT14-failbrk-orl-p05-lowvol-long-tune` | failed |
| `top5-1014-CWT14-failbrk-pdl-p05-long-tune` | failed |
| `top5-1014-heat_fade_short-FD-tune` | failed |
| `top5-1014-RW7-gapdn-bounce-early-short-FD-tune` | failed |

## Proposed Testing additions
**None.** No variant met the Testing bar. No Primary setup is affected.

## vs yesterday
This is the first run, so there is no previous top-5 run to compare with.

## Next run (queued, not scored)
- **The near-misses improve on both splits but are below their bars:**
  - ORL start-10:30 (V05)
  - FD shorts above VWAP (H09, R13)
  - PDL reclaim within 4 bars (V04)

  Re-scoring them on the same history would leak. They are judged only on forward sessions, or as part of a
  pre-declared pair-tweak round (rule 18) that counts against the same lineage N.
- **The top 5 are set by volume.** The 3 CWT14 setups lead because Testing 2 trades many names, and on history all
  3 are -0.09R with t -9. Tuning by one knob cannot fix that. Their removal decision belongs to the owner after the
  4-session scorecard (10-15 is Testing 2's 4th session), with the history numbers above.
