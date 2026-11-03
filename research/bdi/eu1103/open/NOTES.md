Educational only — not financial advice

# eu1103 / open — earlier starts (09:40 / 09:45) and the 09:50-09:55 reversal (owner Q2b, 2026-11-03)

Research only: nothing in `config/`, setups, exits or the live path was changed. Costs are always in. The locked block
2024-11-01..2025-02-28 was never loaded: the 1-minute cache was read with a pyarrow filter that drops it at read time,
and the lab frames were read only through `lib.load_month` (asserted). Pre-declaration: `PLAN.md`, written before
any two-year scoring.
**Configurations scored: 16, all pre-declared** (Part 2: 8, Part 3: 8). There was also 1 descriptive look after the
fact, reported below and counted as a 17th look. **No pre-declared config passed its bar in a way that matters.**
RW7 at 09:40 / 09:45 meets the letter of the Part 2 bar, but only on 35 / 25 trades in two years (see Part 2).

## Failures first

1. **Starting at 09:40 or 09:45 makes every busy live setup worse, or leaves it unchanged.**

   Two-year TRAIN and VALID, total R per session against the 09:50 start:

   | Setup | 09:40 TRAIN | 09:40 VALID | 09:45 TRAIN | 09:45 VALID | 09:50 TRAIN | 09:50 VALID |
   |---|---|---|---|---|---|---|
   | CWT14-failbrk-pdl-p05-long | −15.6 | −21.9 | −13.1 | −18.2 | −12.0 | −16.4 |
   | CWT14-failbrk-pdh-p10-short | −11.0 | −9.0 | −8.7 | −7.6 | −7.0 | −5.2 |
   | L3-gap-slope-fromopen-FD | −0.10 | −0.69 | −0.12 | −0.66 | −0.01 | −0.63 |

   The trades that the earlier start adds or moves earlier are worse than the trades they replace:

   | Setup | Trades entered at 09:40-09:49, avg R TRAIN / VALID | What those same symbol-days earned at 09:50+ |
   |---|---|---|
   | CWT14-pdh-p10-short | −0.145 / −0.096 | |
   | CWT14-pdl-p05-long | −0.108 / −0.134 | |
   | L3 (moved trades) | −0.38 / −0.15 | −0.06 / +0.06 |

   The higher cost of an earlier entry explains only about 0.02-0.03R of this. That is the 2.1x vs 1.4x entry cost
   multiplier (`drift_out.txt`, `extra_cost_vs_0950`). The rest is signal quality: the first 10-20 minutes produce
   more false stop-runs and false stretches.
   - **L3 is Primary's best live setup** (+0.255R live, 10-20..11-03). An earlier start would make its entries 0.3R
     worse on the trades it moves.
   - The OR-based setups cannot fire before 10:05 by construction, so a 09:40 start changes nothing for them
     (CWT14-orl needs the 09:30-10:00 range; CWT12-coil needs 10 bars).

2. **RW7-gapdn-bounce-early-short-FD is the only setup that "passes" the Part 2 bar, and the pass is noise.**
   - Total R per session is a little better (+0.02 / +0.07R) and the early trades are positive (+0.05 / +0.45R).
   - But that is on 20 + 15 trades (09:40) or 14 + 11 trades (09:45) in two years, about 0.07 per session.
   - Day-t: TRAIN 0.09, VALID 1.12. The best day is 134% of TRAIN's total R.
   - RW7 rarely fires before 09:50 at all, because its heat and buyPressure need volume history.
   - My bar had no minimum trade count, so this meets it on paper. It is not evidence and nothing should change.

3. **The 09:50-09:55 dip / spike reversal fails in every form tested (O1-O8).** All 8 configs are negative on TRAIN
   AND VALID after costs.

   | Config | n | TRAIN avg R | VALID avg R | Pooled day-t | Up / down / quiet days, pooled |
   |---|---|---|---|---|---|
   | O1 dip in an up morning → long (primary) | 4,849 | −0.088 | −0.041 | −2.50 | +0.08 / −0.24 / −0.01 |
   | O3 spike in a down morning → short (primary) | 4,679 | −0.217 | −0.153 | −3.87 | −0.39 / +0.01 / −0.11 |
   | O2 / O4 (k 0.35, bigger move) | 583 / 453 | −0.226 / −0.307 | +0.013 / −0.177 | | |
   | O5 capitulation long | 5,368 | −0.101 | −0.196 | | |
   | O6 blow-off short | 5,083 | −0.199 | −0.123 | | |
   | O7 = O1 + SPY above its open | 2,408 | −0.094 | −0.000 | −1.27 | |
   | O8 = O3 + SPY below its open | 2,355 | −0.188 | −0.154 | | |

   - None beats the same-time control on both splits. O1's best is +0.052 TRAIN but −0.011 VALID.
   - None beats the day-matched random entry by more than 0.07R.
   - The market filter in O7 / O8 lifts O1 only on VALID, to about zero, and makes O3 worse.
   - **By day type it is the familiar direction bet:** the long wins only on up days and the short only on down days.
     Not even that holds reliably: O3 on VALID down days is −0.16R.
   - Full table: `reversal_results.csv` and `reversal_out.txt`.

4. **The descriptive look (not a config, 17th look):** the strongest *up* bars at 09:50-09:55 (b ≥ +0.35 ATR) were
   followed by continuation for longs (+0.07 / +0.03R pooled), not a reversal. Split by period it does not hold:
   TRAIN +0.106R (n 709, day-t −1.75, best day 160% of total R), VALID −0.067R (n 346). Not a lead.

## Part 1 — can the live runner react at 09:40? (feasibility, live data plus Alpaca quotes)

**Latency** (`latency.py`, `latency_out.txt`): 12,270 live fills, run_id 1, 5 accounts, 10-06..11-03.
- The runner polls every 60 s, at second :03 of each minute (`PaperRunner.run`). It fetches 1-minute SIP bars from
  09:30 and drops the minute still forming.
- **The signal comes a median 72 s after the 5-minute bar close** (p10 34 s, p90 147 s). By account:
  - Primary: 43 s
  - Testing 1: 65 s
  - Graveyard: 61 s
  - Gen: 93 s
  - Testing 2: 95 s

  The more setups and symbols an account has, the later its signals come.
- After GX1 (5-minute clock gate, effective 10-27) the median for lab setups fell from 76 s to 60 s, and from 72 s to
  43 s for entries at 09:50-09:59.
- **Signal to fill: a median 1.3 s** (p90 3 s).
- So a 09:40 decision bar would be acted on at about 09:40:45-09:41:15 in Primary and about 09:41:35 in Testing 2.
- In the first 1-2 minutes after a 09:40 / 09:45 close, price moves a median **0.16R** (mean 0.21R). From 09:50 on it
  is 0.09-0.11R. The *signed* move against our side is small: −0.005 to −0.014R for CWT14 at 09:40 / 09:45, t up to
  −5.7 (`drift_out.txt`).
- Night1102 measured that a live fill is 0.041R worse than the next 1-minute open, on all times of day.
- **Reacting at 09:40 is technically possible**, but it brings about 60% more entry-price noise than at 09:50.

**Spreads** (`quotes.py`, `quotes_out.txt`): Alpaca historical SIP NBBO for the 60 most-traded live names,
8 sessions 10-22..11-02, a 5-second window at each mark.

| Mark | Median spread (bps) | Ratio to the same name's midday spread, median / mean | Share wider than 25% of the stop |
|---|---|---|---|
| 09:35 | 12.3 | 1.93 / 2.38 | 9.9% |
| 09:40 | 11.1 | 1.58 / 2.09 | 7.1% |
| 09:45 | 11.3 | 1.55 / 2.02 | 6.0% |
| 09:50 | 9.3 | 1.12 / 1.71 | 2.9% |
| 10:30 | 7.1 | 1.00 / 1.22 | 0.2% |
| 12:00 | 5.6 | — | 0.4% |

- **The backtest's entry cost multiplier holds up on the mean.** 2.1x for 09:35-09:49 matches the mean of 2.0-2.1;
  1.4x for 09:50-10:29 matches 1.6-1.7 at 09:50-10:00. It is slightly generous at 09:50-10:00.
- **The live spread cap (25% of the stop) would skip about 2x as many 09:40 signals as 09:50 ones.**
- From the live journals: the spread share of skips is 72% at 09:50-54 vs 11% at noon, and the median spread is
  0.083R at 09:50 vs 0.061R at noon.
- **Spread is not the blocker. Signal quality is.**

**Warm-up:** the live runner prepends 60 prior 5-minute bars (`PRIOR5_BARS`), so RSI14, EMA26, SMA20 / 50 and the
20-bar volume averages are warm at 09:35. The day-anchored features are thin at 09:40, because only 2 bars exist:
VWAP, fromOpen, hod / lod, and volumeRatio (open volume against the prior afternoon). The lab computes them the same
way, so the backtest is consistent. The CWT library blanks volumeRatio before 09:50 on purpose.

**What a 09:40 start would need (live-path change, not done):** `live.no_entry_before` 09:50 → 09:40, and the hard
`max(950, lo)` floor in `LabStrategy.generate` / `eligible`. Before 09:50 the runner already journals signals as
"shadow", but no live setup has a window before 09:50, so the journals hold no shadow signals to measure.
**No new data source is needed for any of this:** SIP bars, quotes and snapshots come from Alpaca.

## Part 2 harness and checks

- **Early rows (bar closes 09:35 / 09:40 / 09:45)** were rebuilt with the lab pipeline (`build_early.py`: heat_frame +
  extra_features + _outcomes_asym on continuous 5-minute RTH bars).
- **Parity:** the rebuilt 09:50 rows equal the lab frames exactly (`parity.csv`). The only exception is
  2025-03-03..03-21: indicators restart after the locked gap, so those 14 TRAIN sessions are dropped from every
  variant.
- **Minimum ADV:** each live setup's own (L3: 0), with an adv20 ≥ $20M floor. One trade per symbol-day. Costs are
  gates.lab_trades.
- **Exits are the plain geometry, not live's:** live CWT14 also uses scale_out_r 0.25, which is not modelled here.
- Full table: `rescore_results.csv` and `rescore_out.txt`.

## What this says for the owner's question

- **Keep the 09:50 start.** The setups we have get worse when started at 09:40 / 09:45, and the reason is the quality
  of the early signals, not latency or spread.
- The "09:50-09:55 dip / spike then the opposite swing" does not exist as a general, costs-in edge on 2 years. After
  that bar, the next move follows the day's direction (up days help longs, down days help shorts). It is not a
  reversal of the bar.
- If the owner's read is right, it is probably narrower than "any name with a big 09:50-09:55 bar": specific names,
  catalysts, or a level being tested. That would need its own pre-declared study (e.g. a reversal only at a
  prior-day level, or on in-play names flagged by the pre-market scan in Q3).

## Rule changes inside the windows used (owner rule 2026-11-02)

The live statistics (10-06..11-03) straddle several ledger changes:
- 10-12 five demotions
- 10-16 scale-out fix
- 10-20 twin cap
- **10-27 GX1 5-minute clock gate (changes latency, split shown above)**
- 10-28 Primary size ~$5k then ~$4k
- 10-29 Primary −2R latched stop, BAR90, Setup Generator paused
- 10-30 Testing cost filter CF (changes which early signals are skipped for spread)
- 11-02 R2A legs into Testing 2

The two-year backtests are rule-fixed and do not carry these.

## Files

- `PLAN.md`
- `latency.py` → `latency_out.txt`
- `quotes.py` → `quotes_out.txt`
- `build_early.py`
- `rescore.py` → `rescore_results.csv`, `rescore_out.txt`, `parity.csv`
- `reversal.py` → `reversal_results.csv`, `reversal_out.txt`
- `drift.py` → `drift_out.txt`

The scratch data was deleted after the run.
