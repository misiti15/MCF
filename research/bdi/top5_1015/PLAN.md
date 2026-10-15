# top5_1015 pre-declaration: execution-quality variants of the 5 most-traded live setups

*Educational only - not financial advice.*

Written 2026-10-15 after the close, after the live ranking (`live_top5.py`, live paper trades only) and **before any
history configuration below was scored**. Results go in `NOTES.md`; this file is not changed afterwards. Anything
added after scoring starts is appended below a dated line and counted.

Owner goal (2026-10-14): better **execution** of the most-traded setups - more quality executions and a better
conversion of win rate into profit. Variants are **not** ranked by profit; win rate is treated as the base to build
on. So the grid is mostly exit/entry mechanics that production already supports as config keys
(`time_stop_min`/`time_stop_min_r`, `be_at_r`, `scale_out_r`/`scale_out_frac`, the exit geometry), plus a few entry-
timing and loser-pattern tests.

## 1. Which setups (step 1, live, rule 7: paper)
Real trades (run_id 1) on 2026-10-09, 12, 13, 14, 15 across Primary (`origin/mcf-data`), Testing 1
(`origin/mcf-data-testing`) and Testing 2 (`origin/mcf-data-testing2`); S6 excluded; a "-FD" copy is its own setup
(`live_rank.csv`).

| rank | setup | acct | live n | win | avg win / avg loss (R) | break-even win | tuned before |
|---|---|---|---|---|---|---|---|
| 1 | CWT14-failbrk-orl-p05-long | T2 | 241 | 58.9% | +0.432 / -0.895 | 67.5% | top5_1014 (once) |
| 2 | CWT14-failbrk-orl-p05-lowvol-long | T2 | 230 | 55.7% | +0.405 / -0.989 | 70.9% | top5_1014 (once) |
| 3 | heat_fade_short-FD | T1 | 205 | 38.5% | +0.767 / -0.863 | 53.0% | top5_1014 (once) |
| 4 | CWT14-failbrk-pdl-p05-long | T2 | 176 | 58.0% | +0.505 / -0.955 | 65.4% | top5_1014 (once) |
| 5 | CWT12-coil-k4-long | T2 | 143 | 68.5% | +0.466 / -1.001 | 68.2% | new |

RW7-gapdn-bounce-early-short-FD dropped to 7th (134). The four repeats were tuned only once (no 3-run rotation is
due), so they stay, but **with none of yesterday's knobs** (yesterday: thresholds p/reclaim/volumeRatio/SHORT_AT,
window, plain exit geometry t1s1/t1s05/t05s1, VWAP side, RSI, fromOpen, gap, min_adv).

Live shape that the grid targets: in every setup the winners rarely went worse than -0.75R (CWT14 4-8 of 98-142
winners, heat 4 of 79, coil 6 of 98), while losers took the full -0.9..-1.0R; 29-49 losers per setup never reached
+0.2R; the CWT setups need 65-71% wins at their win/loss sizes and get 56-69%.

Parents (unchanged from their live modules):
- CWT14 ORL / ORL-lowvol / PDL: `cwt_live_lib.b3(level, p=0.05, lowvol, long)`, t05s1, window [950,1500], min_adv 95M.
- heat_fade_short-FD: regime_9 heat score <= -11.3, gate fo-, k_cost 8, short, t1s1, [950,1500], min_adv 125M.
- CWT12-coil-k4-long: `cwt_live_lib.b4a(nco=4)` (HOD touched >= 3 times within 0.1 ATR; last 4 bars each narrower
  than 0.5 x mean range of up to 20 earlier bars, closing within 0.25 ATR under HOD), t05s1, [950,1130], 95M.

## 2. Data, costs, splits, simulation
- research/history2y frames via `lib.load_month` (open months only). The rule-19 locked block 2024-11-01..2025-02-28
  is **never loaded** (the loader refuses it; `MCF_HIST_ALLOW_LOCKED` is never set; head/tail rows are read per open
  month only).
- Path: 5-minute frame bars 09:50-15:00 plus the 15:05-15:55 tail rows (`refire1014/scan.tail_rows`); CWT signals
  use the 09:35-09:45 head rows as in the parity-verified scans.
- New path simulator (`scan_1015.py`, numba) mirroring `mcf/backtest/engine.py`: stop checked first in a bar, then
  target; management (time stop, breakeven, scale-out) acts from the next bar; time-stop exits at the bar close;
  flat at the 15:55 close. **Parity gate before any variant is scored:** the simulator's parent R must equal
  `gates.lab_trades` (production R) on one open month for all 5 parents (mean |diff| < 0.002R, >= 99% of trades
  within 0.01R); if not, stop and fix.
- Costs (production + time-of-day, as `gates.prod_r`): entry 1c + 1 bps x tod multiplier; target and scale-out
  limit fills free; stop and breakeven fills 1c + 1 bps + 2c; market exits (time stop, time exit, flatten) 1c + 1 bps.
  A limit entry pays the same entry cost as a market entry (conservative). R = 0.25 x daily ATR as live.
- One trade per symbol-day: the first bar in the window where the (variant) mask is true. A limit or confirmation
  entry that does not fill/confirm means no trade that day (the setup does not re-arm).
- **Splits (by date):** TRAIN = open sessions <= 2025-12-31; VALID = 2026-01-01..03-31 and 2026-07-01..09-15;
  **HOLD** = rule-2 holdouts Apr-Jun 2026 and 2026-09-16..10-07: not used for selection; scored once, only for
  variants that meet the Testing bar on TRAIN+VALID.
- **Random control (rule 6):** for each trade, 5 random other symbols at the same date and bar (adv20 >= the
  setup's min_adv, seed 20261015) run through the **same** entry and exit mechanics; excess = R - control mean.
- Regimes `lib.regimes()`; walk-forward `gates.walk_forward` over TRAIN+VALID.
- Not repeated (already scored): re-entry cooldown / refire (refire1014), CWT14 stop-and-reverse (bdi1014 B/B2),
  skip-first-bar (nightly1014), index confirm (nightly1012), and everything in top5_1014.

## 3. Grid (one knob per variant; every row counts)
**Execution knobs, each of the 5 setups** (t05s1 parents = the 3 CWT14 + coil; heat is t1s1)

| id | knob | t05s1 parents | heat_fade_short-FD (t1s1) |
|---|---|---|---|
| X01 | time stop | 15 min, exit if best < +0.2R | same |
| X02 | time stop | 30 min, best < +0.2R | same |
| X03 | time stop | 60 min, best < +0.25R | same |
| X04 | breakeven | stop -> entry at +0.25R | at +0.5R |
| X05 | breakeven | at +0.35R | at +0.75R |
| X06 | scale-out | half at +0.25R, rest stop -> entry, target 0.5R | half at +0.5R, rest BE, target 1R |
| X07 | scale-out | half at +0.5R, rest BE, target 1.0R | half at +0.3R, rest BE, target 1R |
| X08 | tighter stop | 0.75R (target unchanged) | 0.75R |
| X09 | tighter stop | 0.6R | 0.6R |
| X10 | limit entry | 0.1R better than the signal close, good 3 bars | same |
| X11 | limit entry | 0.2R better, good 3 bars | same |
| X12 | wait one bar | enter at the next bar's close | same |
| X13 | wait one bar + confirm | next bar closes in the trade's direction, else skip | same |
| X14 | one extra filter | flow3 > 0 at the signal bar (buyers) | flow3 < 0 (sellers) |
| X15 | time exit (heat only) | - | exit at 15:00 (77 of 205 live trades ride to 15:55) |
| X16 | time exit (heat only) | - | exit at 14:00 |

**Thresholds +-10-25% (coil only; the CWT14 and heat thresholds were done yesterday)**
| id | knob | value (parent) |
|---|---|---|
| T01 / T02 | coil bars nco | 3 / 5 (4) |
| T03 / T04 | tightness vs mean range | 0.4 / 0.6 (0.5) |
| T05 / T06 | close within x ATR under HOD | 0.2 / 0.3 (0.25) |

**Loser patterns as opportunities**
| id | setups | test |
|---|---|---|
| O1 | all 5 | opposite direction for signals before 10:30 (the live loser cluster): the mirror trade (target = parent stop distance, stop = parent target distance) |
| O2 | all 5 | next-day rebound: symbols the parent stopped out on, long at the next session's 09:50 close with the parent's geometry (t05s1; heat: long t1s1). Next session within the same month only (no cross-month load) |
| O3 | heat only | same-day reverse after the stop: long at the close of the stop bar, t1s1, flat 15:55 (CWT14 SAR already failed in bdi1014) |

**Counts:** CWT14 x3: 14 + 2 = 16 each (48); heat 16 + 3 = 19; coil 14 + 6 + 2 = 22. **N (study) = 89**; study bar
sqrt(2 ln 89) = 3.00. Parents re-scored as 5 reference runs (not counted).

## 4. Bars (fixed now)
- **Beats parent** (backlog entry, tag `top5-tune`): exp(variant) - exp(parent) > 0 on TRAIN and on VALID, and the
  improvement's day-block bootstrap t on TRAIN+VALID (1,000 resamples, seed 20261015) >= max(1.5, sqrt(2 ln N_setup))
  (16 -> 2.35, 19 -> 2.43, 22 -> 2.49). Also reported for every row: the same t against the **lineage** bar.
  For opportunity rows (O1-O3, a different trade) "beats parent" means exp > 0 on TRAIN and VALID with t >= the
  setup bar, since there is no paired parent trade.
- **Testing bar** (experimental only, same account as the parent): beats parent; exp > 0 on TRAIN and on VALID;
  day-clustered t >= max(2.0, 3.00) = 3.00; up and down sessions each exp > 0 (n >= 30); walk-forward share >= 0.6;
  ex-best-day > 0; excess over the same-mechanics random control > 0; plateau: the other value of the same knob also
  has exp > 0 on TRAIN+VALID (X14, X13, O-rows: +-50% neighbour scored only if needed, counted). Then HOLD once
  (exp > 0). Passing both = proposed Testing addition named `<parent>-<knob tag>`, never a Primary change.
- **Research bar:** `gates.verdict == keep` at the lineage N: CWT14 cwt-b-b3 121,133 + 48 = 121,181 (t >= 4.84);
  heat_fade_short 19,721 + 19 = 19,740 (t >= 4.45); CWT12 coil cwt-b-b4: 162 (its package-B lineage bar 3.19 =
  sqrt(2 ln 162)) + 22 = 184 (t >= 3.23).
- **Execution-quality readout (not a gate, not a rank):** for every row also win rate, avg win, avg loss, the
  break-even win rate and the margin (win - break-even), trades per day, and the share of losers that never reached
  +0.2R. A variant can raise the win-rate margin and still fail the bars; it is reported, not proposed.
- Every variant is reported (`results.csv`), failures first.
