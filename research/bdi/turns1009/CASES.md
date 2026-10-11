# Turn case studies: the owner's five marked moments, 2026-10-09 (T1)

*Educational only — not financial advice. This is a diagnosis of five hand-picked moments chosen after the fact. Nothing here is tested or live. The signal numbers are in-sample on 4 stocks and include no costs.*

**Inputs**
- SIP 1-minute bars fetched read-only through Alpaca market data (`fetch.py`):
  - AAPL, SPCX, CAT, TSLA, SPY, QQQ, XLK, XLI, XLY and IWM, 2026-09-02..10-09, 04:00-20:00 ET
  - the lab universe (1,223 symbols) for the 10-08 and 10-09 regular sessions
  - the bar cache `data/cache/1Min` for older history
- Market breadth per minute (`breadth.py`), 21 sessions (09-10..10-09), with about 1,154 symbols per minute. The data is under `data/` (git-ignored, 57 MB).

**Scripts**
- `panel.py` builds 111 indicator flags on 1-minute and 5-minute bars, plus levels, market and breadth. It reuses `mcf.research.heat.heat_frame` (MarcoFlow heat) and `setup_lab.extra_features`.
- `cases.py` produces `moments.csv`, `panel_at_turns.csv` (every feature × moment, with timing, percentile and false-alarm counts), `confluence.csv` and `market.csv`.
- `triggers.py` produces `triggers.csv`.
- `signatures.py` produces `signatures.csv` and `signatures_caught.csv`.
- `render.py` produces `tables_moments.md` (a full table for each moment) and `family_tally.csv`.

**Conventions**
- T is the extreme 1-minute bar inside the marked window. A value "at T" is known at T's close (T+1). A 5-minute value is the last 5-minute bar that had closed by then.
- "Lit at T" means the flag was on in any of bars T-2..T.
- Percentiles are taken against the same stock's 20 prior sessions (09-11..10-08, all regular-session minutes).
- A flag is pre-declared as percentile ≤10 / ≥90 in the turn's direction, or the binary pattern (divergence, engulfing and so on). Level flags mean "within 0.10 ATR of the level".
- **Hit (false-alarm test):** from the close of the flag's onset bar, price moves ≥1R in the flag's direction before 1R against, within 60 minutes. R = 0.25 × daily ATR(14), as in the lab. A secondary hit uses 2R before 1R.
  - Onsets use a 15-minute refractory period and the 09:35-15:30 window. They are counted over the 20 prior sessions and over 10-09.
  - precision = hits / onsets; lift = precision / base rate at all minutes.

## Failures and caveats first
1. **The charts show 24-hour sessions, so three of the owner's descriptions of the build-up place it at the wrong time of day.**
   - The screenshots are 1D extended-hours charts with 10-minute candles; the dotted line is the prior close. Two markers 80 minutes apart sit 63 px apart, so x=0 is about 00:00 ET.
   - The SIP data confirms that reading:
     - **AAPL:** the "low around midday" is the premarket/open low. That is 330.74 at 09:28 premarket and 330.70 at 09:33, after a −1.4 ATR gap below the 340.42 prior close. AAPL then rose all day: a grind from 09:33 to 13:49, then the steep leg.
     - **SPCX:** the "high around 10:00" is the **07:35 premarket high (167.74)**. Inside the regular session the high was 09:31 (166.38). The 10:00-10:13 tops (163.39 / 163.30) are lower highs late in a sell-off that began premarket. The thin wick on the chart is an 08:39 print at 160.09.
     - **TSLA:** the "run-up 10:20-10:50" is the premarket→09:53 run (HOD 388.56). 10:51 (388.17) is the second top of an hour-long plateau.
     - **CAT:** the true low is 09:46 (791.19). The marked 10:11 low (794.04) is a higher-low retest.
   - So I studied each owner bar (M1-M5) **and** the true extreme next to it (the "b"/"c" variants).
2. **The OHLC of every marked bar matches SIP to the cent; the volumes do not.**

   | marked bar | screenshot volume | SIP volume |
   |---|---|---|
   | AAPL 15:00 | 441,148 | 689,534 |
   | SPCX 10:10 | 2.307M | 3.880M |
   | CAT 10:10 | 10,431 | 26,235 |
   | TSLA 10:50 | 696,060 | 1,075,788 |

   The app shows non-consolidated volume. Every volume reading here is SIP.
3. **The selection is hindsight.**
   - 11 moments × 111 flags = 1,221 cells, so something lights up by chance.
   - At a random minute, **12.4 of the 99 non-level flags are lit on average** (median 8), against a 10% per-flag rate in a ±2-bar window.
   - Most flags that were lit at a turn have **lift ≈ 1.0-1.4** and fire **4-15 times per session** in the same stock. They are not turn detectors.
4. **Three of the five owner moments were "quiet": nothing unusual at the turn.** SPCX 10:13 had 1 lit flag (2.7th percentile of a random minute's count). CAT 10:11 had 10 (58th) and AAPL 13:49 had 22 (84th). These swings can be seen only after the fact.
5. **The houses are small.** Measured from the extreme to the next swing (the end is the first 1R retrace), they are 0.30-0.77 daily ATR (1.2-3.1R). Measured from the close of the turn bar they are 1.1-3.0R. Round-trip cost is about 0.03-0.06R (1c + 1 bps a side). On the 2R-before-1R label, only TSLA 10:51 and SPCX 09:31 qualify.

## The moments (sizes)
| id | stock | side | turn bar T (extreme) | swing end | from extreme | from T close | MAE after T close | owner-marked? |
|---|---|---|---|---|---|---|---|---|
| M1 | AAPL | long | 13:49 (334.66) | 15:14 (338.61) | 0.64 ATR / 2.55R | 2.37R | 0.15R | yes |
| M1c | AAPL | long | 09:33 (330.70) session low | 09:46 (333.80)* | 0.50 / 2.00 | 1.19 | 0.40 | the true "bottom" of the chart |
| M1b | AAPL | long | 12:13 (333.68) midday range low | 15:14 | 0.79 / 3.18 | 3.04 | 0.00 | no |
| M2 | AAPL | short | 15:14 (338.61) HOD | 15:45 (336.20) | 0.39 / 1.55 | 1.53 | 0.01 | yes (15:00 bar; the top is in 15:10) |
| M3 | SPCX | short | 10:13 (163.30) | 10:23 (161.32) | 0.30 / 1.20 | 1.13 | 0.00 | yes; fully retraced to 164.31 by 10:39 |
| M3a | SPCX | short | 10:02 (163.39) first top | 10:23 | 0.31 / 1.26 | 1.16 | 0.04 | no |
| M3b | SPCX | short | 09:31 (166.38) RTH high | 10:23 | 0.77 / 3.08 | 2.09 | 0.54 | no (premarket high 167.74 at 07:35) |
| M4 | CAT | long | 10:11 (794.04) | 11:03 (804.31) | 0.39 / 1.58 | 1.39 | 0.04 | yes |
| M4b | CAT | long | 09:46 (791.19) LOD | 11:03 | 0.50 / 2.01 | 2.01 | 0.00 | no |
| M5 | TSLA | short | 10:51 (388.17) | 11:35 (379.71) | 0.77 / 3.06 | 3.01 | 0.03 | yes |
| M5b | TSLA | short | 09:53 (388.56) HOD | 10:00 (383.78)* | 0.43 / 1.73 | 1.67 | 0.00 | no |

\*The swing end is the first 1R retrace. The trend later resumed: AAPL to 15:14, TSLA's range to 10:51.

Daily ATR (R): AAPL 6.21 (1.55), SPCX 6.58 (1.64), CAT 26.06 (6.52), TSLA 11.05 (2.76).

**Structure-break trigger** (`triggers.csv`): the first 1-minute close beyond the range of the 10 minutes before the turn. This is known at the minute; the turn itself is not.

| id | trigger | after T | R left to the swing end | MAE after the trigger | share of the swing left |
|---|---|---|---|---|---|
| M1 | 14:08 > 335.40 | 19 min | 2.06R | 0.03R | 81% |
| M1b | 12:19 > 334.59 | 6 min | 2.59R | 0.16R | 82% |
| M2 | 15:24 < 337.77 | 10 min | 0.79R | 0.05R | 51% |
| M3 | 10:16 < 162.45 | 3 min | 0.65R | 0.01R | 54% |
| M5 | 11:07 < 386.06 | 16 min | 2.07R | 0.16R | 68% |
| M4, M4b | no close above the pre-turn range (800.5 / 801.1) within 30 min | | | | |
| M1c | none before the swing end | | | | |

The three biggest owner houses (M1, M1b, M5) still had more than 2R left after a confirmation entry. M2 and M3 had less than 0.8R left.

## Per moment
The tables show flags lit at T, with timing flags first. A timing flag is one lit for less than half of the prior hour. Full 14-row tables are in `tables_moments.md`; every feature is in `panel_at_turns.csv`.

Column key for the tables below:
- **pct**: percentile of the value against the stock's 20 prior sessions.
- **run began**: minutes before T that the current lit run started.
- **on/sess**: onsets per session over the 20 prior sessions.
- **prec**: precision (share of onsets that hit 1R first).
- **lift**: precision / base rate.

### M1 AAPL long, 13:49: launch of the afternoon leg (owner)
**Context**
- Range from 11:10 to 14:00 between 333.7 and 335.4, under the prior-day low of 335.90, after a −1.4 ATR gap.
- 13:49 retests the 13:22 low **to the cent** (334.66), 0.05 ATR above the 12:32 low. It sits at the $335 round number.
- The leg starts with the 14:08 range break and reclaims the prior-day low by about 14:12.

**What flagged it.** At T, the flags were only a short 1-minute flush:

| feature | pct | run began | on/sess | prec | lift |
|---|---|---|---|---|---|
| roc10_atr_1m | 25 | 1 | 6.4 | 0.17 | 1.37 |
| c_ema9_atr_1m | 28 | 1 | 7.5 | 0.17 | 1.33 |
| roc5_atr_1m | 19 | 2 | 8.3 | 0.16 | 1.30 |
| CCI20 1m | 3 | 1 | 7.6 | 0.11 | 0.84 |

Other readings at T:
- 1-minute bullish engulfing and outside bar, with lift ≈ 1.0 and 14-15 onsets per session.
- Volume z 97th percentile and relative volume 2.1×. A 286k-share print came at 13:51, after T.
- 1-minute RSI, MACD and OBV bullish divergences, lit since 13:16 (33 minutes earlier, during the first test of the low).

**What was silent.** Every 5-minute oscillator was mid-range (RSI14 51, %B 0.56), along with the market and breadth.

**Confluence and market**
- 22 flags lit: the 84th percentile of a random minute, with 18.9% hit vs a 12.5% base.
- **SPY explains ~6% of the move.** SPY bottomed 27+ minutes earlier and drifted up all afternoon (+0.10% over the leg vs AAPL +1.09%; beta 0.64).

**Hindsight:** a double-bottom retest plus a 1-minute flush describes this bar. Those flags fired 6-15 times per session in AAPL, mostly without a follow-through.

### M1c AAPL long, 09:33: the actual "bottom" of the owner's chart
- An opening flush after a −1.4 ATR gap: 1-minute RSI14, ROC30, EMA9-21 and distance to the SMA50/200 all at the **0th percentile**. ATR expansion was at the 100th and volume z (5m) at the 99th, with a hammer and a 0.87 lower wick.
- 38 flags lit (94th percentile). Hits for "count ≥ 36" are 27.8% vs 12.5%.
- AAPL bottomed **15 minutes before SPY** (SPY low 09:48, QQQ 09:51). The market was falling during the first 13 minutes of AAPL's bounce, so the market share was −16%.
- The 5-minute values at 09:33 are the prior day's last bar (stale). The 5-minute "oversold" readings appear only after T.

### M2 AAPL short, 15:14: top of the afternoon rally (owner)
**Context**
- Marginal new high: 0.05 ATR above the 15:04 high, 0.6 ATR below the prior close 340.42. Nothing overhead was reached.

**Stretched state** (52 flags lit, the **98.9th percentile**; 85 such minutes in 10 of 20 sessions, 32.9% hit vs 11.1%). These flags had been on for 35-60 minutes:

| flag | percentile |
|---|---|
| 5-minute RSI14 | 99th |
| 5-minute VWAP z | 99th (lit for 60 minutes) |
| 5-minute CMF | 99th |
| 5-minute DI+ minus DI− | 99th |
| 1-minute RSI14 | 97th |
| ROC30 | 95th |
| distance to HOD | ≈0 (lift 2.08) |

**Timing**
- 5-minute volume z: 94th percentile, lit at T (lift 1.78).
- 1-minute ATR expansion: 93rd percentile.
- After T: a 1-minute shooting star, 1-minute MACD cross-down and 5-minute MFI.

**Market:** SPY topped 8 minutes later (15:22). XLK also topped at 15:22, while QQQ had topped at 14:50. SPY explains about 5% of AAPL's drop (−0.05% vs −0.68%).

**Breadth:** 0.67 of the universe above VWAP (88th percentile). This was the only owner moment with high breadth.

### M3 SPCX short, 10:13: the owner's 10:10 bar
**Context**
- The second top (163.30) of a 10:02/10:13 double top, after the premarket high (07:35, 167.74) → RTH high (09:31, 166.38) → 09:52 low (162.14) sell-off.

**Signals**
- **One flag lit at T** (1-minute green-run length): the 2.7th percentile, quieter than an ordinary minute.
- Everything came after T: a bearish engulfing bar, 820k-share volume at 10:17 and the 1-minute MACD cross.
- The break of 162.45 at 10:16 left 0.65R. The low was 161.32 at 10:22, then a full V back to 164.31 by 10:39.

**Market:** SPY and QQQ rose over the same 10 minutes (market share −11%).

**Better short:**
- **M3b, 09:31 RTH high:** 3.08R from the extreme.
  - Lit: ROC10 at the 100th percentile, ATR expansion 100th, a climax bar, and 5-minute volume z at the 99th.
  - 28 flags lit, at the 89th percentile (22.3% hit vs 14.9%).
- **The 07:35 premarket high:** not scorable with the regular-session panel.

### M4 CAT long, 10:11: V-reversal (owner)
**Context**
- A 4-bar flush from 800.5 (10:07) to 794.04. The flush landed **on a cluster of levels**, all within 0.1 ATR (CAT ATR $26, so the band is ±$2.6):
  - open 796.22
  - prior close 796.17
  - premarket low 795.02
  - $795 round number
- Volume was thin: 2-6k shares per minute.

**Signals at T**

| flag | percentile |
|---|---|
| 1-minute RSI2 | 1.1 (2nd percentile) |
| ROC5 | 2nd percentile |
| c−EMA9 | 3rd percentile |
| QQQ 30-minute return | 7th percentile (lift 1.69) |
| near the premarket low | lift 1.85, 2.95 onsets/session |
| near the open | lift 1.58 |

- The hammer and long lower wick came only after T.
- 10 flags lit (58th percentile).

**Market:** CAT is the one name where the market mattered (beta 2.2). SPY explained 34% of the leg. CAT's **true low (M4b, 09:46) came within 2 minutes of the SPY (09:48), XLI (09:45) and QQQ (09:51) lows**. M4b had 28 flags lit (89th percentile), 34.6% hit vs 17.4%, and sat at the prior-day low (lift 2.4) and 2 SD below VWAP.

### M5 TSLA short, 10:51: top after the spike (owner)
**Context**
- A **double top** with the 09:53 HOD (388.17 vs 388.56, −0.035 ATR), after a 4-minute pop (10:47-10:51, +1.7, 230k shares at 10:51).

**Stretched readings** at T (biggest owner house: 3.06R; 46 flags lit, 96.9th percentile, 25.8% hit vs 9.8%):

| flag | percentile | lift |
|---|---|---|
| from open | 0.51 ATR, 90th | 3.41, but 0.3 onsets/session (n≈6, noise-level) |
| 1-minute VWAP z | 94th | 2.16 |
| distance to HOD | 4th | 2.21 |
| 1-minute RSI14 | 94th | 1.77 |
| 5-minute SMA200 distance | 92nd | 7.3 (0.35 onsets/session, n≈7) |
| 5-minute ADX | 98th | 4.5 (n≈16) |

**Timing**
- **5-minute MACD crossed down 7 minutes before T** (lift 1.77).
- 5-minute outside bar.
- After T: 1-minute MACD/EMA cross-down.
- The break of 386.06 at 11:07 left 2.07R.

**Market:** SPY kept rising (market share 2%). XLY topped 1 minute after T, but TSLA is a top XLY holding, so that is circular.

**M5b (09:53 HOD)** had the highest confluence of all: 60 lit, 99.8th percentile. Yet only 12.5% of such minutes hit, with n = 16 minutes.

## Hindsight check (false alarms)
- **Lift of the flags lit at T.** Across all 11 moments, median 1.05-1.5. Only rare, stretched-state flags exceed 2, and those rest on fewer than 20 onsets in 20 sessions.
- **The most frequently lit flags** (1-minute c−EMA9, ROC5, Williams %R, RSI5 and Keltner, lit at 8-9 of 11 moments) are also the most common. They fire 6-10 times per session in each stock with lift 1.1-1.5.
  - On 10-09 alone, AAPL had 6-8 such onsets for 2-3 hits.
  - The owner marked one long.
- **Confluence count is the one thing that separated turns from ordinary minutes, and only for stretched turns** (M1c, M2, M3b, M4b, M5, M5b at the 89th-99.8th percentile).
  - At those counts, precision is 22-35% vs a 10-17% base.
  - The same count level still occurred on 13-353 minutes of the turn day.
- **It did not separate the owner's quiet turns** (M1, M1b, M3, M3a, M4).

## Cross-case summary
**Longs** (M1, M1b, M1c, M4, M4b):
- 1-minute flush flags lit at all 5: ROC5/ROC10 and c−EMA9 at ≤10th percentile, and 1-minute RSI2/stochastic oversold. The run starts 0-4 minutes before the low.
- Plus a **level**:
  - a retested intraday low (M1, M1b)
  - the open, prior close, premarket low or prior-day low (M4, M4b)
  - the $5 round number (M1, M4)
- 5-minute oscillators were silent except at the opening flushes.

**Shorts** (M2, M5, M3b, M5b):
- A **stretched state that lasted 20-60 minutes**: VWAP z, RSI14, ROC30 and distance to SMA50/200 at the 90th-99th percentile, with distance to HOD ≈0.
- The timing came from a **momentum roll**: a 5-minute MACD cross-down 0-7 minutes before, or a 1-minute MACD cross, shooting star or bearish engulfing at T+1..T+5.
- Three tops were also **retests of a prior high within 0.05 ATR**: M5 vs the HOD, M2 a 0.05 ATR marginal new high, M3 vs 10:02.

**The market (SPY at the same minutes):**
- **It explained little of the owner-marked moves:** AAPL 6% / 5%, TSLA 2%, SPCX −11%, CAT 34%.
- SPY's own turn led by about 23-27 minutes (M1, M4), followed by 8-27 minutes (M2, M5), or did not exist.
- Only CAT's true low (M4b) and AAPL's open low (M1c, 15 minutes ahead of SPY) were market-timed turns.
- Breadth (share above VWAP) sat at 0.46-0.67 at every turn and did not turn with any of them.

**MarcoFlow heat (5m)** lit only at the two opening lows (M1c, M4b), at the 94th-95th percentile, with lift 1.6-1.7. At 09:33 it is stale (the prior day's bar). It added nothing at the owner moments.

## Candidate confluence signatures for the scale-up worker
`signatures.py` gives a first in-sample look: 4 stocks × 20 prior sessions, 09:45-15:30, onsets with a 15-minute refractory, signal level, no costs. 7 signatures × 2 sides = 14 configurations. All rules are known at the bar close.

| signature (long / short mirror) | onsets per stock-session | 1R-first | stop-first | base | lift | owner/true moments caught (T..T+5) |
|---|---|---|---|---|---|---|
| **C3b** 5m VWAP z AND 5m RSI14 both ≥ p90 (≤ p10 for longs) + 1m trigger (MACD-hist cross within 3 bars, engulfing, or shooting star/hammer) | 1.2-1.3 | short 27.6% / long 23.3% | 13.3% / 15.5% | 12-13% | 2.3 / 1.7 | M2 (15:15) |
| **C3** the same with VWAP z OR RSI14 | 3.3-3.5 | 22.5% / 22.3% | 16.5% / 11.9% | | 1.85 / 1.65 | M2, M5 (10:56), M1c, M3b, M5b |
| **C6** 1m ROC10 ≤ p10 (≥ p90) + the same 1m trigger | 2.4-2.5 | 23.4% / 26.8% | 17.4% / 18.4% | | 1.7 / 2.2 | M1c, M3b, M4b |
| **C2** pivot retest + 1m ROC10 flush | 2.0-2.5 | 18.3% / 22.1% | 15.8% / 19.6% | | 1.4 / 1.8 | M4, M4b, M5 |
| **C4** low within 0.1 ATR of ≥2 of {open, prior close, premarket low, prior-day low} + close in the upper half | 4.6 | long 15.6% | 9.3% | | 1.16 | M4, M4b |
| **C5** pivot retest + 5m stretched | 2.9-3.2 | 17-18% | 15-18% | | 1.3-1.4 | M5 |
| **C1** pivot retest (within −0.05/+0.10 ATR of a confirmed 5-bar pivot from 10-90 min earlier) + close in the reversal half | **17.6** | 10-12% | 11-12% | | **0.84-0.90** | M1, M1b, M3, M4, M4b, M5 |

- **C1 is the clearest hindsight trap.** It "explains" 6 of 11 moments and has lift below 1. Double tops and bottoms are everywhere.
- The "net" column in `signatures.csv` (hits − stops, timeouts 0, no costs) is +0.06 to +0.14R per signal for C3/C3b/C6. **Read that as an upper bound:** the rules were chosen from these moments, and timeouts are scored at 0.

**For the scale-up worker** (all stocks, two-year history, costs, gates in `mcf/research/gates.py`, try-count from 14 here plus their grid):
1. **S1 stretched + roll (short; long mirror):** C3b with thresholds 85/90/95, the trigger family each one alone, and 10:00-15:30.
2. **S2 1-minute flush + reversal trigger:** C6, with ROC5/ROC10 and p5/p10.
3. **S3 flush into a level cluster:** C4 ∧ C6 (the CAT pattern). Test whether the level adds anything over C6 alone.
4. **S4 market-confirmed low:** a stock's 1-minute flush (C6 long) within ±5 minutes of an SPY/sector 30-minute low (the CAT M4b pattern). This needs the market extreme to be known causally, e.g. SPY makes a 1-minute higher low and closes above its prior 3-bar high.
5. **S5 confluence count:** the side-specific count of these ~99 flags ≥ the stock's own p97 + the 1-minute trigger.
6. **Exit check:** the houses are 1.2-3R. A fixed 1R target captures the median case, and the three big owner houses (M1, M1b, M5) each left more than 2R after a structure-break entry. Test 1R vs trail-after-1R.
7. **Do not pursue:** C1 bare retests, single oscillators (RSI/stochastic/CCI/Williams %R lift ≈ 1.0), breadth level, or MarcoFlow heat as a turn timer. Each has lift ≈ 1 or no sample here.

**Counts:** 111 flags × 11 moments examined (1,221 cells), plus 14 signature configurations. Percentiles use 20 sessions per stock. No holdout was touched.
