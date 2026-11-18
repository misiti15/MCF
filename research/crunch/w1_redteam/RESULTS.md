# W1-redteam: review of the work produced 11-17/18

*Educational only — not financial advice.* Research only. I changed no config, code or runtime and merged nothing.
Every proposal below needs the owner's reply. Plan: PLAN.md, written before any figure was recomputed. Data: live
journals (run_id 1) from all ten `mcf-data*` branches, 10-06..11-18 (11-18 is used only where marked). R = pnl_adj /
(|entry − stop| × shares). The locked block was not read. **Configurations: 24** (the EXIT100 base-rate grid, all
reported in code/exit100b.py). Everything else is recomputation. Scripts: code/. Figures: recomputed.csv.

**Rule changes inside the windows (research/ledger.jsonl):**
- 10-22/23: latch off in Testing 1/2.
- 10-28: Primary sizing ~$4k.
- 10-29: Primary −2R latch.
- 11-05: the MTUM split booking (−$11.46k Alpaca equity, not a trade).
- 11-11: TEAM-6.
- 11-12: LR3/LR8 cost model, Testing D/E/F opened, Gen/Graveyard sizing.
- 11-16: ROT1.
- 11-17: TSZ1 half-size testing lots (dated 11-16 in the ledger, effective 11-17), promotion hold, WB copies.
- 11-18: GY-BENCH, SRCV1.

## Answer first

Most headline numbers reproduce:
- P9 Primary journal: −65.8R, 9/31 green, median −3.83R, SD 19.2R.
- Current six as traded: 547 trades, +89.8R.
- L3 in Primary: +47.7R over 133 trades, and +40.6R over 156 trades (share of the best day 65% / 76%).
- GY-ARCHIVE-20: −66.5R per session over 477 trades; the rest +4.0R.
- GEN: 89 setups, −772R.
- 195 ledger entries.
- L3 AM/PM split.

**The conclusions are weaker than the numbers.** There are five errors that matter for open decisions:

1. **R and dollars are different measures, not one measure × 4-9.** Over 11-12..11-18 the whole system is **−145R per
   session in R but +$21 per session in dollars**. Primary 10-06..11-17 is −65.8R but −$1,024, about −3.5 account R.
   The setup ranking changes too:

   | Setup | Dashboard R | Account R |
   |---|---|---|
   | L3 | +38.1 | +16.6 |
   | RW3 | +23.3 | +3.7 |
   | RW5 | +18.7 | +1.3 |
   | ST7 | +2.0 | −0.01 |
   | NS5 | +0.1 | +1.1 |

   The goal "positive R every day" is ambiguous until the owner picks the unit.
2. **Cost basis is mixed at 11-12.** Before 11-12, 62% of trades carry no cost at all: mean 0.022R, median 0. From
   11-12 the mean is 0.044R and the median 0.027R. Every fit/check split puts the LR8 sessions in the check half, and no
   report re-costed the history.
3. **C3-EXIT100's R claim is the arena base rate.** Flagged setups made −0.099R per trade later. The whole arena made
   −0.095R. Before costs the figures are −0.069 and −0.063. The flag picks setups no worse than average. "+60-75R a
   session" does not follow.
4. **C3-NS5's evidence does not reproduce, and one session flipped it.**
   - To 11-17, NS5 in Primary: 37 trades, −1.65R, green on 8 of 16 days (50%, not 29%), +$115.
   - With 11-18: +0.12R, +$252.
5. **"Honest ceiling two green days in three" is in-sample.** The six were chosen on 11-10 from these same records.
   - Since then Primary is 2 green in 6 in R (3 in 6 in dollars).
   - +29.2R in total, −10.7R without 11-12, median day −2.0R.

There are also four internal contradictions among the open codes. The owner cannot answer Yes to all of them as
written:
- C3-WB vs C3-WB5 / GY tune candidates.
- C3-ROT vs C3-WB5 / W7-TUNE27-08.
- C3-LEAN vs USAGE1.
- C3-EARN vs the BLKOUT finding of the same day.

## Error list (with correction and impact)

| # | Sev. | Claim (source) | Recomputed / found | Correction | Impact on decisions |
|---|---|---|---|---|---|
| E1 | HIGH | "Dashboard R overstates dollars 4-9x" (P3 P8); every R total and the owner goal | **Per setup the dashboard R ÷ account R ratio** ranges 2.3 (L3) to ~15 (RW5), and ST7/NS5 even differ in sign. Primary risk per trade after 10-28: p5 $11, median $36, p95 $131 against the 0.25% target of ~$210. **System R and $ disagree in sign**: 11-12..11-18 −145R/session vs +$21/session. Primary days R and $ disagree on 3 of 32 (10-26, 11-05, 11-18) | Not a scale factor. R treats a $11-risk trade like a $131-risk trade, so R sums weight tight-stop trades far above their dollars. Show both; the scorecard needs account R next to every R | **RE-ASK (RT-UNIT)**. C3-SCORE is strengthened, because it already adds the account-R column. Under P2's "RW3/RW5 protect, dropping costs 23-35R", the 32-session dollar contribution is +1.3 / +3.7 account R. The latch and halt fire on R and so on tight-stop trades with little $; LATCH stays, with this caveat |
| E2 | HIGH | "R after costs" everywhere (P2, P3, U-items, LATCH, GY) | Before 11-12, 62% of trades have pnl_adj = pnl (mean cost 0.022R, median 0). From 11-12: 0.044R / 0.027R, 0% uncosted. LR8's ledger entry says records mix and scripts/recompute_pnl_adj.py re-costs. No report used it | Pre-11-12 R is only partly after costs. Check halves carry ~0.02R per trade more cost than fit halves. W5's exit overlays put LR8 costs on new exits while base trades kept the old allowance, which biases the study against the overlays by up to ~0.02-0.04R per changed trade. W5's code was deleted, so I cannot size this | Decay findings are slightly overstated: W7 rank flip, testing→Primary +0.23→−0.08, EXIT100 later window. Before "exit overlays: null" (W5) is parked for good, re-run it on one cost basis (**RT-COST**). Nothing reversed |
| E3 | HIGH | C3-EXIT100: "flagged went on at −0.107R, −585R in 8 sessions; arena +60-75R/session" (P3 P3/P5) | Reproduced roughly with pooling by setup and Graveyard included: 26 flagged, −0.099R later, −489R, 5 recovered. **All later arena+GY trades: −0.095R.** Other 100+-trade setups: −0.07 to −0.18R. Before costs: −0.069 vs −0.063. With per-account keys: −0.081 vs −0.089 | The flag has no skill beyond the base rate, which agrees with P5 (Spearman 0.03). The "avoided" R is what any arena trade loses. Freed slots go to other arena setups that also average ~−0.1R, so the expected R effect is about 0. A move to the Graveyard leaves system R unchanged, because the Graveyard keeps trading the setup | **RE-ASK (RT-EXIT)**: keep EXIT100 as a rep-allocation rule only, drop the R claim, and end flagged setups in archive (GY-LIFE), not in active Graveyard trading. W7-DRAIN is the same |
| E4 | MED-HIGH | C3-NS5: "41 trades −0.9R, green on 29% of days, −4.0R w/o best day; book +4.1R / 26 sessions, 0 setups worse" | Primary to 11-17: 37 trades, **−1.65R** (raw −0.64R), **green 8/16 = 50%**, w/o best −3.76R, **+$115**. With 11-18: 41 trades **+0.12R**, +$252, 9/17 green. The +4.1R is 1 of 59 drop/add tests, against a daily SD of 13.5R | Noise-level. In dollars NS5 made money. Removing it also removes one of Primary's three longs (Primary is ~80% short) | **RE-ASK (RT-NS5)**: change the recommendation to "No — watch at the Friday review" |
| E5 | HIGH | "Honest ceiling ~2 green days in 3"; "current six pooled +158R, 62% green, median +2.30R" (P3 P1); scorecard "Now" uses it | Pooled six across accounts, no latch: +170R, 68% green over 28 days. This is the hindsight record of a book chosen on 11-10 from these records. P1 itself shows fit 92% → check 31% for selected books. **Primary after selection, 11-11..11-18: R −26.6 / +39.9 / −1.4 / +25.3 / −2.5 / −5.5, so 2/6 green, median −2.0R, −10.7R w/o 11-12.** $: 3/6 green, +$3,008 | The forward green rate is unknown. The observed rate since selection is 33% (R). Use the Primary journal from the TEAM-6 epoch (11-11) as "Now" | Scorecard rows 1-2 are corrected (C3-SCORE / C3-EPOCH). Expectations from C3-NS5's "62% → 69%" are not reliable |
| E6 | MED | Scorecard row 2 "43% since 10-29"; P3 table "current six 31 sessions, 14 green (45%)"; C3-NS5 "median day −1.10 → −0.64R" | Primary journal since 10-29: **4/14 green (29%)**, $: 3/14. The six traded on 26 sessions, 14/26 = 54%. The −1.10 median does not match the −3.83 headline; the series is not named | Use 29% (R) / 21% ($) since 10-29. Name the series for every median | Reporting only |
| E7 | HIGH | C3-WB: "no tunes or copies for losing parents with 100+ trades" (and Conflict 3). C3-WB5 #2, #3. GY triage TUNE-CANDIDATE | Pooled records: MF2-FD 181 tr −0.129; MF4-FD 209 tr −0.266; NS3-FD 258 tr −0.145; MF1-FD 147 tr −0.187; MF3-FD 297 tr −0.154. **All are losing parents with 100+ trades** | WB5 #3 (MF2/MF4-FD gate) and GY's MF1-FD / MF3-FD / NS3-FD tune candidates break C3-WB. WB5 #2 is allowed only on the 79-trade NS3 base, not NS3-FD | **RE-ASK (RT-WB5)**: answering Yes to both C3-WB and C3-WB5 as written is contradictory |
| E8 | MED | C3-ROT: "no verdicts before 15 active days and 30 trades"; C3-WB5 #1, #4; W7-TUNE27-08 | CWT09-g10: 22 trades, 12 active days. GEN-261027-08: 64 trades on **5 active days** ("positive in both halves" means 2-3 days each) | Tuning on these records is a verdict before the rep minimum | RT-WB5: hold #1 and #4 (and W7-TUNE27-08) until 15 active days / 30 trades. #5 (L3-rsi5hi refire off: positive parent, exit/frequency change) fits C3-WB |
| E9 | HIGH | C3-LEAN "pause Guild + Reddit (a yes also answers REDDIT)" vs USAGE1 "keep Guild + Reddit, re-aimed"; both recommended Yes on 11-18 | Direct conflict | One either/or question | **RE-ASK (RT-LEAN)** |
| E10 | MED | C3-EARN / P6 "PASS (one lead)": EARN-GO +0.346R, t 3.6 | The earlier half alone is +0.045R. Without 11-05 and 11-09 it is +0.145R. On the same day, guild BLKOUT found report-day BMO mornings −0.064R (t −3.57) for existing setups and told the owner the "blackout policy stands". U6's non-earnings gap-and-go FAILs | It fails the fit/check split every other study used, so PARTIAL, not PASS. The BLKOUT result belongs in the decision text | **RE-ASK (RT-EARN)**: run a pre-registered 2-year earnings-season test first (locked block excluded), then decide on a blackout exception |
| E11 | MED | W1-BAR / C3-BAR2 back-test "+19.3R, 18/7" | Fit half −11.1R, check half +30.4R: the sign flips across halves. P2 rejected day-type switches for exactly that. P5: 30-trade records do not predict the next 30 | Keep as a process rule (it is conservative), with no R claim | Keep C3-BAR2. Drop "+19.3R" as evidence |
| E12 | MED | SRCV1 plain text: "none of them counts toward a setup's record" | config/effective_sessions.json keeps `uncalibrated_weight` 0.2. effective.py uses it for shadow/replay when there are fewer than 3 calibration days, so Shadow counts 0.2 per session (FWDCAL: "uncalibrated (0.2) everywhere"). Also, SRC-VALUE's screen sample is GEN-only, pre-selected by the screen (restricted range pulls Spearman toward 0), and the 2-year backtest has n = 15 | What is implemented is not what was approved. "No rank skill" is absence of evidence | SRCV1 stands (weight 0 is safe). **RE-ASK with UNCAL (RT-UNCAL)**: set uncalibrated_weight 0 to match the SRCV1 text, or amend the text |
| E13 | LOW | Replay bias | SRC-VALUE snapshot −0.03R (pessimistic); replay_cal held-out +0.005/+0.007 (rosier); FWDCAL arena +0.035 (optimistic), Primary −0.037 | Different engines and windows. Publish one canonical line | None (weight 0) |
| E14 | LOW | L3 ETB block "56-60%" (P3) vs "76% of its short signals" (U9); "CWT14 = 37% of arena trades" | Different denominators. CWT14 is 38% *with* the Graveyard and 29% of the testing arena alone | State the denominators | None |
| E15 | LOW | U9-TGT stop part +56.9R, t 8.24 | R per trade is inflated because the fill-to-stop distance is tiny (U9 says so) | Show $ in the decision | U9-TGT stays a mechanical Yes |
| E16 | LOW | Usage summary lists "TSZ1 11-16" and "Testing half-size 11-17" as two changes | The ledger has one change, effective 11-17 | Fix the date | None |

**Checked and found sound:**
- P9 figures.
- L3 protect figures.
- GY-ARCHIVE-20 (archive group −0.139R/trade vs rest +0.039; the rest's +4.0R/session is carried by 11-12 at 186%).
- The L3-AM read: +0.338 is AM-only vs +0.266 all-day, consistent with the bespoke study's AM +0.31 / PM +0.04. Live
  ≥ 13:00 entries: 37 trades, −0.355R.
- Replay held-out pre-registration order (targets 02:05Z → params frozen 04:00Z → scored once 05:59Z on 11-17).
- LATCH review direction: post-cross real fills −0.154R vs arena base ~−0.09R, so post-latch trades are modestly
  worse. The R-basis caveat (E1) applies.

## Decisions already made (11-17/18): keep or re-ask

| Decision | Status | Red-team call |
|---|---|---|
| SRCV1 (applied) | yes | Keep. Fix the scope wording vs config (E12, RT-UNCAL) |
| L3-AM (FAIL) | yes | Keep. Consistent |
| LATCH as is / LATCH-RW7 not taken | owner | Keep. Note that it is R-based (E1) |
| ODPREP | yes | Keep. GY tune candidates must respect C3-WB (E7) |
| GY-BENCH, promotion hold | yes | Keep |

## Open codes: effect of the errors

| Code | Call |
|---|---|
| C3-NS5 | **Re-ask: No, watch** (E4) |
| C3-EXIT100 / W7-DRAIN | **Re-ask: rep rule only, end in archive** (E3) |
| C3-WB5 / W7-TUNE27-08 | **Re-ask: trimmed** (E7, E8) |
| C3-LEAN vs USAGE1 | **Re-ask as one choice** (E9) |
| C3-EARN | **Re-ask: test first** (E10) |
| C3-BAR2 / W1-BAR | Keep; drop the R claim (E11) |
| C3-SCORE | Keep, stronger: the account-R / $ column is the fix for E1, and the 11-12 cost-basis marker goes on every chart |
| C3-EPOCH | Keep. Compute the paired SD in $ as well |
| C3-WB, C3-MECH, C3-ROT, U9-TGT, U9-ETB, ENG1, GY-LIFE, GY-ARCHIVE-20 | Unaffected |

## Proposals (reply codes)

1. **RT-UNIT** (owner, needed before any target): which unit does "positive R every day" mean?
   - "RT-UNIT A": Primary account R = $ ÷ 0.25% of equity.
   - "RT-UNIT B": dashboard R.
   - "RT-UNIT both": both shown, goal on A (recommended).
2. **RT-NS5**: replace C3-NS5 with "No — watch NS5 at the Friday review". Reply "RT-NS5 yes".
3. **RT-EXIT**: C3-EXIT100 as a rep-allocation rule with no R claim; flagged setups go to archive via GY-LIFE, not to
   active Graveyard trading. Reply "RT-EXIT yes".
4. **RT-WB5**: the Workbench queue becomes:
   - #5 now.
   - #1 and #4 at 15 active days / 30 trades.
   - Drop #3 (MF2/MF4-FD) and GY MF1-FD/MF3-FD/NS3-FD tunes per C3-WB.
   - #2 only on the NS3 base.

   Reply "RT-WB5 yes".
5. **RT-LEAN**: one choice. "LEAN" (pause Guild + Reddit) or "USAGE1" (keep, re-aimed).
6. **RT-EARN**: pre-registered 2-year earnings-season test of EARN-GO (one config, costs in, locked block out) before
   any blackout exception. Reply "RT-EARN yes".
7. **RT-UNCAL**: `uncalibrated_weight` 0.2 → 0, so no unmeasured source counts, which matches the SRCV1 text. Reply
   "RT-UNCAL yes".
8. **RT-COST** (housekeeping-grade research rule): every study re-costs pre-11-12 trades with
   scripts/recompute_pnl_adj.py (or reports raw R beside), and W5's exit overlays are re-scored on one basis before
   "exit overlays: null" is parked. Reply "RT-COST yes".

## Caveats

- Account R uses approximate equity: $95.5k to 11-05 and $83.5k after (MTUM booking excluded; journal $).
- EXIT100 was reproduced only roughly, because P3's code was deleted.
- I could not re-run W5 or P1's 153k-book search. E2's W5 effect is a plausible bias, not a measured one.
- 11-18 is used only for NS5 and the post-TEAM-6 days.
