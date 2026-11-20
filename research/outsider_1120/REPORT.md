Educational only — not financial advice

# MCF outsider pressure test: final report (data to the 11-19 close, written 2026-11-20)

## Owner summary
- **Where MCF stands:** the plumbing works, but there is no edge yet. 28,097 live trades averaged -0.125R after costs (-3,500R). Only 3 of 33 sessions were green. No week was positive, and nothing shows the results converging.
- **Concern 1, no selection skill:** a setup's live rank in one period does not predict its rank in the next (Spearman -0.11; last-10 vs next-10 r = -0.01). Promotions and demotions on live records have so far been picking noise.
- **Concern 2, no null and an undercounted N:** the 10 "positive without best day" survivors are fewer than a fair no-edge null predicts (~13). The t-bar uses N per lineage, but about 20M configurations have been tried across the program.
- **Concern 3, churn and sprawl:** 236 ledger entries in 7 weeks. No setup has 20+ trades under today's rules. Volume has doubled, and that extra volume is the main reason daily R is getting worse.
- **Proposed change of direction:** stop adding volume, setups and rule edits for one clean epoch. Judge setups only by pre-registered tests against a matched random-entry null, and put research effort into entry selection. Exits have been tested thoroughly and are not the lever.

## Scorecard

| ID | Theme | One-line answer | Verdict | Severity |
|---|---|---|---|---|
| Q01 | Convergence | Per-trade loss within fixed setups improved slightly (-0.169→-0.113R, t≈1.1, not significant); daily R got worse (-76→-145R/day); rank persistence -0.11 | confirmed | critical |
| Q02 | Payoff asymmetry | 0.5R targets vs ~1.06R losers; 1,170R (33% of the loss) lost beyond the stop; wider targets failed in 3,836 configs | partly | high |
| Q03 | Multiple testing | Bar uses N per lineage; program N ≈ 2e7 → t 5.8; best live setup t 3.50 | confirmed | high |
| Q04 | Null benchmark | No live null was ever run; a fair null gives ~13 survivors vs 10 observed | confirmed | critical |
| Q05 | Power | 22/101 Testing setups can confirm +0.15R this quarter; negative verdicts come much faster (23 have upper bound <0) | confirmed | high |
| Q06 | Too many setups | Thin setups cost ~2% of trades; the waste is high-rep losers; top-20 picks did not persist | partly | high |
| Q07 | Kill criteria | No permanent retirement rule exists; 0 setups retired; 18 archived 11-19 | confirmed | high |
| Q08 | Graveyard value | 0 rescues reached Primary; 2 exits, both resting on one day | confirmed | medium |
| Q09 | One-day dependence | Best days fall on 7 different sessions (not one bet), but the basket is -27R without 5 cluster days | partly | high |
| Q10 | NM-ETF-late-dip | t 2.9–3.5 on 15 days; fails Bonferroni ×220; not sized up; recent form flat | partly | high |
| Q11 | Backtest vs live | The gap comes from which trades are taken (40–100% symbol-day overlap), not fills; replay counts 0 toward promotion | partly | high |
| Q12 | Fill realism | Calibrated only against paper; real money likely 0.03–0.05R worse (touch-only targets) | partly | high |
| Q13 | Costs | Gross is already -0.095R before costs; costs ≈ 0.056R (LR8); a 0.08R cost cap adds ~7 positive setups | partly | high |
| Q14 | R definition | R = stop distance at entry, stable; dollars per R vary a lot; trade R and account R can have opposite signs | partly | high |
| Q15 | Stop rounding | No inverted stops; rounding caused ~1.8% extra stop-outs, worth ~+0.016R; no verdicts flip | partly | low |
| Q16 | Rule churn | 0 setups with 20+ trades under current rules; only Primary has a freeze plan | confirmed | high |
| Q17 | Regime | Loses in every regime; a hindsight direction gate only reaches -0.051R; pre-open gates reach ~-0.09R | partly | high |
| Q18 | Duplication | 41.7% of trades clash with another setup; effective N ≈ 13 of 63; families plus a long/short factor | partly | high |
| Q19 | Arena overhead | ~16–24% of commits go to account machinery; tags in one account would give about the same information | partly | medium |
| Q20 | Rotation | Benching cost good setups 0R (it rested losers); rotation has produced 0 verdicts | partly | medium |
| Q21 | Yield by source | Not measured; 7 of 10 positives came from in-house swarms; the top-5 tune loop is 0/378 | confirmed | high |
| Q22 | Admission bar | Top-10 standard is relative (admits negative backtests); a positive-history bar would have rejected L3 | partly | high |
| Q23 | Stocks in play | In-play -0.104R vs rest -0.136R (t 1.48, day-paired); a top-50 list is still negative | partly | medium |
| Q24 | Time of day | Losses are worst 09:50–10:30 (-0.176R); a midday ban is a coin flip (48/45) | partly | medium |
| Q25 | Shorts/borrow | Shorts -0.099R, longs -0.143R; ETB gated; no locate fee and no SSR handling | partly | medium |
| Q26 | Execution delay | ~36 s from bar close to fill; ~+0.02–0.04R slippage; limit entries tested once and failed | partly | medium |
| Q27 | Data feed | SIP in both live and backtest; ~0.2% of trades possibly hit by bar revisions (3-session sample) | partly | low |
| Q28 | Brakes | Brakes are per account only; no automatic system-wide stop; Gen setup lost -134.6R on 11-17 with no brake | partly | high |
| Q29 | Frequency | First-signal-per-symbol filter -0.136R; prior-ranked top-50 -0.19 to -0.22R; only a hindsight rank is positive | partly | high |
| Q30 | Capital realism | $50k at 1% risk takes ~25 trades/day (3%); capped books lose part of the edge on good days | confirmed | high |
| Q31 | Common exits | Done: 3,836 exit configs, 0 pass; one narrow pass (RW3/RW5 1.25× target, +0.044R) | unfounded | medium |
| Q32 | Last-10 trend | Last 10 trades do not predict the next 10 across sessions; same-day persistence is real (r 0.35) | partly | high |
| Q33 | Tuition vs production | 97.5% of the loss is outside Primary; Primary +70R after promotions, not proven | partly | high |
| Q34 | MarcoFlow lessons | Mechanical failures fixed; strategic ones (sprawl, churn, overfit) repeating at ~10× volume | partly | high |
| Q35 | Move Hunt | 64% of tradable top movers touched, 13.7% caught right side; wrong-direction trades on them -169R | partly | high |
| Q36 | Concentrated book | Hindsight +231R; walk-forward top-10 lost at all 3 cut dates | partly | high |

Totals: 2 critical, 24 high, 8 medium, 2 low. Verdicts: 9 confirmed, 26 partly, 1 unfounded.

## Top concerns (critical/high, grouped)

**1. No selection skill, no null, undercounted N (Q01, Q03, Q04, Q09, Q10, Q22, Q32, Q36)**
- **Evidence:**
  - Rank persistence: Spearman -0.107 (58 setups). First-half leaders averaged -0.086R in the second half; all others -0.100R.
  - Last-10 vs next-10 trades: r = -0.014. Whole record to date vs next 10: r = -0.016.
  - Walk-forward top-10 lost at every cut (-0.256 / -0.138 / -0.088R per trade).
  - Null D (each setup's own payoff shape, no edge) predicts 13.1 survivors vs 10 observed.
  - Program-wide N ≈ 2e7 puts the bar at t 5.8. Only NM-ETF clears even the live-program bar (t 3.50 vs 3.28 at N=220).
  - The 10 survivors are about 5–6 independent bets. Together they are -27R without 5 cluster days.
- **Targeted improvement (research):**
  - Build a live-equivalent random-entry null per setup: same symbols, entry minute ±30 min, side, stop/target geometry, LR8 costs, 200+ reps.
  - Keep a global try-count register and show three t-bars (lineage, live program, cumulative).
  - Pre-register a convergence test: fixed panel, out-of-sample rank correlation, leaders vs random picks.
  - Calibrate the admission bar against live outcomes, including a "beats random by ≥0.03R" leg.

**2. Churn: rules, volume and setups (Q01, Q16, Q34, Q05, Q06)**
- **Evidence:**
  - 236 ledger entries, 92 of them effective on or after 11-12. Busiest days: 11-17 (29), 11-19 (27).
  - No setup has 20+ trades under the current rules.
  - Trades/day of common setups rose 450→735; new setups lose -0.142R per trade.
  - 140 of 220 setups have traded in more than one account.
  - The 30-trade bar can only detect edges of about ±0.35R (clustered SE ≈ 0.18R).
- **Targeted improvement (owner approval needed):**
  - Apply C3-EPOCH to all accounts for 11-23..~12-18: no edits to costs, sizing, caps, stops or filters. Rotation and Friday moves are the only levers; real bugs can still be fixed (BROKEN exception).
  - Write the epoch id on every journaled trade.
  - Pause growth in volume and admissions during the epoch.
  - Backtest a sequential clustered-SE retirement/flag rule.

**3. Losers that never die, and missing brakes (Q07, Q06, Q28, Q29)**
- **Evidence:**
  - 0 permanent retirements in 7 weeks.
  - Enabled losers made -1,049.7R over the last 10 sessions, about 79% of the net loss.
  - Graveyard losers made -668R over the last 10 sessions.
  - High-rep losers total -3,843R, against +375R for the winners.
  - On 11-17, one Gen setup lost -134.6R over 144 trades with no brake firing.
  - The Graveyard closed 11-17 at -177R against its 120R halt.
  - There is no automatic system-wide halt.
- **Targeted improvement:**
  - Backtest a RETIRED state with a hard floor (e.g. ≥150 trades, w/o-best-day avg ≤ -0.10, day t ≤ -2.5). Report how many later graduates it would have killed by mistake.
  - Replay a cost-in system-wide stop, sweeping 150–400R.
  - Test applying the LR3 cost-in basis to all account halts.
  - Test the -2R per-setup latch in Gen and Testing.
  - Report per-setup better/worse for each brake.
  - Switch the watchdog to "act" in all accounts before any real money (checklist item).

**4. Measurement realism: costs, fills, R units, capital (Q02, Q11, Q12, Q13, Q14, Q30, Q33)**
- **Evidence:**
  - Gross R is -0.095 before costs: 95 of 135 setups are negative before any cost.
  - 1,170R was lost beyond the 1R stop.
  - Touch-only target fills are worth about +0.035R of hidden cost.
  - The cost model has never been checked against a real fill.
  - A $50k account at 1% risk takes 3% of signals.
  - In SIZE1, the cap cut the best book from +0.284R to +0.155–0.20R.
  - The live-minus-backtest gap comes from which trades are taken, not fills.
  - The -3,500R headline mixes research spend with Primary (-87.5R).
- **Targeted improvement:**
  - Run the deferred LR15 NBBO check after the close (300–600 fills, overweighting leveraged ETFs and fast stops).
  - Decompose losses beyond the stop by account, setup and minute.
  - Test a 0.08R ex-ante cost cap out of sample (in sample it raised net-positive setups from 26 to 33 of ~113).
  - Reconcile live vs lab trades per setup.
  - Run a nightly one-real-account shadow book.
  - Publish a Primary-only, after-promotion production scoreboard as the North Star line.

**5. Upstream selection and timing (Q35, Q17, Q18, Q23, Q24)**
- **Evidence:**
  - 64% of tradable top movers were touched, but only 13.7% caught on the right side and in time.
  - Wrong-direction trades on those movers: -169.5R.
  - Longs lose -0.27R on down days; shorts lose -0.29R on up days.
  - The first principal component of daily setup R is mostly the long/short split (loadings correlate 0.83 with side).
  - 09:50–10:30 entries average -0.176R.
  - In-play +0.03R, not significant.
- **Targeted improvement (research only):**
  - Test a 10:30 regime gate (SPY or universe vs VWAP plus open-to-10:30 return), per-setup scored.
  - Test a no-entry-before-10:30 variant only for setups that lose at the open in both halves.
  - Run an opening-rvol study across the full universe.
  - Score setup entries on the "on deck" mover list, split by miss reason.
  - Track wrong-direction R as its own loss category.

## What is working
- **Exits have been tested thoroughly (Q31):** 3,836 configs, 0 pass, skeptic upheld every FAIL. Effort can move to entries. Narrow salvage: the RW3/RW5 1.25× target (+0.044R, t 2.58).
- **Mechanics are sound:**
  - SIP in both live and backtest (Q27).
  - Deterministic order IDs and dedupe (Q28).
  - No inverted stops; the rounding bug was small (~+0.016R) and no verdict flips (Q15).
  - Entry delay ~36 s, costing ~0.02–0.04R per trade (Q26).
  - Matched-trade replay bias +0.005R (Q11).
- **Rotation has not hurt the best setups (Q20):** benching rested only losers, likely avoiding ~100–190R (estimate, not measured).
- **Breadth is cheap (Q06):** setups with fewer than 20 trades use ~2% of trades (-32R).
- **Shorts look better than longs (Q25):** 22 of 71 short setups positive vs 7 of 67 longs. The short record does not lean on illiquid names.
- **Losers resolve fast (Q05):** 23 setups already have a 95% upper bound below 0, so slots can be freed within the quarter.
- **Candidates worth saving:**
  - NM-ETF-late-dip: t 3.5, best day 21% of R. Last 10 trades flat.
  - L3-gap-slope-fromopen: +0.148R without best day over 403 trades. It held up walk-forward.
  - The RW3/RW5 gap-down short core.
  - GEN-03 and CWT09: positive outside the cluster days, but on only ~42 trades between them.
  - In Primary, the current 5 have made +70R over 556 trades since promotion. RW3 and RW5 get ~75% of their R from one day (one-day flag).
- **Ideas where the effect is real but small:**
  - The same-day persistence effect (r 0.35) is real; logged as an R-remedy backlog idea.
  - The gap-size trend in in-play names (-0.158R → -0.060R).

## Proposed decisions (owner)
1. **OUT-EPOCH — one clean rule epoch for all accounts, 11-23..12-18.**
   - Recommend: YES. No rule edits; rotation and Friday moves only; bug fixes allowed; epoch id stamped on each trade; volume and admissions held flat.
   - Why: no setup currently has a clean sample, and growth in volume is the main driver of the worsening daily R.
2. **OUT-NULL — matched random-entry null as the promotion screen.**
   - Recommend: YES (research build first). Until it exists, use null D on LR8 data from 11-12. Show it next to the existing one-big-day column.
   - Why: the survivor count is no better than noise, so raw "positive without best day" is not evidence.
3. **OUT-NMETF — pre-registered single-setup forward test for NM-ETF-late-dip.**
   - Recommend: YES. About 25 sessions with rules frozen. Bar: one-sided day-clustered t ≥ 2 and w/o-best-day avg > 0. Size rule committed in advance (e.g. 0.25%→0.5% on pass). Stays at 1× until then.
   - Why: it is the only candidate above the live-program bar and is not driven by one day, but it is still not separable from the best of 220 noise draws.
4. **OUT-RETIRE — terminal RETIRED state, backtested before adoption.**
   - Recommend: YES to the study; adoption to be decided on its results. Distinct from low-activity trims, which still go to testing under the 11-03 rule. The study must report wrongful kills of later graduates.
   - Why: losers are effectively immortal and make up ~79% of recent net loss.
5. **OUT-BRAKE — system-wide cost-in stop study, plus watchdog "act" in all accounts as a pre-real-money item.**
   - Recommend: YES (research replay; per-setup better/worse reported).
   - Why: on 11-17 no brake applied to a -134.6R Gen setup, and the per-account halts count raw R before costs.
6. **OUT-SCORE — Primary-only, after-promotion production scoreboard as the North Star line.**
   - Recommend: YES. Rule-change epochs marked on the chart; Testing/Gen/Graveyard shown as "research spend". Pre-declared pass/kill bars for the current 5.
   - Why: the -3,500R headline is 97.5% exploration and hides whether a deployable book exists.

Not recommended:
- **Default stacking cap:** the one-entry-per-symbol cap (Q18) stays a research study only.
- **Blanket midday ban:** a coin flip per setup (48 improve, 45 worse).
- **Book-wide target widening:** already failed in the exit study.
- **Cutting Reddit or owner idea sources:** samples too small. Cap the top-5 execution-tune loop instead (0 of 378 reached testing).
- **In-session throttling as a starvation fix:** starvation stays a session-rotation matter.

## Rule-change context (applies to all live figures)
- **Window:** 10-06..11-19, with about 227–236 ledger entries effective inside it.
- **Key dates:**
  - 10-20/22: per-setup -2R latch introduced, then turned off in Testing/Gen.
  - 10-28/29: Primary resized to ~$4k positions; Primary -2R latch.
  - 10-30: Testing 0.15R cost filter.
  - 11-12: 10-account restructure, LR8 cost basis (DQ-P3 restates earlier trades about 0.04R lower), REPV caps and buying power.
  - 11-16/17: ROT1 rotation, TSZ1 half-size testing lots.
  - 11-18: GY-BENCH.
  - 11-19: C3 Epoch 1, EXIT100, GY-ARCHIVE-20.
- **Not in the data:** the 11-20 stop rounding, inverse guard (shadow only), FOOTRACE-EXIT and testing admissions.
- **Comparability:** no before/after comparison above is like-for-like across these changes.

## Count
- **Questions:** 36. **Answered:** 36, all with repo or data evidence.
- **Fresh computations:**
  - About 31 of 36 answers include them, mostly on live_trades.pkl (28,097 trades), the journals (≈22–28k trades), setup_stats.pkl and the backlog/ledger.
  - Explicit variants scored by investigators: ≈45. These include Q13's 11 cost/stop filters, Q04's 4 nulls × 300 reps, Q17's ~7 regime gates, Q23's ~8 in-play cuts, Q24's 3 time windows, Q29's ~8 selection filters and Q30's ~6 capital replays.
  - All are in sample on live data. None is a validated result.
- **Cited prior research (not re-run):** giveback_1119 (3,836 configs), SIZE1 (200), bdi1013 limit entries (957), and the 27,228-spec generator screen.

---

## Appendix: full Q&A

**Q01 Convergence.**
- **Q:** Is daily R in weeks 5–7 better than in weeks 1–2 with the setup mix fixed? What shows convergence?
- **A:** Only marginally better per trade, and not significant. Total daily R got worse. Live rank does not persist, so the process is churning.
- **Evidence:**
  - Fixed mix (77 setups): -0.169→-0.113R per trade. With weeks 1–3 as "early": -0.117→-0.112.
  - Welch t ≈ 1.13; slope +0.0009R per session.
  - R/day -76→-145; new setups -0.142R per trade.
  - Half-to-half Spearman -0.107.
- **Improvement:** pre-registered fixed-panel convergence test (out-of-sample rank correlation, leaders vs random). Pause growth in volume.

**Q02 Payoff asymmetry.**
- **Q:** Why are losers ~1R and winners well under 1R?
- **A:** The 0.5R-target / 1R-stop design (71% of lab trades), plus slippage and costs on stops. Expectancy would be about +0.21R if the median winner reached 1R at the same win rate, but further targets cut the hit rate about as much as they raise the payoff.
- **Evidence:**
  - Win rate 52.3%; avg win +0.586R; median loss -1.057R.
  - 9,422 trades lost more than 1R, giving up 1,170R beyond the stop.
  - Break-even win rate at today's payoffs: 60.6%.
  - giveback_1119: 0 of 36 family-sides adopted any target change.
- **Improvement:** decompose losses beyond the stop (slippage, costs, rounding); test GB-GENTRAIL on GEN hold setups in research only.

**Q03 Multiple testing.**
- **Q:** What is the cumulative N, and is the bar global?
- **A:** The bar uses N per lineage. The cumulative N is about 2e7, which puts the bar at t 5.8.
- **Evidence:**
  - RESEARCH_RULES rules 19, 22, 30 and 33 define N per lineage.
  - Callers hard-code N (9 to 200).
  - Generator setups have no t-bar at all.
  - Best live setup: t 3.50 (NM-ETF), whose lineage N is unknown.
- **Improvement:** global try-count register; show three bars per setup; deflated Sharpe.

**Q04 Null benchmark.**
- **Q:** How does 10/142 compare with random entries?
- **A:** A live null was never run. The fair null gives ~13, so 10 is noise-level.
- **Evidence:**
  - Null A: 5.3 survivors (P(≥10) = 0.04). Null B: 5.5.
  - Null D: 13.1 (P(≥10) = 0.83).
  - Null C at a -0.05R pool mean: 26.5.
- **Improvement:** matched random-entry null as a standing leaderboard column; promote only on the difference.

**Q05 Power.**
- **Q:** How many sessions until each setup reaches a verdict?
- **A:** A typical Testing setup needs ~146 active sessions (~7 months) for +0.15R. Losers resolve much faster.
- **Evidence:**
  - Trade SD 0.872; same-day ICC 0.20; design effect 1.44.
  - Quarter: 22 of 101 Testing setups can confirm at +0.15R, 1 of 101 at +0.1R.
  - 23 setups have a 95% upper bound below 0.
  - 27 enabled setups have zero trades.
- **Improvement:** backtest a sequential clustered-SE retire/flag rule; size the arena to what can resolve.

**Q06 Too many setups.**
- **Q:** Why 215 setups rather than the top 20?
- **A:** Thin setups are cheap. Top-20 picks did not persist. The waste is high-rep losers.
- **Evidence:**
  - Fewer than 20 trades: 2% of trades, -31.8R.
  - Top 20 after the cut: -0.082 and -0.064R per trade.
  - Losers with 20+ trades: -3,843R.
  - Graveyard: 35% of trades.
- **Improvement:** point-in-time retirement study on high-rep losers; measure the reps needed before records persist.

**Q07 Kill criteria.**
- **Q:** What rule turns a setup off for good?
- **A:** None. 0 setups retired; archive is revivable.
- **Evidence:**
  - Rule 20 (retirement is the owner's decision after 10 more sessions); rule 29 (archive is never retirement).
  - 18 archived 11-19 had cost -1,621R before the cut.
  - Enabled losers made -1,049.7R over the last 10 sessions (~79% of the net loss).
- **Improvement:** RETIRED state with a hard floor; Graveyard at reduced risk or shadow; backtest wrongful kills first.

**Q08 Graveyard value.**
- **Q:** Has any rescue reached Primary?
- **A:** No. 2 exits (RW6, ST4), both resting on one day.
- **Evidence:**
  - Graveyard: 9,700 trades, -1,177R; 2 of 22 sessions positive.
  - The 18 archived setups made 82% of the Graveyard loss.
  - The remaining 33 run at -0.061R per trade.
- **Improvement:** one pre-written rescue rule with an expiry; rescue rate shown on the dashboard; re-assign capacity if still 0 after one more cycle.

**Q09 One-day dependence.**
- **Q:** Do the survivors share the same big day?
- **A:** No. Their best days fall on 7 different sessions (mean pairwise r 0.14). But the basket depends on 5 sessions.
- **Evidence:**
  - Basket +231.5R; without the top 5 days -27.4R over 1,468 trades.
  - Outside those days only GEN-03, CWT09 and NM-ETF hold (~82 trades in total).
  - 9 of the 10 are shorts or fades.
- **Improvement:** cluster view (avg R without shared cluster days); count correlation ≥0.7 groups as one bet.

**Q10 NM-ETF-late-dip.**
- **Q:** Clustered t, Bonferroni, sizing?
- **A:** t 2.9–3.5 on 15 days. Fails Bonferroni ×220 (needs t ≈ 4.4). Flat 0.25% risk.
- **Evidence:**
  - n=33, +0.212R; +0.185R without best day; best day 21%.
  - Last 10 trades -0.007R.
  - 2-year validation period only +0.002R.
- **Improvement:** pre-registered ~25-session confirmation test with a size rule committed in advance.

**Q11 Backtest vs live.**
- **Q:** Where does the gap come from? Is the backtester trusted?
- **A:** The gap is about which trades are taken, not fills. Replay is trusted for mechanics only; the 2-year lab has not predicted the live winners.
- **Evidence:**
  - Live minus backtest +0.09R (selection-biased top 10).
  - Symbol-day overlap 40–100%.
  - Replay matches 87% of live trades, with 26% extra; matched bias +0.005R.
- **Improvement:** per-setup reconciliation (both / live-only / lab-only); fix replay quotes using recorded spreads.

**Q12 Fill realism.**
- **Q:** Is the cost model checked against real fills?
- **A:** Paper only. Real money is likely 0.03–0.05R worse.
- **Evidence:**
  - Calibrated on SIP bars over 4 sessions; LR15 not done.
  - Paper stop fills already 4.6 bps beyond the stop.
  - 11.1% of target fills were touch-only (+0.035R hidden cost).
  - SOXL/SOXS/APLD are 1.3% of trades.
- **Improvement:** NBBO check after the close; tiered stop allowance; small real-money calibration with owner approval.

**Q13 Costs.**
- **Q:** What share of the loss is costs? What is gross R?
- **A:** Gross is already -0.095R. Costs make it worse but do not cause it. A cost cap helps modestly.
- **Evidence:**
  - Costs 0.056R (LR8), about 37% of the net loss.
  - Costs flip 12 setups, all of them marginal.
  - 0.08R cap: 33 vs 26 setups positive; 69 improve vs 31 worse.
  - 11 configs tried, in sample.
- **Improvement:** test a 0.08/0.10R CF extension out of sample on 2-year lab signals; focus on gross entry signal.

**Q14 R definition.**
- **Q:** How is 1R defined, and is it comparable?
- **A:** 1R is the stop distance at entry, and that definition is stable. Dollars per R vary, and tight stops pay much more cost per R.
- **Evidence:**
  - The slot cap sets size on almost every trade.
  - 11-12..11-18: -145R per session but +$21 per session.
  - $0.02 minimum stop cost = 0.4R on a 5¢ stop.
- **Improvement:** leaderboard columns for stop % and ATR, cost per R, and account R; flag ranking flips.

**Q15 Stop rounding.**
- **Q:** How many stops were bad, and are verdicts invalidated?
- **A:** No inverted stops. About 1.8% of trades were stopped out by rounding (~+0.016R). No verdict flips.
- **Evidence:**
  - 0 of 22,190 trades had an inverted stop.
  - 49% of stops were tightened, by a median 0.0027R.
  - 12 of 116 checked tightened stop-outs hit only the rounded stop.
  - The inverse guard concerns inverse-ETF shorts.
- **Improvement:** full-bar correction replay; re-score setups within 0.05R of zero before the Friday review.

**Q16 Rule churn.**
- **Q:** Setups with 20+ trades under one rule set? Is there a freeze plan?
- **A:** None strictly. A freeze plan exists for Primary only.
- **Evidence:**
  - 236 entries, 92 of them effective on or after 11-12.
  - Since 11-12: 66 single-account setups with 20+ trades, 0 with 15+ days.
  - 8 entries dated 11-20 and 1 dated 11-23.
- **Improvement:** epoch for all accounts 11-23..12-18 with epoch ids; pre-registered slate.

**Q17 Regime.**
- **Q:** Avg R by up/flat/down day?
- **A:** Negative in every regime. Losses depend on direction, but even a hindsight gate only reaches -0.051R.
- **Evidence:**
  - SPY open-to-close: down -0.151, flat -0.083, up -0.134R.
  - Longs on down days -0.271R; shorts on up days -0.291R.
  - Pre-open gates: -0.09 to -0.10R.
  - 19 setups lose in all three regimes.
- **Improvement:** 10:30 regime-gate study with per-setup reporting.

**Q18 Duplication.**
- **Q:** Same-symbol overlap and effective N?
- **A:** 41.7% of trades clash with another setup; effective N ≈ 13 of 63. The overlap comes from sibling families plus a long/short factor.
- **Evidence:**
  - 97% of clashes are same-side.
  - Buckets of 3+ setups: -386.5R.
  - CWT14: 15 setups, 35% of trades.
  - 11-17: longs -354R gross, shorts -14R.
- **Improvement:** research replay of a per-symbol/side/5-min cap (not a default cap); family column on the leaderboard.

**Q19 Arena overhead.**
- **Q:** What share of effort goes to account machinery?
- **A:** About 16% of commits are pure arena work (24% including mixed); about 22% are edge research. Tags would give about the same information.
- **Evidence:**
  - 451 real commits since 11-06.
  - 53% of ledger entries in the window are moves, admissions or rotation.
  - Resource skips 0.2–2.4% of signals.
- **Improvement:** one-virtual-account replay with budgets per tag; workstream tags on commits.

**Q20 Rotation.**
- **Q:** What did benching cost? Did rotation produce verdicts?
- **A:** Benching cost good setups 0R. Rotation produced 0 verdicts.
- **Evidence:**
  - GY-BENCH rested 18 losers (17 negative).
  - The ROT1 spotlight produced 33 trades and -10.5R.
  - Guests produced 6 trades.
  - The bottleneck is signal rarity and spread/borrow checks, not account room.
- **Improvement:** columns for reps gained and projected sessions to the gate; setups needing >40 sessions get reps from replay or shadow.

**Q21 Yield by source.**
- **Q:** What is the pass rate by idea source?
- **A:** Not measured. Statuses are stale. 7 of 10 positives came from in-house swarms or rework.
- **Evidence:**
  - Top-5 execution tune: 0 of 378 reached testing (283 of 303 rework items).
  - NM-ETF's backlog row still says "idea".
  - Reddit, owner and consultant sources: 0 live survivors on small samples.
- **Improvement:** origin field on every backlog row; monthly yield table; cap the tune loop.

**Q22 Admission bar.**
- **Q:** What does the top-10 standard filter?
- **A:** It screens out the clearly bad setups but does not select for edge. A "positive on history" bar would have rejected L3.
- **Evidence:**
  - Tier A thresholds are negative.
  - BEG-01 is level with random entries.
  - GEN setups (history-positive by construction) pool at -0.175R vs -0.113R for the rest.
- **Improvement:** calibrate admission tests against live outcomes; add a "beats random" leg.

**Q23 Stocks in play.**
- **Q:** Does in-play lift R?
- **A:** Slightly: -0.104 vs -0.136R, not significant. A top-50 list is still negative.
- **Evidence:**
  - Day-paired t 1.48.
  - Gap trend from -0.158R to -0.060R.
  - Per setup 66 better / 58 worse.
  - Primary does worse in play.
- **Improvement:** full-universe opening-rvol study.

**Q24 Time of day.**
- **Q:** Where is the bleed concentrated?
- **A:** At the open, 09:50–10:30 (-0.176R). A midday ban does not help.
- **Evidence:**
  - Midday ban: kept trades -0.137R; 48 setups improve, 45 worse.
  - Skipping 09:50–10:30: 42 improve, 21 worse; median +0.017R.
- **Improvement:** targeted no-entry-before-10:30 test for setups that lose at the open in both halves.

**Q25 Shorts and borrow.**
- **Q:** Long vs short; is borrow modelled?
- **A:** Shorts -0.099R, longs -0.143R. ETB gated; no locate fee and no SSR handling.
- **Evidence:**
  - ~6,300 short signals refused as not ETB.
  - Price floor $5.03.
  - The replay broker assumes borrow.
- **Improvement:** short-realism audit (borrow flags, SSR days, locate charge); replay uses recorded flags.

**Q26 Execution delay.**
- **Q:** Delay, adverse move, limit entries?
- **A:** ~36 s; +0.02–0.04R. Limit entries tested once and failed.
- **Evidence:**
  - 34 s polling lag plus 1.6 s fill.
  - Fills at the signal price would give 36 positive setups instead of 28 (of 119).
  - bdi1013: 0 of 957 limit configurations passed.
- **Improvement:** stop-limit replay for setups whose trigger is set before the bar closes; streaming or tighter polling.

**Q27 Data feed.**
- **Q:** IEX or SIP; revised bars?
- **A:** SIP everywhere. About 0.2% of trades possibly affected by revisions (3-session sample).
- **Evidence:**
  - feed: sip in config and workflows.
  - Replay audit: 35 of 2,749 trades had no replay signal at the decision minute (30 of them Gen breadth contexts).
  - fetch_bars still defaults to IEX.
- **Improvement:** nightly decision-bar fidelity check; change the default to SIP (housekeeping).

**Q28 Brakes.**
- **Q:** What protections exist, and did they fire on 11-17?
- **A:** Per-account brakes only, loose outside Primary. The Graveyard halt and the -2R latches fired.
- **Evidence:**
  - Gen and Testing halts at 300R; no per-setup stop in Gen.
  - Graveyard halt blocked 1,532 entries (saved ~40R after costs).
  - Latch skips over 11-17..19 would have lost -362.6R.
  - Watchdog acts only in Primary.
- **Improvement:** system-wide stop replay; cost-in halts in all accounts; latch in Gen and Testing; watchdog act on the checklist.

**Q29 Frequency.**
- **Q:** First signal per symbol, or top-50?
- **A:** Both negative. Only a hindsight ranking is positive.
- **Evidence:**
  - First signal -0.136R.
  - Prior-ranked top-50 -0.19 to -0.22R.
  - Busy days lose more (r -0.39).
  - Graveyard plus Gen = 49% of trades.
- **Improvement:** walk-forward per-signal ranking vs random; journal entry timestamps and a rank field.

**Q30 Capital realism.**
- **Q:** How many signals could a $50k account at 1% risk take?
- **A:** ~25 a day (3%). Per-setup R does not transfer to a capped account.
- **Evidence:**
  - About 4 positions open at once at 1% risk with a ~1% stop.
  - Capped replay -0.129R.
  - SIZE1: the cap cuts the best book's edge.
- **Improvement:** nightly one-real-account shadow book (0.10% / 4×, plus a 1% stress case) with a market-impact add-on.

**Q31 Common exits.**
- **Q:** Has a common-exit replay been run?
- **A:** Yes. 3,836 configs, 0 pass. The exact "2R target for every setup" variant was not run on its own.
- **Evidence:**
  - Chandelier trail -379R; time stops negative.
  - Partial exits 0/27 families better.
  - Y1 (RW3/RW5 1.25× target) passed: +0.044R.
- **Improvement:** GB-GENTRAIL; one 2.0R-target variant; otherwise focus on entries.

**Q32 Last-10 trend.**
- **Q:** Does recent form predict?
- **A:** No across sessions. Same-day persistence is real.
- **Evidence:**
  - Last-10 vs next-10 r -0.014 (CI -0.09 to +0.06).
  - Hot streaks → -0.135R next.
  - Block persistence r 0.35, but 93% of block boundaries fall inside one session.
  - Primary demotion uses -10R since admission.
- **Improvement:** Friday calibration of scoring rules; replace the -10R trigger with a day-clustered rule; backlog an in-session gate as an R remedy.

**Q33 Tuition vs production.**
- **Q:** How much of -3,500R is exploration?
- **A:** 97.5%. Primary -87.5R. The current 5 have made +70R since promotion, not proven.
- **Evidence:**
  - Primary day t -0.81.
  - RW3 and RW5 get ~75% of their R from one day.
  - The 5 together: day t 1.66.
- **Improvement:** production scoreboard; pre-declared pass/kill bars.

**Q34 MarcoFlow lessons.**
- **Q:** Which failure modes are repeating?
- **A:** Sprawl, churn and overfitting are repeating. Fills, latency and duplicate orders are fixed.
- **Evidence:**
  - 220 setups have traded; 23–63 new per week.
  - 236 ledger entries; 11 flagged mid-session.
  - Giveback fit-best time cuts: 9 better / 26 worse.
  - Fill drag +0.041R vs MarcoFlow's ~0.25%.
- **Improvement:** realized false-discovery audit; freeze admissions; Friday epochs for all accounts.

**Q35 Move Hunt.**
- **Q:** Capture rate of top movers; is the predictor measured independently?
- **A:** 4.9% caught (all) / 13.7% (tradable); 64% touched that day. A pre-open predictor gives ~2× random lift on 2-year history, but it is not run live.
- **Evidence:**
  - Captured +60.3R vs wrong-direction trades -169.5R.
  - Misses: outside the move 31%, no signal 31%.
  - Capture rate is not in the daily report.
- **Improvement:** nightly "on deck" ranking plus capture score; timing/direction study on known movers.

**Q36 Concentrated book.**
- **Q:** What would a pro book of the 10 survivors have done?
- **A:** Hindsight +231R. Walk-forward lost at all 3 cut dates, so it is not shown to beat the machine.
- **Evidence:**
  - Walk-forward -0.256 / -0.138 / -0.088R vs rest of machine -0.124 / -0.121 / -0.105R.
  - Hindsight book day t 1.63; +48.8R without its top 3 days.
- **Improvement:** pre-registered 20-session frozen shadow book (L3 plus RW3/RW5, members picked by a written rule); in-play journal-only tag.
