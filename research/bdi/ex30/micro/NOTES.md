Educational only — not financial advice

# ex30 / micro — microstructure / bar-shape setups (results)

Pre-declared in `PLAN.md` (committed 7aa4fb891 before anything was scored). Scripts: `score.py` (harness, independent
pandas re-implementation of every rule), `report.py` (tables), modules in `modules/` (+ shared `micro_lib.py`).
Outputs: `results.csv`, `parity.csv`. **Configurations scored: 15** (5 primaries + 10 pre-declared neighbours), nothing else.
Locked block 2024-11-01..2025-02-28 never loaded (asserted). Costs in (production 1c + 1 bps per side, +2c on stops,
time-of-day entry multiplier). Backtest only (2-year lab frames); nothing here is a paper or live result.
Rule-change context: these are new setups scored on fixed historical frames; no ledger rule change applies to them.

## Failures first: 0 of 15 pass the light lane gate

| setup (primary) | side/geom | TRAIN avg R (t) | VALID avg R (t) | trades/session | vs random TRAIN / VALID | up / down / quiet (TRAIN+VALID) | gate |
|---|---|---|---|---|---|---|---|
| MC1-nr7-expansion-volburst-long | long t1s1 | -0.094 (-5.3) | -0.090 (-3.9) | 176.8 | -0.037 / -0.019 | +0.065 / -0.238 / -0.143 | fail (R, frequency) |
| MC2-dryup-surge-wickreject-short | short t1s1 | -0.141 (-5.9) | -0.079 (-3.4) | 28.3 | -0.038 / -0.023 | -0.304 / +0.037 / -0.058 | fail (R, frequency) |
| MC3-vwap-glued-stretch-long | long t05s1 | -0.258 (-1.9) | -0.260 (-1.5) | 0.35 | -0.110 / -0.202 | -0.292 / -0.333 / -0.033 | fail (R, too rare) |
| MC4-redrun-outside-reversal-long | long t05s1 | -0.066 (-4.5) | -0.092 (-4.4) | 74.4 | +0.030 (t 2.9) / -0.006 | +0.031 / -0.152 / -0.083 | fail (R, frequency) |
| MC5-firsthour-break-voldecay-short | short t1s1 | -0.104 (-4.0) | -0.052 (-1.7) | 226.5 | +0.025 (t 1.6) / +0.023 (t 1.0) | -0.286 / +0.161 / +0.033 | fail (R, frequency) |

Sessions: TRAIN 234, VALID 114. Neighbours (all in `results.csv`) sit on the same values (plateau), so none of the
failures is a threshold accident: NR5/NR10, surge 1.5/3.0, run 5/8, volumeRatio 0.6/1.0 all within ~0.01-0.02R of the
primary. MC3's neighbours: share 0.50 = -0.112 / -0.196 (2.0/session), share 0.70 = 11 trades in two years.
Avg R without the best day is lower than the full avg in every case (all totals negative; no one-big-day carry).

Parity (module vs harness, bar by bar, 2026-09 inside window + ADV): exact for all 5 (MC1 2,242, MC2 345, MC4 886,
MC5 2,981 bars). MC3's scored month (to 09-15) had 0 bars, so its parity is vacuous there; on the full 2026-09 month
(pre-run check) harness = module = 4 bars.

## What the bar-shape family says

1. **Bar shape alone does not beat costs.** Every primary is a near-random entry: vs-random excess -0.04..+0.03R on
   a base of about -0.08..-0.10R. Same finding as night1102/simple for 1-condition cores.
2. **They are still direction bets.** Longs (MC1, MC4) win only on SPY up days; shorts (MC2, MC5) win only on down days.
   None of the "range / quiet-day" designs is positive on quiet days in both splits except MC5 (+0.048 TRAIN, +0.006
   VALID quiet — near zero).
3. **The two that beat random:** MC5 (first-hour-high break on fading volume, short) beats the day-matched random
   short in TRAIN and VALID (+0.025 / +0.023, t 1.6 / 1.0) and is the least-bad on quiet days; MC4 (six red bars then an
   outside green bar, long) beats random in TRAIN (t 2.9) but not in VALID. Both are far too busy (74-226 trades/session
   at ADV 95M): as exploratory seats they would need a per-setup trade cap or a higher ADV floor, which is a new
   configuration and was not scored here.
4. **MC3 (time-at-VWAP balance) is too rare**: a name that straddles VWAP on >= 60% of its bars almost never gets
   0.30 ATR away from it. The pre-declared rule is reported as is.

Data-limit notes for the live runner: the frames carry no bar open, so colour is recovered from the wick columns
(exact); look-backs only use >= 09:50 bars so live (bars from 09:35) and offline (from 09:50) agree inside each window.
