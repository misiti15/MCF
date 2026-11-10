# stoplab VERIFY: skeptic's review of studies A, B, C

*Educational only — not financial advice.* These are live paper results (2026-10-06..11-09) plus 2-year lab backtests, with costs in. This page is a review only: nothing in config/, mcf/, setups, exits or the ledger was changed. The locked block 2024-11-01..2025-02-28 was not read.

**Bottom line.** The overall answer holds up: **keep -2.0R and keep k = 1.0.** Every headline number I re-ran matched to 0.1R. All three "leads" are weaker than their write-ups say, so none of them should move a setup. The main thing to correct is how the answer is framed. The daily stop is mainly a lever on *how much of a losing setup gets traded*, not a measure of stop quality. So "what is the best level" really depends on the setup's expectancy, and on 25 sessions we cannot measure that per setup.

## 1. Re-runs (independent of the study scripts)
| Figure | Study says | My re-run | Method |
|---|---|---|---|
| Book total at off / -2.0 / -1.0 | -2,703 / -1,850 / -1,546R; 22,543 / 15,363 / 12,886 trades | **-2,702.9 / -1,850.0 / -1,545.8R; 22,543 / 15,363 / 12,886** | My own replay from `trades.csv.gz` (run_id 1 + latch what-ifs, halt what-ifs out, trigger on realised r_multiple of trades exited at or before entry). The A replay is reproduced exactly. |
| A: -1.0 vs -2.0 on validate | +110.1R, t 2.39 | +110.1R, t 2.39 (17 dates) | From `units_main.csv.gz`, t clustered by date |
| A: -1.5 / -1.75 / -2.25 / off / give-back 1.5 | +14.6 / +13.8 / -90.6 / -459.0 / +83.0 | same | same |
| A: gap-down shorts, off vs -2.0 | +112R all sessions, +47R validate (t 2.14), 58% on 10-22 | +111.5 all, **+46.6 validate (t 2.14)**, 10-22 = +65.1 | same |
| B: TRAIN-positive setups whose best k ≠ 1 | 45, of which 17 improve and 28 worsen on VALID | 45 → 17 / 28; 0 pass; 13 pass_study on total d | `lab_setup_k.csv` |
| C: T15 b0.5 | +196.3 all, validate +28.6 (t 0.30), winning setups -233R | +196.3, +28.6 (t 0.30), winners -232.7, losers +429.0 | `trades_c12.csv.gz` |
| C: G m1.0 g1.0 | validate +7.0 (t 1.44) | +7.0 (t 1.44); **on winning setups -6.4R** | same |

There are no arithmetic or replay errors. The problems are in how the results are read, not in the numbers.

## 2. Verdicts on the headline claims

### A1. "-1.25..-2.01 is one flat plateau; -1.6 / -1.75 / -1.8 / -2.01 are the same as -2.0": **CONFIRMED**
- Validate deltas are +8..+15R with |t| ≤ 0.67.
- 90%+ of the -1.5 and -1.75 gains come from one validate day. Without that day they are +1.4R and +1.1R.
- -2.01 differs from -2.0 in only 4 setups, so there is no information in it.
- **What would change it:** nothing realistic. At this size of effect it would take hundreds of sessions to separate the levels.

### A2. "Looser (-2.25..-4) is worse": **CONFIRMED for today's book, but it is not a stop-quality finding**
- The extra trades that a looser level allows are mostly latch **what-ifs**, which are flattering. Their average R is -0.072, against -0.133 for live trades, because they carry backtest costs and ignore other blocks. Even so, looser is still worse, so the bias makes the conclusion conservative.
- The mechanism is "trade more of a negative-expectancy book". In the lab the *excess* for looser levels is positive (up to +795R VALID at -4.0). Positive-expectancy lab setups lean towards off/looser (+86R VALID, t 2.3, 13 up / 4 down).
- So "looser is worse" is true **because most setups lose**. It does not show that -2.0 is the right stop for a winning setup.
- **What would settle the winning-setup case:** a forward shadow of off vs -2.0 on setups that are positive on ≥ 20 live trades, judged per setup over 15+ new sessions.

### A3. "-1.0 beats -2.0 by +110R but fails": **CONFIRMED that it fails; the gain is real but carries no timing information**
- t 2.39 is below the bar. The bar should now be **2.96 (N = 79 after C)**, not the 2.88 that A quotes.
- -1.0 is at the edge of the grid, and its excess is about 0 (+6R; -776R on the 2-year VALID).
- **Day concentration.** 4 validate dates (11-04, 11-05, 11-06, 11-09) give +90R of the +110R (82%). 11-04 alone is 37%. Without 11-05, 11-06 and 11-09 it is +61R. 7 of the 17 validate dates contribute exactly 0.
- **Market and regime confounding.** The daily -1.0 vs -2.0 delta correlates at **-0.67** with the book's daily R at off. Tighter levels win on the days the whole book bleeds. That is mechanical, but it means the result depends on how many bad days fall in the window, and the validate window ends on the three big days the brief flags.
- **Leakage.** The split is per setup, not by calendar. So "choose" days for new setups (late Oct to Nov) are the same calendar days as "validate" for old setups. The global CHOOSE pick therefore sees validate-period market days. This is minor, but it inflates the global result.
- **What would settle it:** a calendar split, with all choosing done on dates ≤ 10-31 and scoring on later dates only. The real fix is setup-level (cut or fix the losing setups), not the stop level.

### A4. "Per-setup levels do not hold up (0 of 111)": **CONFIRMED**
- 84 setups each chose from 12 levels on 3-15 choose sessions. Validate improves in 24 setups and worsens in 15, net -45R. As a whole-book rule it scores -34R.
- This is what pure noise looks like: the expected maximum t over 12 levels × 84 setups under the null is about 3.4.

### A5. "Gap-down shorts, stop off: +47R validate, backlog shadow": **PLAUSIBLE-BUT-THIN, and weaker than written**
- The write-up says the one-big-day flag is 10-22 (58%). That is the *all-session* figure, and 10-22 is a CHOOSE day. The **validate** +46.6R rests on only 4 positive dates out of 9 (11-05 +19.3, 10-30 +11.3, 11-06 +10.7, 11-03 +6.9). 11-05 + 11-06 = 64%.
- **Of the +111.5R total, +84.2R comes from latch what-ifs, not live fills.** +51.4R of that is 105 what-if trades on one day in one account (10-22, Testing 1, RW7-FD). Those trades carry backtest costs and were never checked against the symbol and lot caps. The live-fill part is only about +27R.
- 15 family rows × 13 levels were searched, so a t of 2.14 for the best one is within noise.
- **What would settle it:** a forward shadow (no live change) on RW1/3/3S/5/7-FD and CWT09, scored on live fills only, for 15+ sessions with no single day above 40% of the gain.

### A6. "Give-back G = 1.5: +83R, fails": **CONFIRMED**
- t 1.47, validate excess -27R, and 57% of the gain on the best day.

### B1. "Wider stops look better in the lab, but it is size": **CONFIRMED**
- The size-only control is the right test. The stop effect is +0.003..+0.006R, about 0 on SPY-down days, and appears only on up days. That is a market-direction effect, not a stop edge.
- It matches the Guild's STOPW result from an independent harness.

### B2. "Tighter (0.75 / 0.9) is worse": **CONFIRMED in the lab, UNSETTLED live**
- The live approximation cannot judge tighter stops. 2,668 of 6,708 stop exits show bar-mark mae_r > -1, so tight stops look better than they are.

### B3. "Per-setup k choice is noise": **CONFIRMED**
- 45 TRAIN-positive setups → 17 improve / 28 worsen on VALID. 69 + 15 of the TRAIN picks sit at the grid edges.
- Live choose→validate sign agreement is at chance level.

### B4. "L3-gap-slope-fromopen-FD at k = 1.5 is a lead": **PLAUSIBLE-BUT-THIN, closer to noise**
- It is the best of 119 setups × 5 k. The stop-effect t of 2.52 is below the 2.96 bar and below the null expectation for the top of 119 (about 3.1).
- k = 1.5 is the grid edge. The "plateau" is a monotone ramp from 0.75 to 1.5.
- **VALID avg R at k = 1.5 without its best day is -0.0012.** So "turns positive on both splits" fails the one-big-day rule.
- The live approximation points the other way (-0.10R at k = 1.5).
- **What would settle it:** the B1 1-min live re-walk with the parity gate, plus a k = 1.75 / 2.0 lab row to see whether the ramp keeps going (in which case it is size or regime, not a stop edge).

### C1. "Open-loss latch fails; its gain is from trading losers less": **CONFIRMED**
- Excess is -50..-56R at every k, and it does worse in Primary at every k.
- The "winning setups" figure (-28R) uses the CHOOSE split to define winners, so it has some selection bias. The validate-only view is what counts there, and it is flat.

### C2. "Time stop fails": **CONFIRMED**
- Live validate t is ≤ 1.83 (T90 b0.25, the best of 12). Lab VALID is negative for every b > 0.
- The winning-setup cost (-233R) is mostly CHOOSE-defined and in-sample (-238R on choose). Read it as "it cuts winners' right tails", which the lab confirms (86 of 117 setups worse).

### C3. "Break-even after +1R (G m1.0 g1.0) is a lead for hold setups": **PLAUSIBLE-BUT-THIN**
- It fires on only 2% of trades, validate is +7R (t 1.44), and the g = 0.5 neighbour is negative.
- **It is -6.4R on winning setups.** All of its gain comes from losing setups, so it is the same "trade losers less" mechanism.
- The C live window ends on 11-04, so it does not include the 11-05 / 11-06 / 11-09 days at all.

## 3. Cross-cutting issues
- **Config count is lenient, but this does not matter for the verdict.**
  - A3 (12 levels × 84 setups) counts as 1 configuration and B3 (5 × 119) as 5.
  - Counting honestly would raise the bar well above 3, so nothing passes either way.
  - It *does* matter for the leads: each one is the maximum of a large search, and its t sits where the null maximum would be.
- **Double counting across accounts is negligible.** Only 38 of 1,552 setup-dates appear in more than one account, and the t-tests are clustered by date.
- **What-ifs.** These are used correctly as the trades a latch removed. But they are rosier than live fills (-0.072 vs -0.133 avg R), so every off/looser figure is optimistic. 45% of the Graveyard sequence is what-ifs.
- **Different windows.** A runs to 11-09, C live to 11-04, and B's live approximation for k > 1 to 11-04. A level that looks good in one study and a variant that looks good in another were not judged on the same days.
- **Rule changes inside the window** (ledger): the per-setup stop was on in T1/T2/Gen 10-19..10-22 and then off from 10-23 (ST-A); the Graveyard has had -2R since 10-21; Primary has had the latched -2R since 10-29 (ST-P). Other changes: Primary size ~$5k then ~$4k from 10-28, BAR90 10-29, the CF filter 10-30, R2A 11-03, ROLL1 11-05 and EXPO1109 11-09. The replays hold the trade list fixed across levels, so these changes move the sample, not the comparison.
- **Primary, the account that runs the rule:** 8 sessions since 10-29. -1.0 gives +8.8R (t 1.1) and off gives -5.2R. That is noise.

## 4. What the synthesis should say
1. Keep -2.0R. Use 2.96 as the bar, not 2.88.
2. Levels from -1.25 to -2.01 cannot be told apart on this data. Looser levels add losing trades. -1.0 "wins" only by trading losing setups less, and 82% of that gain sits on 4 recent days.
3. The real lever is setup expectancy. A per-setup daily stop cannot be fitted on ≤ 25 sessions.
4. Backlog ideas, as forward shadows only:
   - gap-down shorts with the stop off, scored on **live fills only**, noting that 75% of the current gain is what-ifs;
   - L3-fromopen-FD at k = 1.5, via the B1 re-walk;
   - break-even after +1R for hold geometries.
   None of them should be presented as near passing.
5. A calendar-split re-check (choose ≤ 10-31) would close the leakage point for A.

*Educational only — not financial advice.*
