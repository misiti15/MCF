# Top-5 setup execution tune, 2026-10-16 (third run): FAILED the Testing bar, 0 of 80; 9 beat their parent

*Educational only - not financial advice.*

- Live numbers are **paper** trades from 5 sessions, 10-12..10-16 (rule 7). They are a diagnosis, not evidence.
- History numbers are **backtests** on the open two-year history (2024-10, 2025-03..2026-10-07), with production and
  time-of-day costs in. TRAIN+VALID is shown unless a row says otherwise.
- The rule-19 locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was scored, because nothing
  reached the Testing bar.
- `PLAN.md` was written before any history configuration was scored. Nothing was appended afterwards.
- **Configurations scored: 80.** That is pdh-short 21, orl-p10 14, orl-p10-lowvol 14, coil 12 and RW7 19, plus 5
  parent reference runs.
- **0 variants have exp > 0. 0 meet the Testing bar. 0 meet the research bar. 9 beat their parent** at the
  pre-declared bar. 4 of those 9 also clear the lineage bar.
- **No Testing addition is proposed.** config/ and mcf/ are untouched, and nothing was committed by this run.

Files:
- `live_rank.py`: ranks the setups and writes `live_rank.csv`, `live_top5.csv` and `live_top5_detail.txt`.
- `scan_1016.py`: the history scan. It is `top5_1015/scan_1015.py` plus a short-side b3 kernel, no-target
  (hold) mode, a trailing stop, a clock exit and re-entry after a stop.
- `report_1016.py`: writes `results.csv`, `summary.json` and `hist_parent_detail.txt`.
- `add_backlog.py`: writes the backlog entries.
- **Parity on 2025-06:** the short and lowvol b3 kernels equal `cwt_live_lib.b3`. All 5 parents equal
  `gates.lab_trades` trade for trade (mean |diff| 3-4e-5 R).
- The parent n on the full open history match their config/verify numbers: 43,876 / 39,989 / 31,676 / 44,505 / 26,164.

## Rotation and selection
Each of the excluded setups is listed with its live trade count over the 5 sessions.

**Rotated out:**
- CWT14 orl-p05 (301), orl-p05-lowvol (294) and pdl-p05 (192). These got a change: `scale_out_r 0.25` with
  `live_scale_out` from 10-19.
- heat_fade_short-FD (240). It was tuned on 10-14 and 10-15 with no change.

**Next five eligible:** listed below. No Primary-promoted FD setup is in range; the nearest, MF3-FD, has 43 trades.

## Failures first

| setup (acct) | n var | exp>0 | beat parent | best (d R; t_improve / setup bar / lineage bar) |
|---|---|---|---|---|
| CWT14-failbrk-pdh-p05-lowvol-short (T2) | 21 | 0 | 4 | E06 scale-out 0.35R: -0.0761 vs -0.0968, **+0.0207R, t 8.15** / 2.47 / 4.84 (E05 0.25R: +0.0233R, t 5.61) |
| CWT14-failbrk-orl-p10-long (T2) | 14 | 0 | 2 | E06 scale-out 0.35R: +0.0191R, **t 5.29** / 2.30 / 4.84 |
| CWT12-coil-k4-long (T2) | 12 | 0 | 1 | E06 scale-out 0.35R: +0.0127R, **t 3.48** / 2.23 / 3.25 |
| CWT14-failbrk-orl-p10-lowvol-long (T2) | 14 | 0 | 2 | E06 scale-out 0.35R: +0.0194R, **t 5.21** / 2.30 / 4.84 |
| RW7-gapdn-bounce-early-short-FD (T1) | 19 | 0 | 0 | H08 flat 14:30: +0.0066R, t 0.58 / 2.43 / 4.76 |

**Every parent is negative after costs.** On TRAIN+VALID:

| setup | exp | t |
|---|---|---|
| pdh-short | -0.097R | -10.4 |
| orl-p10 | -0.089R | -6.1 |
| orl-p10-lowvol | -0.088R | -6.9 |
| coil | -0.073R | -4.9 |
| RW7 | -0.062R | -3.0 |

The best execution change narrows the loss by about 0.02R. It does not change the sign. The walk-forward share is
0.0-0.2. CWT14's excess over the same-minute random control is negative for every variant.

## 1. Live (paper, 5 sessions) vs backtest

| setup | live n | live win / BE win | live avg win / loss | backtest win / BE win / exp | med MFE / MAE (bt) | loser give-back (bt) |
|---|---|---|---|---|---|---|
| pdh-p05-lowvol-short | 169 | 61.5 / 66.7% | +0.49 / -0.98 | 63.1 / 69.6% / -0.097 | 0.54 / -0.52 | 1.22R |
| orl-p10-long | 165 | 59.4 / 69.9% | +0.44 / -1.03 | 65.0 / 70.7% / -0.089 | 0.54 / -0.51 | 1.28R |
| coil-k4-long | 165 | 63.0 / 68.6% | +0.46 / -1.01 | 63.5 / 68.5% / -0.073 | 0.53 / -0.48 | 1.20R |
| orl-p10-lowvol-long | 157 | 61.8 / 71.0% | +0.43 / -1.05 | 64.4 / 70.2% / -0.088 | 0.54 / -0.51 | 1.26R |
| RW7-FD | 156 | 53.2 / 49.9% | +0.67 / -0.67 | 48.7 / 52.5% / -0.062 | 0.64 / -0.60 | 1.17R |

Live avg R by setup:

| setup | live avg R | live P/L |
|---|---|---|
| pdh-p05-lowvol-short | -0.076 | -$77 |
| orl-p10-long | -0.155 | -$293 |
| coil-k4-long | -0.081 | -$166 |
| orl-p10-lowvol-long | -0.137 | -$163 |
| RW7-FD | +0.044 | +$158 |

**Loser clusters (live):**
- **pdh short.** The 10:00-11:30 entries (122 trades) run at -0.12 to -0.15R. The 09:50 bar is positive (+0.19R,
  28 trades). 10-15 (up day) was the worst day, at -11.5R.
- **orl-p10 and orl-p10-lowvol.** The 10:00-10:30 entries make up 131 and 95 trades, at -0.16 and -0.22R. 10-16
  (down day) was the worst day, at -11.8 and -12.6R.
- **coil.** The 10:30-11:30 entries make up 133 trades, at -0.09R. 10-16 was the worst day, at -14.0R (27% wins).
- **RW7.**
  - 71 of 156 trades rode to 15:55.
  - 15 of 73 losers had reached +0.5R first.
  - 10-13 was the worst day, at -8.3R. 10-14 and 10-16 (down days) were positive.

**Never-worked losers:** in every CWT setup, 28-30 live losers never reached +0.2R. On the backtest the share is
53-55%.

**Regime split of the parents (backtest):** this is the same split as in the last two runs.
- CWT longs: up sessions +0.03 to +0.07R, down sessions -0.18 to -0.23R.
- Shorts: up sessions -0.22R (pdh) and -0.30R (RW7); down sessions +0.00R (pdh) and +0.10R (RW7).

## 2. Grid results
All 80 rows are in `results.csv`, with win rate, avg win / loss, break-even win, margin and the share of losers
that never worked.

| knob | 3 CWT14 (d R) | coil | RW7 | effect on the win/loss shape |
|---|---|---|---|---|
| E01-E03 time stop 30/60/90 min | +0.000..+0.004 | +0.002..+0.005 | -0.001..+0.003 | Avg loss -1.03 -> -0.78R, win 63 -> 56% (30 min); a wash, t <= 1.9 |
| E04 breakeven 0.35R (RW7 0.5R) | -0.006..-0.009 | -0.008 | -0.015 | Cuts winners: win 63 -> 51% |
| **E05 scale-out half at +0.25R** | **+0.018..+0.023** | +0.010 | -0.009 | Win 63 -> 70-71%, avg loss -1.03 -> -0.85..-0.88 |
| **E06 scale-out half at +0.35R** (RW7 0.5R) | **+0.019..+0.021** | **+0.013** | -0.007 | Win 63 -> 69-70%; the best t in each CWT setup |
| E07/E08 stop 0.85 / 0.75R | -0.005..+0.000 | -0.002..0.000 | -0.001..-0.002 | Loss -1.03 -> -0.85R, but win falls just as much |
| E09 wait one bar | +0.007..+0.011 | +0.001 | -0.003 | pdh short beats its bar (t 2.91) |
| E10 flow3 agrees | -0.000..+0.010 | +0.003 | +0.005 (t 0.7) | pdh short beats its bar (t 2.81); 33-45% fewer trades |
| E11 window from 10:30 | +0.005..+0.009 | +0.002 | - | The live 10:00-10:30 cluster is only slightly worse on history (t <= 0.98) |
| E12/E13 poke depth +-20% | -0.003..+0.002 | - | - | Flat plateau |
| O1 re-entry after stop (own exp) | -0.054..-0.086 | -0.018 (213) | -0.008 (627) | All negative; RW7 TRAIN +0.030 / VALID -0.112 |

### Hold winners longer, SHORT setups (owner's question from tonight's BDI). Exp by session regime (TRAIN+VALID)

| variant | pdh-short: all / up / flat / down | RW7-FD: all / up / flat / down |
|---|---|---|
| parent (target 0.5R / 1R) | -0.097 / -0.218 / -0.063 / **+0.000** | -0.062 / -0.295 / -0.046 / **+0.105** |
| H01 hold to 15:55 (no target) | -0.118 / -0.449 / -0.118 / **+0.245** | -0.079 / -0.418 / -0.072 / **+0.175** |
| H02 trail 0.5R after +0.5R | -0.120 / -0.260 / -0.095 / +0.008 | -0.086 / -0.263 / -0.086 / +0.050 |
| H03 trail 1R after +1R | -0.123 / -0.357 / -0.103 / +0.112 | -0.076 / -0.345 / -0.074 / +0.129 |
| H04 trail 0.75R after +0.5R | -0.127 / -0.294 / -0.106 / +0.034 | -0.084 / -0.287 / -0.093 / +0.078 |
| H05 target x2 | -0.103 / -0.306 / -0.067 / +0.080 | -0.067 / -0.377 / -0.061 / +0.165 |
| H06 half at target, runner to BE / 15:55 | -0.110 / -0.278 / -0.092 / +0.054 | -0.070 / -0.339 / -0.064 / +0.132 |
| H07 half at target, runner trails 0.5R | -0.108 / -0.239 / -0.079 / +0.004 | -0.068 / -0.306 / -0.057 / +0.106 |
| H08 RW7 flat at 14:30 | - | -0.055 / -0.239 / -0.040 / +0.073 |

**Holding the shorts to the close does exactly what tonight's BDI saw on down days.** pdh down sessions improve from
+0.00 to +0.25R, and RW7 from +0.10 to +0.18R.

**On up sessions it loses more than it gains.** pdh falls from -0.22 to -0.45R and RW7 from -0.30 to -0.42R.
- Net, every hold/trail variant is worse than its parent (d -0.006..-0.031R), in both shorts.
- Without a day-direction call that is known at entry, hold-to-close is a bet on the day.
- bdi1016 showed that the early (10:00/10:30) day class is too weak to carry that bet.

**Not proposed.**

## 3. Bars applied (PLAN section 4)
**Beats parent:** d > 0 on TRAIN and on VALID, and t_improve >= the setup bar. 9 variants qualify:

| variant | d TRAIN / VALID | t_improve | setup bar | lineage bar | variant exp (t) | up / down |
|---|---|---|---|---|---|---|
| pdh-short E06 scale-out 0.35R | +0.020 / +0.022 | **8.15** | 2.47 | **4.84 met** | -0.076 (-9.9) | -0.169 / -0.006 |
| pdh-short E05 scale-out 0.25R (d +0.023) | +0.023 / +0.024 | **5.61** | 2.47 | **4.84 met** | -0.074 (-11.6) | -0.146 / -0.020 |
| orl-p10 E06 scale-out 0.35R | +0.023 / +0.013 | **5.29** | 2.30 | **4.84 met** | -0.070 (-5.7) | +0.019 / -0.141 |
| orl-p10-lowvol E06 scale-out 0.35R | +0.021 / +0.016 | **5.21** | 2.30 | **4.84 met** | -0.069 (-6.4) | +0.025 / -0.133 |
| coil E06 scale-out 0.35R | +0.011 / +0.015 | 3.48 | 2.23 | **3.25 met** | -0.060 (-5.0) | +0.050 / -0.178 |
| orl-p10 E05 scale-out 0.25R | +0.027 / +0.007 | 3.41 | 2.30 | 4.84 not met | -0.069 (-6.6) | +0.002 / -0.127 |
| orl-p10-lowvol E05 scale-out 0.25R | +0.023 / +0.010 | 3.27 | 2.30 | 4.84 not met | -0.070 (-7.5) | +0.004 / -0.121 |
| pdh-short E09 wait one bar | +0.010 / +0.013 | 2.91 | 2.47 | 4.84 not met | -0.086 (-8.8) | -0.216 / +0.028 |
| pdh-short E10 flow3 < 0 | +0.014 / +0.004 | 2.81 | 2.47 | 4.84 not met | -0.087 (-9.1) | -0.211 / +0.007 |

- **Testing bar** (exp > 0 on TRAIN and VALID, t >= 2.96, up and down sessions each > 0, WF >= 0.6, excess over
  random > 0, plateau): **0 met it.** Every variant is negative.
- **Research bar** (lineage N 121,230 / 196 / 82,999): **0 met it.**
- **Scale-out is mostly an exit effect, not information in the setup.**
  - The excess over the same-minute random control (run through the same scale-out) barely moves: CWT14 parents
    -0.009..-0.013R, scale-out variants -0.008..-0.013R; coil +0.014 -> +0.008R.
  - So random entries gain about as much from the scale-out. This repeats 10-15's X06 finding on 4 more setups.

## Proposals and live-support check (mcf/execution/runner.py, mcf/strategies/setups.py)
**No Testing addition is proposed.** No variant meets the Testing bar. The table below only records what each
beats-parent knob would need if the owner wanted it as an exit change in the same family as 10-16's CWT14 scale-out.
Any such change would also need an after-hours merge and a ledger entry (rules 9 and 11).

| knob | live support |
|---|---|
| E05/E06 scale-out | **Supported by config alone.** Set `scale_out_r: 0.25` or `0.35`, plus **`live_scale_out: true`** (`runner._live_scale_out` / `scale_outs`). `scale_out_frac` defaults to 0.5, and the stop moves to BE after the partial. Lots under 2 shares are never scaled. All 4 CWT entries in `config/account_testing2.yaml` currently have `scale_out_r: null`. |
| E09 wait one bar | **Not supported.** `LabStrategy` always enters at the signal bar's close. It needs code: an `entry_delay_bars` param in `LabStrategy._signal`, mirrored in the backtester. |
| E10 flow3 filter | Supported as a **new research module** (mask & flow3 < 0) plus a new config entry. No mcf/ change. |
| Time stops (E01-E03) | Supported: `time_stop_min` / `time_stop_min_r` (`runner.manage`, minutes from the fill on 1-minute bars). None beat its parent. |
| Breakeven (E04) | Supported: `be_at_r`. Fails. |
| Trailing (H02-H04, H07) | `trail_r` / `trail_after_r` are supported in `runner.manage`. **But `LabStrategy` always sets a target from the module GEOM**, so "no target / runner" needs code: a target override (e.g. `target_r: null`) in `LabStrategy._signal`. The same applies to H01 and H06 hold-to-close. |
| Clock exit H08 (14:30) | **Not supported live.** The runner does not act on `Signal.exit_by`; only the 15:55 flatten runs. It needs code: a per-setup `exit_by` in `runner.manage`. A fixed-duration time stop (`time_stop_min` with a large `time_stop_min_r`) is not equivalent. |
| Smaller stop (E07/E08) | Needs a new GEOM (`LabStrategy.GEOMS` only has t1s1 / t05s1 / t1s05). Fails anyway. |

**Reference only, not proposed.** On this evidence, adding `scale_out_r: 0.35` with `live_scale_out: true` to
these setups would cut the per-trade loss by about 0.02R:
- pdh-p05-lowvol-short, orl-p10-long and orl-p10-lowvol-long
- coil-k4-long (+0.013R)

It would not make any of them profitable. 0.25R vs 0.35R is a near tie on exp: 0.25R is better on pdh and orl-p10
(by 0.0004..0.0026R), 0.35R on orl-p10-lowvol and coil (0.0011..0.0028R). 0.35R has the higher t_improve everywhere
because its paired difference is less noisy. Whether the CWT14 p05 setups live from 10-19 (0.25R) should move to
0.35R was not scored on them.

## Backlog
Tag `top5-tune`; `research/BACKLOG.md` was regenerated and now has 440 entries.
- `top5-1016-<setup>-exec` x 5: status **failed**.
- 9 beats-parent entries `top5-1016-<setup>-<var>-<knob>`: status **rework**. Each carries a `live_support` field.

## Next run (queued, not scored)
- **Pair round** (rule 18, pre-declared, counted in the lineage):
  - pdh-short: E06 + E09 (wait one bar).
  - pdh-short: E06 + E10 (flow3).
  - CWT14 p05 trio: scale_out 0.35 vs the 0.25 now live.
- **Rotation:** coil-k4 has now been tuned twice with no change. One more run rotates it out.
- **Shorts' hold-to-close:** only worth retesting together with a day-direction rule known at entry. That is the
  `bdi1016-dayclass-late-decision` idea, at 11:00/12:00.
