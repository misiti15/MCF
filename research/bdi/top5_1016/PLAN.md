# top5_1016 pre-declaration: execution variants of the next 5 most-traded live setups (third run)

*Educational only - not financial advice.*

Written 2026-10-16 after the close, after the live ranking (`live_rank.py`, live paper trades only) and **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards. Anything
added after scoring starts is appended below a dated line and counted.

Owner goal: better **execution** of the most-traded setups (more quality executions, better conversion of win rate
into R) for data collection. Variants are not ranked by profit.

## 1. Which setups (live, rule 7: paper)
Real trades (run_id 1) on 2026-10-12, 13, 14, 15, 16 across Primary (`origin/mcf-data`), Testing 1
(`origin/mcf-data-testing`), Testing 2 (`origin/mcf-data-testing2`); S6 excluded; "-FD" copies are their own setup
(`live_rank.csv`).

**Rotation (owner rule: rotate out a setup tuned in the last 3 runs with no change, and setups that just got a change):**
- Out: CWT14-failbrk-orl-p05-long (301), CWT14-failbrk-orl-p05-lowvol-long (294), CWT14-failbrk-pdl-p05-long (192):
  they got a change (ledger `2026-10-16-live-scale-out`, `scale_out_r 0.25` + `live_scale_out` from 10-19).
- Out: heat_fade_short-FD (240): tuned 10-14 and 10-15, no change.
- Eligible next five by live count (no Primary-promoted FD setup is in range: MF3-open-flowsell-rsi5hi-FD has 43):

| rank (all) | setup | acct | live n | win | avg win / avg loss (R) | break-even win | avg R | tuned before |
|---|---|---|---|---|---|---|---|---|
| 5 | CWT14-failbrk-pdh-p05-lowvol-short | T2 | 169 | 61.5% | +0.488 / -0.978 | 66.7% | -0.076 | never |
| 6 | CWT14-failbrk-orl-p10-long | T2 | 165 | 59.4% | +0.444 / -1.030 | 69.9% | -0.155 | never |
| 7 | CWT12-coil-k4-long | T2 | 165 | 63.0% | +0.462 / -1.007 | 68.6% | -0.081 | once (10-15, thresholds + exec) |
| 8 | CWT14-failbrk-orl-p10-lowvol-long | T2 | 157 | 61.8% | +0.428 / -1.051 | 71.0% | -0.137 | never |
| 9 | RW7-gapdn-bounce-early-short-FD | T1 | 156 | 53.2% | +0.672 / -0.670 | 49.9% | +0.044 | once (10-14, thresholds/window/geometry/VWAP) |

Live shape: the 4 CWT setups lose because the full -1R stop is twice the +0.5R target (break-even 67-71% vs 59-63%);
28-30 losers per setup never reached +0.2R. RW7 converts better (53% vs 50% break-even), but 71 of 156 ride to 15:55
and 15 of 73 losers had reached +0.5R first. pdh short live: 09:50 entries +0.19R (28), 10:00-11:30 -0.12..-0.15R.

Parents (from their live modules / config):
- pdh-p05-lowvol-short: `cwt_live_lib.b3(PD, p=0.05, lowvol, short)`, t05s1, [950,1500], min_adv 95M.
- orl-p10-long: `b3(OR, p=0.10, long)`, t05s1, **[950,1200]**, 95M. orl-p10-lowvol-long: lowvol, [950,1500].
- CWT12-coil-k4-long: `cwt_live_lib.b4a(nco=4)`, t05s1, [950,1130], 95M.
- RW7-FD: heat <= -20 & buyPressure < -0.15 & 55 <= RSI14 <= 65 & gap < 0, short t1s1, [950,1500], 95M.

## 2. Data, costs, splits, simulation (as top5_1015)
- research/history2y frames via `lib.load_month`, open months only. The rule-19 locked block 2024-11-01..2025-02-28 is
  **never loaded** (`MCF_HIST_ALLOW_LOCKED` never set; asserted).
- 5-minute path simulator from `top5_1015/scan_1015.py` (stop first, then target; management from the next bar;
  flat 15:55), extended with: no target (hold to 15:55), trailing stop (`trail_r` behind the best excursion once
  `trail_after_r` is reached, engine order: time stop, breakeven, trail, scale-out), a clock exit, and a short-side
  b3 kernel (prices negated into the long kernel). **Parity gate before any variant is scored:** parent R equals
  `gates.lab_trades` on 2025-06 for all 5 (mean |diff| < 0.002R, >= 99% within 0.01R), and the short kernel equals
  `cwt_live_lib.b3(side='short')`; else stop and fix.
- Costs as `gates.prod_r` + time-of-day: entry 1c + 1 bps x tod mult; target / scale-out limits free; stop /
  breakeven / trail fills 1c + 1 bps + 2c; market exits 1c + 1 bps. R = 0.25 x daily ATR.
- One trade per symbol-day (first qualifying bar), as live (refire off for these setups).
- Splits: TRAIN = open sessions <= 2025-12-31; VALID = 2026-01..03 and 2026-07-01..09-15; HOLD = Apr-Jun 2026 and
  2026-09-16..10-07, scored once only for variants that meet the Testing bar on TRAIN+VALID.
- Random control: 5 random symbols at the same date and bar (adv20 >= min_adv, seed 20261016), same mechanics.
- Regimes `lib.regimes()` (up / flat / down sessions); walk-forward `gates.walk_forward`.
- Not repeated: refire / re-entry cooldown (refire1014 scored cd1/3/6 on every live lab setup), CWT14 SAR (bdi1014),
  skip-first-bar (nightly1014), index confirm (nightly1012), day-class gates (bdi1016), limit entries (X10/X11 failed
  on 5 setups 10-15), coil thresholds (10-15), RW7 thresholds/window/geometry/VWAP (10-14).

## 3. Grid (one knob per row; every row counts)
**E: execution knobs.** t05s1 parents = pdh short, orl-p10, orl-p10-lowvol, coil; RW7 is t1s1.

| id | knob | t05s1 parents | RW7 (t1s1) | applies to |
|---|---|---|---|---|
| E01 | time stop | 30 min, exit if best < +0.2R | same | all |
| E02 | time stop | 60 min, best < +0.25R | same | all |
| E03 | time stop | 90 min, best < +0.3R | same | all |
| E04 | breakeven | at +0.35R | at +0.5R | all |
| E05 | scale-out | half at +0.25R, rest to BE | half at +0.25R | all |
| E06 | scale-out | half at +0.35R, rest to BE | half at +0.5R | all |
| E07 | smaller stop | 0.85R | 0.85R | all |
| E08 | smaller stop | 0.75R | 0.75R | all |
| E09 | wait one bar | enter at the next bar's close | same | all |
| E10 | extra filter | flow3 agrees with the side at the signal bar | same | all |
| E11 | loser cluster | window start 10:30 (live 10:00-10:30 cluster) | - | 4 CWT |
| E12 / E13 | poke depth p -20% / +20% | p05 -> 0.04 / 0.06; p10 -> 0.08 / 0.12 | - | 3 CWT14 |

**H: hold winners longer (SHORT setups only, both regimes reported).** pdh-short (target 0.5R) and RW7 (target 1R).
| id | knob |
|---|---|
| H01 | no target: hold to 15:55, stop 1R |
| H02 | no target, trail 0.5R once +0.5R |
| H03 | no target, trail 1.0R once +1.0R |
| H04 | no target, trail 0.75R once +0.5R |
| H05 | target doubled (pdh 1.0R; RW7 2.0R) |
| H06 | half off at the parent target, rest to BE and hold to 15:55 |
| H07 | half off at the parent target, rest trails 0.5R |
| H08 (RW7 only) | flat at 14:30 (bdi1016 `rw7-late-exit` idea) |

**O: loser pattern as opportunity (all 5).** O1 one re-entry after a parent stop: the first bar within 60 min
(12 bars) of the stop bar whose close is back beyond the original entry price (short: below), inside the window;
same geometry. (bdi1016 queued it for pdh shorts: "stopped_then_reversed" on 5 days.)

**Counts:** pdh short 13 + 7 + 1 = 21; orl-p10 14; orl-p10-lowvol 14; coil 11 + 1 = 12; RW7 10 + 8 + 1 = 19.
**N (study) = 80**; study bar sqrt(2 ln 80) = 2.96. Parents re-scored as 5 reference runs (not counted).

## 4. Bars (fixed now)
- **Beats parent** (backlog, tag `top5-tune`): d exp > 0 on TRAIN and VALID, and day-block bootstrap t of the
  improvement on TRAIN+VALID (1,000 resamples, seed 20261016) >= max(1.5, sqrt(2 ln N_setup)) (21 -> 2.47, 14 -> 2.30,
  12 -> 2.23, 19 -> 2.43). Also reported against the lineage bar. O1 (a different trade): exp > 0 on TRAIN and VALID
  with t >= the setup bar.
- **Testing bar** (experimental; same account as parent): beats parent; exp > 0 on TRAIN and VALID; day-clustered
  t >= max(2.0, 2.96) = 2.96; up and down sessions each exp > 0 (n >= 30); walk-forward share >= 0.6; ex-best-day > 0;
  excess over random > 0; plateau: a neighbouring value of the same knob family has exp > 0 on TRAIN+VALID. Then
  HOLD once (exp > 0). Passing both = proposed Testing addition `<parent>-<knob tag>`.
- **Research bar** (`gates.verdict == keep`) at lineage N: CWT14 cwt-b-b3 121,181 + 49 = 121,230 (t >= 4.84);
  coil 184 + 12 = 196 (t >= 3.25); RW7 82,980 + 19 = 82,999 (t >= 4.76).
- **Live-support check** for every exit/entry knob (mcf/execution/runner.py, mcf/strategies/setups.py), stated in
  NOTES next to any proposal.
- Execution readout for every row (not a gate): win, avg win, avg loss, break-even win, margin, never-worked share,
  and for H rows up / flat / down session exp.
- Every variant is reported (`results.csv`), failures first.
