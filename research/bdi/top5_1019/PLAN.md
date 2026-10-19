# top5_1019 pre-declaration: execution variants of the 5 most-traded eligible live setups (fourth run)

*Educational only - not financial advice.*

Written 2026-10-19 after the close, after the live ranking (`live_rank.py`, live paper trades only) and **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards. Anything
added after scoring starts is appended below a dated line and counted.

Owner goal: more **quality executions** and better **conversion of win rate into R** on the most-traded setups.
Variants are not ranked by profit.

## 1. Which setups (live, rule 7: paper)
Source: `reports/<date>.csv` on `origin/mcf-data` (Primary), `origin/mcf-data-testing` (Testing 1),
`origin/mcf-data-testing2` (Testing 2); sessions 2026-10-13, 14, 15, 16, 19; run_id 1; S6 and GEN-* excluded;
"-FD" copies count as their own setup. **Caveat:** the Testing 1 report for 10-19 is missing about 132 trades, so T1
counts on 10-19 are low (T1 setups may be ranked slightly low).

**Rotation** (owner rule: rotate out a setup tuned in the last 3 runs - top5_1014, top5_1015, top5_1016 - with no
change). Every setup tuned in those runs is out:
- CWT14 orl-p05 (314), orl-p05-lowvol (293), pdl-p05 (215): tuned 10-14 and 10-15; their scale-out change from 10-19
  (ledger 2026-10-16) does **not** execute at Alpaca (bracket leg qty cannot be changed), so they are effectively
  unchanged - flagged in NOTES, but a third execution grid on them would repeat 10-14/10-15.
- heat_fade_short-FD (269): 10-14, 10-15. orl-p10 (169), pdh-p05-lowvol-short (151), orl-p10-lowvol (140),
  RW7-FD (138), coil-k4 (128): 10-16 (coil also 10-15).

**Chosen (next five by live count, never tuned by this task):**

| rank (all) | setup | acct | live n | win | avg win / avg loss (R) | break-even win | avg R |
|---|---|---|---|---|---|---|---|
| 6 | CWT14-failbrk-pdl-p10-long | T2 | 164 | 62.2% | +0.388 / -1.023 | 72.5% | -0.146 |
| 8 | CWT14-failbrk-pdl-p05-lowvol-long | T2 | 142 | 61.3% | +0.445 / -0.934 | 67.7% | -0.089 |
| 11 | CWT14-failbrk-pdh-p10-short | T2 | 136 | 66.9% | +0.435 / -0.993 | 69.5% | -0.037 |
| 13 | LIQ-orl-sweep-open15-s25-long | T1 | 126 | 43.7% | +0.884 / -0.831 | 48.4% | -0.082 |
| 14 | RW2-exhaustion-noon-adv150-short-FD | T1 | 125 | 45.6% | +0.921 / -0.969 | 51.3% | -0.107 |

Parents (live modules / config):
- pdl-p10-long: `cwt_live_lib.b3(PD, p=0.10, long)`, t05s1, [950,1500], min_adv 95M.
- pdl-p05-lowvol-long: `b3(PD, p=0.05, lowvol, long)`, t05s1, [950,1500], 95M.
- pdh-p10-short: `b3(PD, p=0.10, short)`, t05s1, **[950,1200]**, 95M.
- LIQ-orl: `liq_live_lib.sweep(OR, long, x=0.15, trig=open, k=15)`; stop 0.05 ATR under the sweep low (skip if risk
  > 1 ATR), target 2.5x risk, flat 15:55; [950,1500], 95M. R = structural risk (entry - stop).
- RW2-FD: rsi5 > 90 & sma20_dist_pct > 1.0 & bear_div > 0; short t1s1; [950,1500]; min_adv 150M.

## 2. Data, costs, splits, simulation
- research/history2y frames via `lib.load_month`, open months only. The rule-19 locked block 2024-11-01..2025-02-28 is
  **never loaded** (`MCF_HIST_ALLOW_LOCKED` never set; asserted).
- 5-minute path simulator = `top5_1016/scan_1016.sim` (stop first, then target; management from the next bar; flat
  15:55), extended only with a per-trade risk unit (LIQ structural risk). **Parity gate before any variant is scored:**
  the 3 CWT14 and the RW2 parents equal `gates.lab_trades` on 2025-06 (mean |diff| < 0.002R, >= 99% within 0.01R);
  LIQ parent n is compared with `reddit1012liq/live/verify.json`. Else stop and fix.
- Costs: entry 1c + 1 bps x time-of-day multiplier; target / scale-out limits free; stop / breakeven fills
  1c + 1 bps + 2c; market exits 1c + 1 bps.
- **Stop-distance variants are scored at the same $ risk** (live sizing is by risk): their R is divided by the stop
  multiple (also reported unscaled).
- One trade per symbol-day (first qualifying bar), as live (0 repeats per symbol-day in the 5 live sessions).
- Splits: TRAIN = open sessions <= 2025-12-31; VALID = 2026-01..03 and 2026-07-01..09-15; HOLD = Apr-Jun 2026 and
  2026-09-16..10-07, scored once only for a variant that meets the Testing bar on TRAIN+VALID.
- Random control: 5 random symbols at the same date and bar (adv20 >= min_adv, seed 20261019), same mechanics, same
  risk in ATR units.
- Index move: SPY's `fromOpen` (%) at the signal bar, from SPY's own rows in the same frames.

## 3. Grid (one knob per row; every row counts)
t05 = the 3 CWT14 setups (target 0.5R); t1 = RW2 (1R); LIQ target 2.5R.

| id | knob | CWT14 (t05) | RW2 (t1) | LIQ |
|---|---|---|---|---|
| E01 | time stop for never-worked trades | 30 min, exit if best < +0.2R | same | same |
| E02 | time stop | 60 min, best < +0.25R | same | same |
| E03 | earlier/tighter stop (same $ risk) | 0.85R | 0.85R | 0.85R |
| E04 | tighter stop (same $ risk) | 0.75R | 0.75R | 0.75R |
| E05 | wider stop, target price unchanged (same $ risk; gb-1019-wide-stop-t05) | 1.25R | 1.25R | 1.25R |
| E06 | breakeven | at +0.35R | at +0.5R | at +1.0R |
| E07 | earlier partial exit (scale-out half, rest to BE) **live caveat: does not execute at Alpaca** | at +0.25R | at +0.5R | at +1.0R |
| E08 | entry timing: wait one bar (enter at the next bar's close) | yes | yes | yes |
| E09 | entry window start 10:00 | yes | yes | (signals start 10:05: not run) |
| E10 | entry window start 10:30 | yes | yes | yes |
| E11 | entry window end 11:00 | yes | yes | yes |
| E12 | index filter: after 10:30 skip entries against SPY's move from the open (long if SPY fo < 0; short if > 0) | yes | yes | yes |
| E13 | same, only when SPY is >= 0.25% against | yes | yes | yes |
| E14 | index filter all day (skip any entry against SPY fo) | yes | yes | yes |
| E15 | flow3 agrees with the side at the signal bar | yes | yes | yes |
| E16 | re-entry with cooldown: allow a 2nd trade per symbol-day on the next signal >= 30 min (6 bars) after the 1st exits (scored as parent + 2nd trades) | yes | yes | yes |
| T1 / T2 | signal thresholds -20% / +20% | poke p x0.8 / x1.2 | sma20 dist 0.8 / 1.2 | sweep x 0.12 / 0.18 |
| T3 / T4 | | - | rsi5 > 88 / > 92 | target 1.5R / 2.0R (live: 68 of 126 ride to 15:55) |

**Counts:** CWT14 x3: 16 + 2 = 18 each (54); RW2 16 + 4 = 20; LIQ 15 + 4 = 19 (E09 not run).
**N (study) = 93**; study bar sqrt(2 ln 93) = 3.01. Parents re-scored as 5 reference runs (not counted).
Not repeated (already scored on these families): limit entries, CWT14 SAR, skip-first-bar, day-class gates,
trailing / hold-to-close on longs, opposite-side reversal.

## 4. Bars (fixed now)
- **Beats parent** (backlog proposal, tag `top5-tune`): d exp > 0 on TRAIN **and** VALID, and day-block bootstrap t of
  the improvement on TRAIN+VALID (1,000 resamples, seed 20261019) >= max(1.5, sqrt(2 ln N_setup)) (18 -> 2.40,
  19 -> 2.43, 20 -> 2.45). Also reported against the lineage bar (CWT14 b3 121,230 + 54 -> 4.84; LIQ 7,718 + 19 ->
  4.23; RW2 exhaustion lineage 934,522 + 20 -> 5.24). Also reported: excess over the same-minute random control.
- **Testing candidate:** beats parent, and **VALID day-clustered t of the variant >= 3.01** (study bar), exp > 0 on
  TRAIN and VALID, up and down sessions each > 0, ex-best-day > 0, excess over random > 0; then HOLD once (exp > 0).
  Otherwise no Testing proposal.
- Execution readout for every row (not a gate): fill share, trades/day, win, avg win, avg loss, break-even win,
  margin, never-worked share, up / down exp.
- Every variant is reported (`results.csv`), failures first. Live-support for each knob is stated in NOTES.
