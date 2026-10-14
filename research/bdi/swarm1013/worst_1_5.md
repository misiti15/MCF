# Primary 2026-10-13: autopsy of the worst 5 trades (swarm1013, worst #1-#5)

*Educational only — not financial advice. Live **paper** trades from one session (rule 7): this is a diagnosis, not evidence. **0 configurations were tested on the history.** Every "what if" below is a one-session replay on SIP 1-minute bars (Alpaca market data, read-only). Replays are gross: they use the journal fill as the entry, take the stop first when one minute touches both legs, and include no costs. Roughly 20 exit/entry variants were replayed per trade, so a few will look good by chance. None of this justifies a live change. The candidate rules at the end go to the backlog for a full test.*

Inputs:
- `journal.db` from `origin/mcf-data` (run 1, 18 trades) and `research/bdi/nightly1013/trades.csv`.
- Rule values recomputed with `mcf.research.heat.heat_frame` and `setup_lab.extra_features` on 5-minute bars (history from 2026-08-20). The four NS2 masks and the MF1 mask reproduce on the recomputed values.
- Context ETFs: SPY, QQQ, IWM, SMH, XLK and IGV.
- Scratch scripts (not committed): `scratchpad/swarm1013/w15_an.py`, `w15_alt.py`, `w15_win.py`.

The losers are ranked by $ P/L. By R the order differs: FPS MF1 is the worst at −1.22R, and CVS NS3 at −1.09R comes ahead of TTMI.

## Market on the day
- **Split tape.**
  - QQQ: +0.56% at 10:01, back to +0.10% at 11:30, then +0.57% by 12:30.
  - SMH: +0.86% at 10:45, −0.05% at 11:30, then **+1.42% at 12:30** and +1.61% at the close.
  - IWM: −0.5 to −0.8% all day.
  - QQQ fromOpen minus IWM fromOpen was at least 0.75% during every entry below.
- **The NS2 split.** Primary's NS2 shorts (5 of them in semis and AI hardware) either reached target during the 10:45–11:30 QQQ/SMH dip or were stopped in the 11:46–12:30 SMH rebound.
  - **Winners:** AMD reached target at 11:26, SEI at 11:25 and EBAY within 30 minutes.
  - **Losers:** the four NS2 losers were all still open at 11:46.

## The five trades

| # | trade | entry (ET) | entry / stop / target | exit | R | $ | MFE (time) | MAE | loss type |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TTMI NS2 short, 17 sh | 11:10:55 | 108.52 / 110.71 / 106.65 | stop 12:32, 110.81 | −1.05 | −38.93 | 0.46R (11:39, 107.52) | 1.00 | gave back, then trend day (closed 115.85, **−3.3R**) |
| 2 | CBRS NS2 short, 13 sh | 10:50:33 | 146.91 / 150.34 / 143.86 | flatten 15:55, 149.80 | −0.84 | −37.57 | 0.25R (11:18) | 0.90 | never worked, late hold (high 150.00 at 15:54) |
| 3 | SWKS NS2 short, 25 sh | 10:31:03 | 75.38 / 76.66 / 74.41 | stop 14:31, 76.70 | −1.03 | −33.00 | 0.09R (11:48) | 1.24 | never worked |
| 4 | CORZ NS2 short, 127 sh | 10:45:37 | 14.97 / 15.196 / 14.764 | stop 12:30, 15.21 | −1.06 | −30.50 | **0.84R (11:37, 14.78)**: target missed by 1.6c | 1.17 | gave back gains |
| 5 | FPS MF1 short, 53 sh | 10:00:54 | 35.73 / 36.016 / 35.161 (t1s05: the stop is 0.5 lab-R) | stop 10:02, 36.08 | −1.22 | −18.54 | 0.20R (10:00) | 1.08 | noise stop inside the recent range (98 seconds) |

**Shared facts**
- Every one of the five closed the day beyond the stop: on the short side, above the entry.
- None reached its target after the exit.
- A wider stop could not have rescued any of them. The setups picked the wrong side of a semis trend day.

### Rule values at the decision bar against the thresholds

**NS2 thresholds:** the 5-minute close crosses above the SMA50, RSI(14) ≥ 60 and fromOpen > 2%.

| trade | SMA50 dist (prev → now) | RSI14 | fromOpen | gap vs prior close | vs prior close | VWAP dist | SMA20 slope | buyPressure |
|---|---|---|---|---|---|---|---|---|
| TTMI | −0.07 → **+0.26** | **60.1** (just over the bar) | 2.24 | −3.65% | −1.5% | +0.67 | −0.51 | +0.30 |
| CBRS | −0.22 → **+0.09** | 75.2 | 2.72 | −2.33% | +0.3% | +0.86 | −0.19 | −0.01 |
| SWKS | −0.10 → +0.19 | **60.2** (just over the bar) | 2.41 | −1.23% | +1.1% | **−0.14 (below VWAP)** | **+0.23 (rising)** | −0.60 |
| CORZ | −0.14 → **+0.07** | 84.5 | 2.67 | −2.86% | −0.3% | +2.37 | −0.20 | −0.32 |
| *winners:* AMD / SEI / EBAY | +0.23 / +0.07 / +0.34 | 80.6 / 63.0 / 61.1 | 2.4 / 2.1 / 2.0 | −2.8 / −3.8 / −0.4% | | +1.2 / +0.6 / +0.7 | all negative | |

**FPS MF1 thresholds:** heat ≤ −30, buyPressure < −0.25 and vwapDist > +0.05. On the 09:55 bar:
- heat **−30.96**, just past the threshold
- buyPressure −0.55
- vwapDist +0.25
- FPS had gapped −4.0% (prior close 37.10, open 35.60), made its low at 34.75 at 09:34, and rallied to 36.33 at 09:45.

**Honest read**
- Most of the threshold values were marginal: two RSI readings at about 60.1, two SMA50 crosses of +0.07–0.09%, and the heat reading at −30.96.
- But the winners were just as marginal (SEI: SMA +0.07, RSI 63). The gap-down "gap-fill" profile is shared by winners and losers: AMD and SEI also gapped −2.8% and −3.8%.
- **No entry metric known at the time separates the four NS2 losers from the three winners.**
- The only odd one is SWKS. It was the only NS2 short taken **below VWAP** with a **rising** SMA20. The other six entries were all above VWAP and had a falling SMA20.

### Market and sector context at entry (fromOpen %, VWAP side)

| trade | SPY | QQQ | IWM | SMH | stock |
|---|---|---|---|---|---|
| TTMI 11:10 | −0.06 (below) | +0.26 (below) | −0.54 | +0.41 (below) | +2.24 (+0.72 above) |
| CBRS 10:50 | +0.01 | +0.38 (below) | −0.60 | +0.71 (above) | +2.72 |
| SWKS 10:31 | +0.02 | +0.41 (at VWAP) | −0.60 | +0.67 (above) | +2.25 |
| CORZ 10:45 | +0.04 | +0.48 (above) | −0.59 | +0.86 (above) | +2.67 |
| FPS 10:00 | +0.10 | +0.56 (above, near the day's QQQ high) | −0.52 | +0.69 (above) | +0.37 |

- Correlation of 5-minute returns with SMH (Sep 1 – Oct 12): TTMI 0.55, AMD 0.70, FPS 0.45, CBRS 0.43, CORZ 0.39, SWKS 0.23.
  - The traded symbols correlate more with SMH than with QQQ, and barely at all with IGV.
  - **Five of the seven NS2 lots (SWKS, AMD, CORZ, CBRS, TTMI) were opened between 10:31 and 11:10 on names that track SMH.** Together they lost −$123.8. In effect this was a single semis short at five times the size.

### Path detail and execution

**TTMI**
- MFE of 0.46R at 11:39.
- The stop was touched by **1 cent**: the 12:32 high was 110.72 against a stop of 110.711, and that minute closed at 110.43.
- Price then stayed at or below 110.58 for 15 minutes. From 13:30 it trended to 116.35.
- A stop triggered on the close instead of the wick would have exited later and at a worse price. The wick stop was not the problem here.

**CBRS**
- Never reached 0.3R.
- It was held to 15:55 and flattened at 149.80. The 15:55 bar close was 149.575, so the flatten fill cost a further 0.07R.

**SWKS**
- MFE was only 0.09R.
- The stop broke on a real close: the 14:31 minute closed at 76.96, above the stop of 76.66.

**CORZ**
- Reached 14.78 at 11:37 against a target of 14.764, missing it by **0.07R**.
- It was stopped 53 minutes later.

**FPS**
- The 0.5-lab-R stop (36.016) sat **below the high of the previous 15 minutes** (36.33 at 09:45; also 36.14 at 09:53).
  - The 10:02 wick reached 36.04 and the minute closed at 35.88.
  - Ten minutes later the price was at 36.224.
- Entry fill: 35.73 against a ref of 35.731.
- **Exit slippage was 0.22R.** The stop was 36.016 and the fill 36.08.
- FPS was then **shorted again by MF2 at 10:45** (worst #6: −$16.43, MFE 1.45 stop-units, stopped 12:20).

**Slippage across the five**
- **Exit (stop fills):** $7.8 in total. Per trade: FPS 3.38, TTMI 1.68, CORZ 1.73, SWKS 1.00.
- **Entry (sold at the bid, under the signal ref price):** about $10.4 in total. Per trade: SWKS 0.155 ($3.9), CBRS 0.19 ($2.5), TTMI 0.16 ($2.7), CORZ ($1.3).
- Together that is about $18 of the −$158.5. Execution is a secondary cause, not the main one.

### Alternatives (replayed R in units of each trade's actual stop distance; base = journal geometry)

| alternative | TTMI | CBRS | SWKS | CORZ | FPS | sum 5 | NS2 all 7 (incl. AMD, SEI, EBAY) |
|---|---|---|---|---|---|---|---|
| base | −1.00 | −0.78 | −1.00 | −1.00 | −1.00 | −4.78 | −1.44 |
| stop ×1.5 | −1.50 | −0.78 | −0.81 | −1.50 | −1.50 | −6.09 | n/a |
| stop ×2 | −2.00 | −0.78 | −0.81 | −2.00 | −2.00 | −7.59 | n/a |
| hold to 15:55, no stop | −3.34 | −0.78 | −0.81 | −1.70 | −1.64 | −8.27 | n/a |
| breakeven after +0.3R | **0.00** | −0.78 | −1.00 | **0.00** | −1.00 | −2.78 | **+0.56** |
| breakeven after +0.5R | −1.00 | −0.78 | −1.00 | 0.00 | −1.00 | −3.78 | −0.44 |
| trail 0.5R | −1.00 | −0.78 | −1.00 | +0.34 | −1.00 | −3.44 | −0.10 |
| target 0.8R | −1.00 | −0.78 | −1.00 | +0.80 | −1.00 | −2.98 | +0.42 |
| time stop 30 min | +0.35 | +0.18 | −0.16 | +0.31 | −1.00 | −0.32 | **+2.74** (cuts AMD to +0.61) |
| time stop 60 min | −0.47 | −0.32 | −0.29 | +0.68 | −1.00 | −1.40 | +1.94 |
| exit when QQQ's 5-min close is above its VWAP | −0.44 (12:05) | −0.38 (12:05) | −0.38 (10:40) | +0.11 (12:05) | stopped first | −2.09 | **+1.00** (cuts EBAY to +0.40) |
| delay entry 5 / 15 / 30 / 60 min (same R) | all −1 | −1 / −0.69 / −0.86 / −0.46 | all −1 | all −1 | −1 / **+1** / −1 / **+1** | n/a | n/a |
| re-entry after stop (next 5-min close back through entry) | none | n/a | none | none | 10:25 at 35.52, −1 | n/a | n/a |
| opposite side, 1R/1R | +1 | +0.78 | +1 | +1 | +1 | n/a | n/a |
| G7 split-tape skip (bdi1013) | skip | skip | skip | skip | skip | +4.78 | also skips all 3 winners (+2.37R) |

**Reading the table**
- **Wider stops and later entries do not help.** These were trend-day losers, not noise stops. FPS is the exception: entering 15 minutes later at 36.10 would have reached target, and a stop above 36.33 would have survived the move.
- **The opposite side is hindsight.** longs1013 Q1 showed that the mirror trade is set by the regime: the MF and NS longs win in up sessions and lose in down sessions. The only signal known at entry that pointed long was the sector/index tape: SMH and QQQ were above VWAP at 3 of the 4 NS2 entries.
  - That tape signal is what G7 (split-tape) and indexlink have already tested: G7 sits in Testing at t 2.23, and indexlink found nothing for Primary.
- **What helped was management of the NS2 trades that had not paid by about 11:30:**
  - a 30-minute time stop
  - a scratch at +0.3R
  - an exit when the index reclaimed its VWAP
- **Book-wide versions of these exits already failed.** EXIT_STUDY (t6-exit-overlay) and sw-w4-book-exits failed. The best book-wide result was the 30-minute time stop if MFE < 0.25R, at t 0.62.
  - Today is one up-tape day. On 10-08 NS2 made +$33 with a different path.
  - So the only candidates worth testing are **setup-specific** versions or **new conditioning variables**: index reclaim, sector cluster, recent range.

## Candidate rules (precise, testable; none validated)
Each needs the 2-year 1-minute path replay with costs and its configuration count, under rule 19. The locked block stays untouched.

1. **NS2-QX: index-reclaim exit for shorts.** Exit an open NS2/RW6 short at market at the close of the first 5-minute bar after entry on which QQQ closes above its session VWAP (only while the trade is not at target).
   - Variants: QQQ or SMH as the index; the trade must have been entered with the index below or at its VWAP, or not.
   - Today: NS2 −1.44R → +1.00R (n 7).
   - New conditioning variable: it is not in sw-w4 or EXIT_STUDY.
2. **NS2-T30: setup-specific scratch.** Exit an NS2 short at market 30 minutes (variants 20/45) after entry if MFE < 0.5R; otherwise keep the t1s1 brackets.
   - Today: +2.74R (n 7).
   - The book-wide version failed (t 0.62), so the test is NS2/RW6 lineage only, scored against that failure count.
3. **NS2-BE03: breakeven after +0.3R MFE for NS2.** Move the stop to entry once MFE ≥ 0.3R.
   - Today: +0.56R.
   - Prior evidence is weak: the book-wide breakeven at +0.75R failed. Test it together with #2, as one family.
4. **CLUSTER-2: correlated same-side lot cap (portfolio).** Skip a new short (long) when two or more open short (long) lots already have a 20-day 5-minute-return correlation ≥ 0.35 with the new symbol, or with the same sector ETF (SMH, XLK, …).
   - Today it would have skipped CORZ, CBRS and TTMI (+$107 in hindsight) and kept SWKS and AMD.
   - It is distinct from the stacking cap (one symbol) and from G7 (the index).
5. **STOP-IN-RANGE skip (entry/execution, all market-bracket setups).** Skip a short when stop < max(high of the last 15 one-minute bars); the long mirror uses the low.
   - Of today's 10 Primary shorts with bars, it flags only FPS MF1 (with a 30-minute window it also flags FPS MF2: both losers).
   - The same rule as a stop-floor variant instead of a skip: stop = max(geometry stop, 15-minute high + 1 tick), with the size recomputed to the same $ risk.
6. **NS2-VW: require vwapDistPct > 0 and SMA20 slope ≤ 0 on the NS2 signal bar.**
   - Today it removes only SWKS (n 1). The rising-EMA guard in trendguard (8,494 configurations) is close to this, so the prior is low.
   - Score it only as a two-variable add-on to the trendguard lineage count.
7. **LOCKOUT-60: same-symbol short lockout.** After a short lot on a symbol is stopped, block new shorts on that symbol for 60 minutes (variant: the rest of the day).
   - Today only FPS (MF2 at 10:45 after MF1's 10:02 stop, −1.03R), so n = 1.

Not proposed:
- **Wider stops, delayed entries, re-entries and the opposite side.** The replays do not support them, or they are hindsight.
- **G7 split-tape.** It is already in Testing from bdi1013, and today it would also have removed all three NS2 winners.

Five trades are no evidence of an edge. These are hypotheses for the backlog, not rules.
