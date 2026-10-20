# top5_1020 pre-declaration: execution variants of the next 5 most-traded eligible live setups (fifth run)

*Educational only - not financial advice.*

Written 2026-10-20 after the close, after the live ranking (`live_rank.py`, live paper trades only) and **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards. Anything
added after scoring starts is appended below a dated line and counted.

Owner goal: more **quality executions** and better **conversion of win rate into R** on the most-traded setups.
Variants are not ranked by profit.

## 1. Which setups (live, rule 7: paper)
Source: `reports/<date>.csv` on `origin/mcf-data` (Primary), `origin/mcf-data-testing` (Testing 1),
`origin/mcf-data-testing2` (Testing 2); sessions 2026-10-14, 15, 16, 19, 20; run_id 1; S6 and GEN-* excluded;
"-FD" copies count as their own setup (`live_rank.csv`).

**Exclusions (lead's brief, 2026-10-20):**
- MF3 family (swarmed today, research/bdi/mf3swarm1020).
- Tuned in top5_1019: CWT14 pdl-p10 (136), pdl-p05-lowvol (115), pdh-p10 (110), LIQ-orl (83), RW2-FD (119).
- Moving to the Graveyard tonight: heat_fade_short-FD (212), L3-gap-slope-fromopen-FD (112), heat_fade_long-FD (98),
  LIQ-orl, RW2-FD, heat_fade_long, RW6-FD, NS2-FD, ST1-FD, L3-lowdist-FD, MF1-FD, ST2-FD.

**Chosen (top five remaining by live count):**

| rank (all) | setup | acct | live n | win | avg win / avg loss (R) | break-even win | avg R | tuned before |
|---|---|---|---|---|---|---|---|---|
| 1 | CWT14-failbrk-orl-p05-long | T2 | 235 | 59.1% | +0.416 / -0.993 | 70.5% | -0.160 | 10-14, 10-15 |
| 2 | CWT14-failbrk-orl-p05-lowvol-long | T2 | 217 | 53.9% | +0.406 / -1.035 | 71.8% | -0.258 | 10-14, 10-15 |
| 4 | CWT14-failbrk-pdl-p05-long | T2 | 187 | 61.0% | +0.492 / -0.998 | 67.0% | -0.090 | 10-15 |
| 6 | CWT14-failbrk-pdh-p05-lowvol-short | T2 | 122 | 60.7% | +0.445 / -0.981 | 68.8% | -0.116 | 10-16 |
| 7 | CWT14-failbrk-orl-p10-long | T2 | 121 | 58.7% | +0.456 / -1.056 | 69.9% | -0.169 | 10-16 |

All five got a live change since they were last tuned: `scale_out_r` (0.25 for the p05 trio, owner 10-16; 0.35 for
pdh-p05-lowvol and orl-p10, owner Q17 10-17) with `live_scale_out`. The scale-out did not execute at Alpaca until
the runner fix of 10-19 (cancel the bracket legs, sell half, re-protect at breakeven); the first live
`scaled+target` exits are on 10-20 (2 trades). So the 5-session live sample is almost all **without** scale-out.

Parents (live modules / config, t05s1 = target 0.5R, stop 1R, R = 0.25 x daily ATR, flat 15:55, min_adv 95M):
- orl-p05: `cwt_live_lib.b3(OR, p=0.05, long)`, [950,1500], scale-out half at +0.25R, rest to BE.
- orl-p05-lowvol: `b3(OR, p=0.05, lowvol, long)`, [950,1500], scale 0.25.
- pdl-p05: `b3(PD, p=0.05, long)`, [950,1500], scale 0.25.
- pdh-p05-lowvol-short: `b3(PD, p=0.05, lowvol, short)`, [950,1500], scale 0.35.
- orl-p10: `b3(OR, p=0.10, long)`, **[950,1200]**, scale 0.35.
**Parent P = the live config including the scale-out.** R0 (no scale-out, what actually ran 10-14..10-19) is a
counted row.

## 2. Data, costs, splits, simulation (harness = top5_1019/scan_1019.py)
- research/history2y frames via `lib.load_month`, open months only. The rule-19 locked block 2024-11-01..2025-02-28 is
  **never loaded** (`MCF_HIST_ALLOW_LOCKED` never set; asserted).
- 5-minute path simulator = `top5_1019/scan_1019.sim` unchanged (stop first, then target, then time stop / BE /
  scale-out; management from the next bar; flat 15:55). **Parity gate before any variant is scored:** R0 of all 5
  equals `gates.lab_trades` on 2025-06 (mean |diff| < 0.002R, >= 99% within 0.01R) and the 5 kernels equal
  `cwt_live_lib.b3`. Else stop and fix.
- Costs: entry 1c + 1 bps x time-of-day multiplier; target / scale-out limits free; stop / breakeven fills
  1c + 1 bps + 2c; market exits 1c + 1 bps.
- **Stop-distance variants are scored at the same $ risk**: target and scale-out prices stay where the parent has them
  (in units of the parent R), and R per trade is divided by the stop multiple (also reported unscaled).
- One trade per symbol-day (first qualifying bar), as live.
- Splits: TRAIN = open sessions <= 2025-12-31; VALID = 2026-01..03 and 2026-07-01..09-15; HOLD = Apr-Jun 2026 and
  2026-09-16..10-07, scored once only for a variant that meets the Testing bar on TRAIN+VALID.
- Random control: 5 random symbols at the same date and bar (adv20 >= 95M, seed 20261020), same mechanics, same risk
  in ATR units.
- Index move: SPY's `fromOpen` (%) at the signal bar.

## 3. Grid (one knob per row; every row counts)

| id | knob | value (p05 trio: scale 0.25 / pdh-p05-lowvol, orl-p10: scale 0.35) |
|---|---|---|
| R0 | no scale-out (pre-10-20 live behaviour) | plain t05s1 |
| E01 | time stop for never-worked trades | 30 min, exit if best < +0.2R |
| E02 | time stop | 60 min, best < +0.25R |
| E03 | tighter stop (same $ risk) | 0.85R |
| E04 | wider stop, target + scale price unchanged (same $ risk; queued by top5_1019) | 1.25R |
| E05 | wider stop (same $ risk) | 1.5R |
| E06 | scale-out trigger -0.10R | 0.15 / 0.25 |
| E07 | scale-out trigger +0.10R | 0.35 / 0.45 |
| E08 | entry timing: wait one bar (enter at the next bar's close) | yes |
| E09 | entry window start 10:00 | yes (OR setups signal from 10:05: equals P, still counted) |
| E10 | entry window start 10:30 | yes |
| E11 | entry window end 11:00 | yes |
| E12 | market context: after 10:30 skip entries against SPY's move from the open | yes |
| E13 | re-entry with cooldown: a 2nd trade per symbol-day on the next signal >= 30 min (6 bars) after the 1st exits | yes |
| T1 / T2 | poke threshold p -20% / +20% | p x 0.8 / x 1.2 |

**Counts:** 16 variants per setup x 5 = **N (study) = 80**; parents re-scored as 5 reference runs (not counted).
Study bar max(1.5, sqrt(2 ln 80)) = **2.96**. Setup bar max(1.5, sqrt(2 ln 16)) = 2.35. Lineage (CWT14 b3:
121,230 + 54 (top5_1019) + 80 = 121,364) bar 4.84, reported.
Not repeated (already scored on these families): limit entries, CWT14 SAR, skip-first-bar, day-class gates, breakeven
without scale-out, trailing, opposite-side reversal, VWAP / RSI / gap filters, exit geometry t1s1 / t1s05.

## 4. Bars (fixed now)
- **Beats parent** (backlog proposal, tag `top5-tune`): d exp > 0 on TRAIN **and** VALID, and day-block bootstrap t of
  the improvement on TRAIN+VALID (1,000 resamples, seed 20261020) >= setup bar 2.35. Lineage bar reported.
- **Testing candidate:** beats parent, and **VALID day-clustered t of the variant >= 2.96** (study bar), exp > 0 on
  TRAIN and VALID, up and down sessions each > 0, ex-best-day > 0, excess over random > 0; then HOLD once (exp > 0).
  Otherwise no Testing proposal.
- Execution readout for every row (not a gate): trades/day, win, avg win, avg loss, break-even win, margin,
  never-worked share, up / down exp, excess vs random.
- Every variant is reported (`results.csv`), failures first. Live support for each knob is stated in NOTES.
