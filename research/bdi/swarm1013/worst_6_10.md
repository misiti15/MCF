# 2026-10-13 Primary: worst trades #6 to #10, trade by trade

*Educational only — not financial advice. This covers 5 paper trades from one session (rule 7), so it is a diagnosis, not evidence. **0 configurations were tested on history.** Every "alternative" below is a replay of this one day on 1-minute bars, and every rule candidate is a hypothesis for the backlog gates.*

## Scope
- Primary had **18 trades: 9 losers, 9 winners.** Ranked by P/L, the losers are TTMI, CBRS, SWKS, CORZ, FPS (MF1), **FPS (MF2), CVS, AME, XLI**. Those last four are #6 to #9.
- There are **only 9 losers**, and Primary had no break-even trades. Slot #10 therefore goes to the **smallest winner, NOK NS1 (+$3.90)**. It is included because its execution was effectively a loss-shaped trade.

**Data used:**
- `research/bdi/nightly1013/trades.csv`, and `journal.db` from `origin/mcf-data` (signals rows).
- SIP 1-minute bars from 2026-09-22 to 10-13, fetched read-only with `mcf.data.alpaca_data.fetch_bars`.
- Entry metrics were recomputed on 5-minute bars with `mcf.research.heat.heat_frame`. The journal `info` field does not store the metric values, only the layer text.
- R means the distance from the fill to the stop. Scripts: scratchpad `swarm1013b/an.py`.

**Tape:**
- SPY finished +0.09%, QQQ +0.56% and IWM −0.46%.
- From 10:00 to 11:46 everything sagged: IWM −0.28% and XLI −0.41% between 11:15 and 11:46.
- From 11:46 to 12:40 there was a broad rebound: XLI +0.65%, XLK +0.79%, IWM +0.31%.
- XLV, the healthcare ETF, was the weakest sector all day (−1.3% to −1.6%).

| # | trade | setup (module) | entry → exit (ET) | P/L | MFE / MAE (R) | loss type |
|---|---|---|---|---|---|---|
| 6 | FPS short 53 sh | MF2-open-rsimidhi-flowsell (`research/primitives/marcoflow/MF-open-rsimidhi-flowsell.py`, t1s05) | 10:45:41 @35.67 → 12:20:48 @35.98 stop | −16.43 | **+1.45** at 11:47 / −1.00 | gave back gains |
| 7 | CVS short 21 sh | NS3-failed-vwap-reclaim-short (`research/owner1008/NS3-…py`, t1s1) | 11:15:35 @87.25 → 12:05:58 @87.85 stop | −12.59 | +0.18 at 11:17 / −1.02 | never worked |
| 8 | AME short 7 sh | MF5-flowsell-vwapup-rsi5hi (`research/primitives/marcoflow/MF-flowsell-vwapup-rsi5hi.py`, t1s1) | 12:40:30 @248.75 → 13:31:14 @250.17 stop | −9.94 | +0.18 at 13:01 / −1.01 | never worked (fade into a rebound) |
| 9 | XLI short 11 sh | MF5-flowsell-vwapup-rsi5hi | 12:45:47 @167.69 → 14:06:57 @168.31 stop | −6.82 | +0.48 at 13:01 / −1.00 | gave back gains (small) |
| 10 | NOK long 195 sh | NS1-rsidip-rsi5pop-long (`research/owner1008/NS1-…py`, t05s1) | 10:01:08 @9.85 → 10:07:57 @9.87 target | +3.90 | +0.20 / −0.20 | execution: target already consumed by the fill |

---

## #6 FPS: MF2 short, −$16.43 (gave back +1.45R)

**Setup rules and values at entry.** The decision bar was 10:40–10:45 ET.

| rule | threshold | FPS value |
|---|---|---|
| heat | ≤ −30 | **−30.3** (passes by 0.3) |
| RSI(14) | 55–65 | **63.5** |
| buyPressure | < −0.25 | −0.46 |
| time window | 09:50–10:55 | 10:45 |

**The RSI(14) reading was a window artifact.** RSI(14) went from 35.1 to 63.5 in a single bar while price fell from 35.71 to 35.685. MarcoFlow's simple (non-Wilder) RSI dropped the 09:35 opening flush out of its 14-change window. The "mid-high RSI" was therefore not a real overbought state.

**Context:**
- FPS gapped −4.0% after a −7.4% session on 10-12, so the trade went with the trend.
- XLI was −0.64% at entry; IWM was −0.57%.
- Primary's MF1 had already been stopped short on FPS at 10:02 (−$18.54). This trade was a same-direction re-entry 0.06 below that entry.

**Price path:**
- 10:50 low 35.46 (+0.70R).
- 11:05 bounce to 35.835 (−0.55R).
- 11:47 low **35.235 (+1.45R)**. This was the same minute as IWM's day low (11:46).
- Then the market-wide rebound: 12:20 high 36.06, stop filled at 35.98.
- After the exit, FPS reached a high of 36.56 and closed at 36.20 (15:55). The 35.115 target (1.85R from the fill) was never reached.

**Alternatives (replayed on 1-minute bars):**

| exit rule | result |
|---|---|
| actual | −1.0R |
| breakeven after +0.5R | 0.0R (stopped at breakeven 11:07 on the 35.835 bounce) |
| trail 0.5R after +0.5R | +0.23R (11:03) |
| 0.5R target | +0.5R at 10:52 |
| time stop at 60 min (11:46) | **+1.35R** |
| time stop at 30 min | −0.27R |
| wider stop 1.5R / 2R | −1.5R / −2.0R |
| opposite side (long) | would have been stopped |

**What went wrong:** management, not direction. The t1s05 target was 1.85R from the fill, much further than the 1.45R the move gave, and nothing protected the open profit through the 11:46 market turn.

## #7 CVS: NS3 short, −$12.59 (never worked)

**Setup rules and values.** The decision bar was 11:10–11:15.

| rule | threshold | CVS value |
|---|---|---|
| VWAP reclaim | vwapDist > 0, previous ≤ 0 | +0.016% (previous −0.150) |
| price vs 50-bar average | sma50_dist > 0 | +0.18% |
| fromOpen | < −2% | **−2.18%** (passes by 0.18) |
| time window | 09:50–11:30 | 11:15 |

**Context:**
- CVS **gapped +1.64%**, opening at 89.20, then faded to a 86.12 low.
- At entry it was only −0.6% from the prior close of 87.76. The "down 2% from the open" was a gap-fill, not a downtrend.
- The stop (87.80) sat **4c above the prior close**, which is the level price was rebuilding toward.
- XLV was −1.34%, so the sector agreed with a short. Even so, the stock held.

**Price path:**
- Best price 87.15 at 11:17 (+0.18R).
- It held the 87.15–87.46 range through the 11:46 sag, a show of relative strength.
- 12:00–12:05 push to 87.865. The stop filled at 87.85; the one 1-minute close beyond the stop was 87.80 at 12:05.
- After the exit: high 88.16, 15:55 close 87.52. The target (86.72) was never touched.

**Alternatives:**

| alternative | result |
|---|---|
| time stop at 30 min (11:46) | **−0.10R** |
| 2R stop | −0.69R at 15:55 |
| 1.5R stop | −1.5R |
| breakeven / trail / smaller targets | none were ever armed |
| opposite side (long) | would have made +1R at 12:05 with 0.2R heat. Hindsight: the only at-entry hint was the gap-fill geometry, not sector or index |

## #8 AME: MF5 short, −$9.94 (shorting the first VWAP reclaim of a red stock into a rebound)

**Setup rules and values.** The decision bar was 12:35–12:40.

| rule | threshold | AME value |
|---|---|---|
| heat | ≤ −30 | −32.7 |
| buyPressure | < −0.25 | −0.69 |
| vwapDistPct | > 0.05% | **0.059%** (passes by 0.009) |
| RSI(5) | > 70 | 100 |
| time window | 09:50–15:00 | 12:40 |

**Other context:**
- **fromOpen was −0.32%.** AME was still red on the day and had only crossed above VWAP 3 bars earlier.
- **buyPressure −0.69 while price rose** (+0.38% in 30 min, +0.59% in 60 min) means the sell-flow was being absorbed, not leading price.
- XLI (its own sector ETF) was +0.34% in the 30 minutes before entry, part of the 11:46 rebound. The 5-minute ATR was low at 0.145%, a slow grind.

**Price path:**
- Best price 248.52 at 13:01 (+0.18R).
- A steady climb to the stop, filled at 250.17 at 13:31.
- After the exit: high 251.24, close 250.60.

**Alternatives:**

| alternative | result |
|---|---|
| time stop at 30 min | −0.22R |
| 2R stop | −1.55R |
| breakeven / trail | never armed |
| opposite side (long) | +1R at 13:31, with 0.18R heat |

## #9 XLI: MF5 short, −$6.82 (same cluster as AME, 5 minutes later)

**Setup rules and values.** The decision bar was 12:40–12:45.

| rule | threshold | XLI value |
|---|---|---|
| heat | ≤ −30 | −48.4 |
| buyPressure | < −0.25 | **−0.26** (passes by 0.01) |
| vwapDistPct | > 0.05% | **0.055%** |
| RSI(5) | > 70 | 100 |
| RSI(14) | (not a rule) | 90.4 |

**Other context:**
- fromOpen was −0.61%, and price had been above VWAP for only 2 bars. Its own 30-minute return was +0.30%.
- This was a second short on the same industrials move 5 minutes after AME, which is an XLI component. In effect it doubled one bet.

**Price path:**
- Best price 167.40 at 13:01 (+0.48R).
- Then a grind to the stop, filled at 168.31 at 14:07.
- After the exit: high 168.93, 15:55 close 168.665.

**Alternatives:**

| alternative | result |
|---|---|
| breakeven after +0.3R | 0.0R |
| 0.3R target | **+0.3R** at 13:00 |
| time stop at 30 min | **+0.28R** |
| breakeven after +0.5R | not armed (MFE was 0.48R) |
| time stop at 60 min | −0.35R |
| 1.5R / 2R stop | −1.5R / −2.0R |
| opposite side (long) | +1R at 14:06 |

## #10 NOK: NS1 long, +$3.90 (the bracket was set from the bar close, not the fill)

**Setup rules and values.** The decision bar was 09:55–10:00.

| rule | threshold | NOK value |
|---|---|---|
| RSI(14) crosses below 40 | crosses on this bar | 39.98 (previous 42.33) |
| RSI(5) | ≥ 80 | 81.9 |
| fromOpen | > 2% | 2.64% |

**Context:**
- NOK gapped −3.4% after a −4.6% day on 10-12, so the setup bought a gap-fill bounce.
- The setup's two layers contradict each other: RSI(14) falling below 40 while RSI(5) is at 82.

**Execution was the issue:**
- The reference price was 9.8123, the 10:00 bar close.
- The order filled at **9.85 at 10:01:08**, 50 seconds after the decision and **+0.25R** above the reference.
- The bracket was computed from the reference price: target 9.868 (ref + 0.5R), stop 9.70 (ref − 1R).
- Measured from the fill, the live trade was **+0.12R / −1.0R**. It hit the target at 10:07 (MFE only 0.20R).
- A 0.5R target measured from the fill (9.925) was never reached; the day's best price was 9.89. Holding with that target would have ended at −1R (stopped at 11:35).
- The +$3.90 came from reward-to-risk geometry of about 1:8. The positive outcome was luck.

---

## What generalises (testable rule candidates, information known at entry only)

Each candidate below is a backlog hypothesis that must clear the gates: costs in, train/valid, locked holdout scored once. The counts are from today only.

**C1. Fill-anchored bracket / progress skip (execution, NS1 and every setup).**
- Rule: measure progress = side × (fill − ref) / R_plan. If it is ≥ 0.25 for a t05 target (≥ 0.5 for t1), skip the trade, or re-anchor both legs to the fill.
- This extends the existing `nightly-1013-tight-target-progress-skip` idea. Today's case is NOK, at +0.25R progress.
- Test it on the history: entry at the next minute's open versus the bar close.

**C2. RSI window-roll guard (MF2, and any setup using MarcoFlow's simple RSI).**
- Rule: skip if |RSI14 − RSI14[−1]| > 15 while |close change| < 0.2 × ATR5. Alternatively, compute the RSI layers with Wilder smoothing.
- Today's case is FPS: 35 to 63 with price down.

**C3. MF5 "extended, not reclaiming" filter.**
- Rule: require fromOpen > 0 and vwapDistPct ≥ 0.10%, or require price to have been above VWAP for ≥ 6 bars.
- Today it separates 3 winners (HCA +0.38/+0.63%, PBR +1.21/+0.96%, PANW +1.34/+0.13%; fromOpen/vwapDistPct) from the 2 losers (AME −0.32/+0.06%, XLI −0.61/+0.06%).
- **n = 5.** HCA and PBR heat values come from one-day bars (warm-up incomplete).

**C4. Flow/price divergence skip for flow-sell setups (MF1–MF5).**
- Rule: skip a short when buyPressure < −0.25 but the stock's own 30-minute return is > +0.25%. That reading is absorption, not selling.
- Today's cases: AME (+0.38%) and XLI (+0.30%).

**C5. NS3 gap-fill exclusion.**
- Rule: skip when gap > +1% and price at entry is within 0.5R of the prior close. Alternatively, define the "down" layer from the prior close (≤ −1%) instead of from the open.
- Today's case: CVS was −2.18% from the open but −0.6% from the prior close, and the stop sat 4c above the prior close.

**C6. Setup-specific early exit for t1s05 / MF2 (not book-wide).**
- Candidates: a trail of 0.5R once MFE ≥ 1R, or a 60-minute time stop.
- Today, FPS would have made +0.23R (trail) or +1.35R (time stop) instead of −1.0R.
- **Caution:** book-wide exit overlays already failed (`t6-exit-overlay`, `sw-w4-book-exits`, `t1-orb-exits`). This must be tested per setup and against those results.

**C7. Same-sector duplicate cap.**
- Rule: no second same-side entry in a sector-ETF group (ETF plus its components) within 15 minutes.
- Today's case: AME then XLI. This overlaps `window-open-cluster`; the cross-setup cluster cap `loop-1008-exhaustion-cluster-t1` failed. Test it as a sector key, not a time key.

**Not proposed:** an index or sector "rebound" gate.
- A +0.25% sector-ETF 30-minute filter would also have blocked the PANW winner (XLK +0.44%).
- The `ix-gate` backlog item already failed.
- Wider stops lost more in all 4 stop-outs (1.5R and 2R both worse, except CVS at 2R, which was −0.69R).
- The opposite side won in 3 of 5 (CVS, AME, XLI), but only with hindsight. No at-entry rule today pointed long, beyond what C3 and C4 capture.

## Counts and caveats
- 5 trades analysed, from 1 session.
- 11 exit variants replayed per trade on 1-minute bars (stop/target touch order within a minute is approximated by stop first).
- 7 candidates. None has been tested, and none implies an edge.
