# BDI 2026-10-07: falling-knife management and trade frequency

*Educational only — not financial advice.* These are backtest results only. Nothing here has been tested live. No locked holdout was read: the data is `data/cache`, loaded with `end='2026-09-16'`, and `data/cache_q2` was not touched.

- **Train** is 2026-07-15..08-25 (30 sessions). **Valid** is 08-26..09-15 (14 sessions).
- The **2026-10-06 replay** uses the live day's 1-minute bars (`live_bars.parquet`, fetched for the autopsy; it covers 10-06 and 10-07 only). Signal price and R come from the live journal.
- **Costs** are production costs on every trade: `mcf.backtest.engine.simulate` with config/default.yaml costs (1 bps + 1c per share per side, +2c on stops, 3c on the extended tier). Entries fill at the next bar, the stop is assumed hit first inside a bar, and a gap through the stop fills at the open.
- **R unit = R0 = 0.25 × the prior-day daily ATR** at the original signal. Production sizing is bound by notional (a ~$2k slot), so every leg carries the same dollars and a 0.5R stop loses 0.5 R0.

**Configurations tried: 73** (plus 4 baselines):
- Task 1: 38.
- Task 2(b): 24 re-entry configurations, plus 8 portfolio combinations of them.
- Task 2(c): 3.

At p = 0.05, about 3–4 of these would look good by chance.

## Failures first
- **No configuration passes the gate.** The gate needs better total R and exp R on train, confirmed on valid, with a paired day-t of at least 1.0 on valid, and not carried by one day. **There are 0 finalists for the primary account.**
- **(a) Stop-and-reverse loses in both splits.** The reverse short opened after heat_fade_long's 1R stop made:

  | split | n | exp (R per trade, by target) |
  |---|---|---|
  | train | 129 | 1R target −0.14, 2R target −0.24, no target −0.23 |
  | valid | 38 | −0.13 to −0.16 |

  After the stop, these names on average bounce; they do not keep falling. 2026-10-06 was the exception, not the rule.
- **(b) A 0.5R first stop costs money.**
  - On its own it gives train +0.056 against base +0.109, and valid −0.060 against −0.022.
  - Re-entry on a higher low: the re-entry legs make +0.12R on train (n 226) and −0.08R on valid (n 58). Paired valid diff −9.3R, t −2.3.
  - VWAP-reclaim re-entries are rare (62 on train, 9 on valid).
- **(c) Wait-for-confirmation is flat on train and worse on valid.**
  - The prev-high trigger within 60 minutes: train +0.11R (paired diff +0.1R), valid −6.4R.
  - A VWAP reclaim within 60 minutes almost never happens: 34 train trades, 7 valid.
- **(d) Short continuation after N lower lows loses on train in every variant.** It was tried with N = 1–3 and with a t1, trail 0.5 or trail 1.0 exit.
  - N1 with trail 1.0 made −89R on train.
  - Valid is mixed and small: n 23–67.
- **(e) Capping the 11:05 cluster by score does not help.**
  - Keeping only the top-k by heat score lowers train expectancy. With k = 1 over all bars, train falls from +0.109 to +0.029. The highest-scored names are not the better ones.
  - On 10-06, the top-3 by score (GRML, TEM, TWST) were all losers.
- **Extra management ideas, added and counted.** None passes. All three show the same regime flip:
  - Per-setup daily circuit breaker after 2 or 3 stops.
  - Skip, or flip to short, when SPY is below VWAP.
  - Skip every signal in a bar where 3, 4 or 6 or more names fire together.

  The flip:
  - On train, heat_fade_long earns *only* on SPY-below-VWAP days (+64.7R) and in multi-name clusters (+70R on 243 trades).
  - On valid, both of those lose (−6.7R and −11.2R).
  - On 10-06, SPY and QQQ were above VWAP and the open at 11:04. This was a sector selloff (genomics / biotech), not a market dip.

  Read: heat_fade_long is a market-dip buy whose edge flipped between train and valid. Its valid base is −0.022R per trade, t −0.18. No management rule fixes a setup whose entry edge is ≈0.

## Task 1 numbers (heat_fade_long first signals; full table in `task1_results.csv`)
| variant | train n / win / exp / tot / t / ex-best | valid n / win / exp / tot / t / ex-best | paired diff valid (t) |
|---|---|---|---|
| base | 497 / .55 / +.109 / +54.1 / 1.32 / +25.8 | 116 / .50 / −.022 / −2.6 / −0.18 / −8.0 | — |
| a SAR, 1R target | 626 / .53 / +.058 / +36.3 / 1.01 / +14.6 | 154 / .47 / −.056 / −8.6 / −0.56 / −12.9 | −6.0 (−0.96) |
| a SAR, no target | 626 / .51 / +.040 / +24.8 / 0.78 / +12.3 | 154 / .45 / −.055 / −8.4 / −0.53 / −12.8 | −5.9 (−0.93) |
| b 0.5R stop + HL re-entry | 723 / .43 / +.077 / +55.6 / 1.13 / +22.2 | 174 / .35 / −.068 / −11.9 / −0.98 / −14.5 | −9.3 (−2.30) |
| c confirm prev-high, 60m | 454 / .56 / +.119 / +54.2 / 1.31 / +25.7 | 106 / .48 / −.085 / −9.0 / −0.61 / −15.6 | −6.4 (−0.92) |
| d cont. LL1, trail 0.5 | 337 / .49 / −.191 / −64.4 / −1.71 | 67 / .69 / +.097 / +6.5 / 0.54 / −4.3 | +9.1 (0.37) |
| e cap 1 per bar | 243 / .52 / +.029 / +7.1 / 0.40 | 81 / .56 / +.084 / +6.8 / 0.97 / +3.1 | +9.3 (0.98) |
| e2 skip clusters ≥ 3 | 254 / .47 / −.063 / −16.0 / −0.76 | 89 / .55 / +.097 / +8.6 / 1.00 / +3.2 | +11.2 (1.27) |
| f breaker after 2 stops | 366 / .50 / +.016 / +5.9 / 0.23 | 104 / .48 / −.059 / −6.2 / −0.41 | −3.6 (−1.69) |
| g skip if SPY below VWAP | 139 / .49 / −.076 / −10.6 / −0.66 | 47 / .55 / +.089 / +4.2 / 0.53 | +6.7 (0.54) |

**2026-10-06 replay of the six 11:05 entries** (GRML, TEM, CAI, TWLO, TWST, GH), in R0. The full table, which also covers DHR, KLAC and NET (also bought at 11:05), is in `task1_live_1006.csv`.

| variant | 10-06 result (six names) |
|---|---|
| base | −5.42 |
| a SAR, 1R target | −4.62 |
| a SAR, 2R target | −2.20 |
| a SAR, no target | −0.14 (TWST reverse +4.25, TEM +1.79, TWLO +1.41; CAI and GH reversed into a second stop) |
| b 0.5R stop | −3.08 |
| b + HL re-entry | −4.10 |
| c prev-high confirm, 30 min | +0.16 (skips 4 of 6) |
| c prev-high confirm, 60 min | −2.00 |
| d LL1, trail 1.0 | +2.53 (TEM +3.30), but this rule made −89R on train |
| e top-k by score | k = 3 keeps GRML/TEM/TWST for −2.39 |

The variants that "would have saved" 10-06 (SAR with no target, LL1 continuation) are the ones that lose most across Jul–Sep. That is the hindsight trap.

## Task 2 numbers
**(a) Funnel, 44 sessions, production engine.** The universe is about 1,199 names per day, and the in-play filter removes almost nothing.

| setup | eligible names/day | qualifying 5m bars/day | signals/day (1 per symbol-day) | filled | after allocator | exp R train (n, t) | exp R valid (n, t) |
|---|---|---|---|---|---|---|---|
| heat_fade_short | 371 | 38.4 | 15.0 | 15.0 | 15.0 | +.047 (520, 0.43) | +.180 (141, 1.47) |
| heat_fade_long | 191 | 56.4 | 13.9 | 13.9 | 13.5 | +.110 (484, 1.32) | −.059 (108, −0.43) |
| exhaustion_short | 393 | 15.4 | 9.1 | 9.1 | 8.7 | +.271 (333, 1.49) | +.149 (51, 0.90) |
| orb20_a | 13 | — | 10.1 | 7.1 (stop entry) | 7.0 | +.050 | +.051 |
| intraday_momentum | 4 | — | 2.8 | 2.8 | 2.6 | +.012 | +.029 |

- **Portfolio:** 46.9 trades a day after the allocator. The allocator (160 slots, 100 per setup, one position per symbol) drops only about 1 trade a day.
- **Live filters (journal, 2 days):** on 10-06, 30 of 72 signals were skipped (22 for spread above max, 4 not shortable/ETB, the rest spread as a share of the stop, or already holding the symbol). On 10-07, 6 of 22 were skipped. The backtest does not model the spread filter, so expect about 60–70% of backtest volume live, roughly 30 a day.
- **The binding constraint is the signal generators.** Slots are not the limit. Most "extra" qualifying bars fall while the first trade is still open.

**(b) Re-entry.** Up to 2 or 3 trades per symbol per setup per day, after the previous trade has closed, with a 15 or 30 minute cooldown. "Any" means any later qualifying bar; "fresh" means a new threshold cross. Full table in `task2_reentry.csv`.
- **Volume added is tiny:** 0.1–1.9 trades a day per setup. The windows are short (heat_fade_short runs 09:50–10:30), and most qualifying bars come while the trade is open.
- **heat_fade_short:** re-entry legs make −0.12 to −1.0R on train. **Fails.**
- **heat_fade_long:** the re-entry legs are strong on train: n2, cd15, "any" gives +0.40R (n 56, t 2.05). They do not hold on valid: −0.15R (n 12). With cd30 the legs are +0.51R on train (n 31) and +0.19R on valid (n 6), but the paired valid t is only 0.54. **Fails the gate.** This is a near-miss.
- **exhaustion_short:** re-entry legs make +0.43–0.55R on train (n 10–12). On valid there are 2 legs at about 0R. **Inconclusive.**
- **Portfolio of all setups, production allocator:**
  - Re-entry raises train from 179.5R to 205.1R.
  - Valid is flat to worse: 32.9 → 31.8 for n2/cd15, 34.7 for n2/cd30.
  - Volume changes only from 54 to 57 a day on train and from 31 to 33 on valid.

**(c) Volume ceiling.** Here every qualifying 5-minute bar is taken as its own trade, ignoring the one-signal rule and the one-position-per-symbol rule (`task2c_volume.csv`).

| setup | bars 2+ per day (train / valid) | bars 2+ exp R train (t) | bars 2+ exp R valid (t, ex-best) |
|---|---|---|---|
| heat_fade_short | 27.6 / 14.3 | −.142 (−0.82) | −.021 (−0.11) |
| heat_fade_long | 52.6 / 20.9 | +.304 (2.04) | −.091 (−0.95) |
| exhaustion_short | 8.3 / 2.1 | +.462 (1.55) | +.063 (0.29, −1.5) |

- Taking every bar lifts the live setups (plus orb20_a and intraday_momentum) to about 144 trades a day on train and about 69 on valid. Train is inside the owner's 80–200 range; valid falls short of it.
- On valid, the extra 522 trades average **−0.055R**. Total valid R falls from +31.9 to +3.0.
- **More trades from these setups would have lost money on valid.**

**Other sources of volume (existing evidence):**
- The primitives gap-down short at 13:00 (`P1-gap_V1`, ~23 a day) failed both holdouts, at −0.05R and −0.06R.
- The L3 gap-slope shorts, now on probation in the Testing account, add about 2–8 a day at roughly 0 to +0.05R on the holdouts. That is unproven.
- The escalation `x_*` finalists failed the holdouts.
- No setup with positive expectancy confirmed on a holdout exists that could add the 35–150 trades a day needed.

**Estimate:** a portfolio reaching 80–200 trades a day today would be mostly zero- or negative-expectancy volume. At the valid numbers, 100 trades a day at about +0.004R each is break-even before the live spread drag. The binding work is **finding new setups that hold out**, not loosening the caps.

## Near-misses for the Testing account (not finalists; none passes the gate)
1. **heat_fade_long re-entry, 2 per day, 30-minute cooldown, any qualifying bar.**
   - Re-entry legs: +0.51R on train (n 31, t 1.86) and +0.19R on valid (n 6). The paired valid t is 0.54.
   - Its plateau neighbour, the 15-minute cooldown, is negative on valid.
   - It needs code: `HeatStrategy.generate` returns only the first hit, and `Strategy.max_signals_per_day = 1`. The proposed keys are `max_entries_per_day: 2` and `reentry_cooldown_min: 30`.
   - It adds about 1 trade a day.
2. **exhaustion_short scale-in on later qualifying bars,** meaning a second position in the same symbol.
   - Bars 2+: +0.46R on train (n 248, t 1.55) and +0.06R on valid (n 30, t 0.29, ex-best −1.5).
   - It needs the allocator to allow 2 positions per symbol for this setup.
   - It adds about 2–8 trades a day.

## Files
- `collect.py` (2 parts, ~20 minutes) writes `data/hits_*.pkl`, which is gitignored. It holds every qualifying bar of each live setup and the bars of each symbol-day that has a hit.
- `lib.py` holds the shared simulation and statistics code.
- `task1_knife.py` produces `task1_results.csv`, `task1_live_1006.csv` and `task1_output.txt`.
- `task2_freq.py` produces `task2_funnel.csv`, `task2_reentry.csv`, `task2_portfolio.csv` and `task2_output.txt`.
- `task2c_volume.py` produces `task2c_volume.csv`.
