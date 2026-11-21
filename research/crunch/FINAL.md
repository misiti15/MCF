Educational only — not financial advice

# Crunch FINAL — lead consultant consolidation (written Fri 2026-11-20 after the close, ~19:30 ET)

Consolidation only: **0 new configurations**, no backtest, no config / setup / exit / ledger change. Sources: research/crunch/WAVE1.md, WAVE2.md (incl. its Skeptic), research/ultimate_1119/ (ROUNDS.md, round5, round6, top10, footrace), research/outsider_1120/REPORT.md, research/whatworks_1120/ (REPORT + null / retire / brake / nmetf), research/st7_review_1120/REVIEW.md, research/remedyq_1120/verdicts.json, research/lateqshort_1120/REVIEW.md, research/workbench/latepb_1120/REPORT.md, research/beginner_1120/REPORT.md, research/giveback_1119/REPORT.md, research/rootcause_1119/FINDINGS.md, research/owner1120/REPORT.md, research/owner_inbox/2026-11-20.md ("## Consultant"), docs/live/decisions.json (44 open), docs/PROTECTED.md. All R is after costs (LR8) unless marked "booked".

## 1. Plain summary (5 lines)

1. **Primary had a `1 day` week:** +4.11R for 11-16..20, but −21.20R without 11-16 (+25.31R). Over the last 20 sessions it was green on 7 (35%), the median day of the last 10 was −3.99R and the worst day was −31.25R (11-10). Account R for the week was about +2.0R (+$414).
2. **No broad edge is proven yet.** Only the gap-down trio (L3-fromopen, RW3, RW5) makes money in Primary: +73.4R on 530 trades, but −9.7R without its 2 best days. The other 24 setups that traded there lost −161R. Across the system, a setup's live rank does not predict its next rank (Spearman −0.11).
3. **About 26,000 configurations were tested this crunch, and the "obvious fixes" all failed:** exits, breakeven and day-locks (0 of ~22,000), timing cut-offs on 2-year data, loosening, regime gates, learned rankers, earnings setups, textbook setups and more generator volume. What does hold is narrow: picking the right stock-day, the spread gate, the plumbing, and the inverse-short guard.
4. **For next week, three decisions are worth taking:** INV-H1 (short setups skip inverse / long-vol funds: +55.9R live without its discovery day, 50 setup-accounts better and 24 worse); ST7-MOVE (ST7-FD to On Deck at the next Friday window); and ETF-BURST (a study only). Everything else is hold steady: let the changes that start 11-23 run, which follows the owner's consistency-over-churn rule.
5. **Proposed cadence now that consultant overtime ends:** one short scorecard check-in after each close. Decisions are batched for Friday, and research runs only when a decision needs it. The 44 open decisions should be cut to about 10.

## 2. Where Primary stands this week

**Scorecard** (source: research/owner_inbox/2026-11-20.md "## Consultant", Primary `mcf-data:journal.db` run 1, R = LR8 after-cost trade R)

| Measure | Value |
|---|---|
| Week 11-16..20 | **+4.11R** |
| Week without its best day (11-16 +25.31R) | **−21.20R**. 11-16 is about 6x the week's total, so the week is tagged **`1 day`** |
| Median day, last 10 sessions | **−3.99R** (10-session total −33.4R) |
| Green days, last 20 sessions | **7 of 20 (35%)** |
| Worst day, last 20 | **−31.25R** (11-10). 7 days were at or below −10R: 10-29, 11-04, 11-06, 11-09, 11-10, 11-11, 11-19 |
| Today 11-20 | +3.00R on 33 trades (21 wins). The dashboard shows +3.79R because it uses trade R before LR8 |
| Account R vs dashboard R | Today: **+0.77R account** (+$161.91 after costs ÷ 0.25% of $84,121), or +1.02R on Alpaca's +$214.16. Week: about **+2.0R account (+$414)**, against +4.11R trade R |
| 33-session view (WAVE2 item 7) | −133.4R trade R (LR8) but only **−10.0R account R**. Lots under $25 carry 61% of the trade-R loss. On 3 days trade R and account R have opposite signs |
| Epoch 1 (11-19..20) | −13.2R. The BASE1 paired difference is +9.19R, all of it NS5 on 11-19. Two sessions are too few for a verdict |

**What drove the week**
- **11-19, −14.4R:** two rule defects, not stacking and not execution (rootcause_1119).
  - ST7-FD bought 7 tech names on the 10:45 bar because of an RSI warm-up artifact (−7.53R).
  - L3 shorted SPXS and SQQQ, which made it a long-market bet (−6.49R).
  - The system rules saved about +43R that day: ETB skips about +33R and the −2R latch about +10R.
- **11-20, +3.00R:** Primary's 20 shorts were all green (+15.3R) on a −3.2% SPY day.
  - NM-ETF-late-dip lost −12.57R on 12 stopped lots that opened together around 14:10-14:15.
  - BRAKE-BURST (from 11-23) would have blocked none of those 12 lots.
- **The current Primary book** (NS5 left on 11-19): L3-fromopen, RW3, RW5, ST7-FD and NM-ETF-late-dip.
  - No member is at the −10R demotion line. ST7-FD is closest, about 2.7R away: 43 trades, −0.149R, −0.281R without its best day.
  - No setup in On Deck or Testing A-F clears C3-BAR2. RW7-FD comes closest: it fails only the best-day check (63-65% `1 day`).

**Rule-change context (research/ledger.jsonl): do not mix these with setup results**
- **Inside the 20-session window:**
  - 10-23 Testing per-setup stop off.
  - 10-28 Primary sizing of about $4k (slots 160 → 77).
  - 10-29 −2R latch.
  - 11-11 TEAM-6.
  - 11-12 LR8 after-cost R. Figures that span this date are re-costed.
  - 11-16 ROT1.
  - 11-17 TSZ1 half lots in testing, 15 WB copies and the promotion hold.
  - 11-18 GY-BENCH, SRCV1 (weight 0) and recorded quotes.
- **This week:**
  - **11-19:** C3 Epoch 1 (NS5 out of Primary, BASE1, EXIT100, ROT/ROT2, BAR2, WB/WB5, SCORE, U9-ETB, U9-TGT), plus the conflict-check rule.
  - **11-20:** stop-rounding fix, 9 ultimate_1119 testing admissions, FOOTRACE-EXIT, the GY foot race, ROT arena block 2, and the inverse shadow (journal only). Policy entries `primary-scoreboard` and `consistency-over-churn` also date from 11-20.
- **From 11-23** (PRs #238 / #239):
  - BEG-ORB (Testing F) and BEG-GNG (Testing B).
  - Remedy-Q 12:30 copies of L3 / RW3 / RW5 in Testing F / Testing 2 / Explore 1.
  - BRAKE-BURST, watchdog act, WW-PROTECT, WW-CLUSTER and RETIRE-R3.
  - 12 FOOTRACE-EXIT moves and 12 retirements.
  - **None of these changes Primary's lineup or rules.** Next week's Primary figures are therefore comparable with this week's, apart from the brake and watchdog, which have never fired in Primary.

## 3. What should go into next week (RANKED, owner decides each)

The ranking weighs evidence strength × effect on Primary, then cost and risk. **Friday window** means the next Primary epoch window: 11-27 after the 13:00 half-day close, or 11-30 after hours, with a rule-27 skeptic review and a ledger entry. Each item names the protected-list (PROT) and owner-rule conflicts it must clear (conflict-check rule, 11-19).

| # | Code | What | Why (numbers) | Risk | Conflict flags |
|---|---|---|---|---|---|
| **1** | **INV-H1** (existing; with **INV-LONGS** yes and **INV-BUY** no) | Every short setup skips inverse and long-vol funds (SQQQ / SPXS / SOXS / VXX type). Inverse longs stay in play. The journal-only shadow keeps running, and the guard goes live outside 09:30-16:00 once it has passed **≥ 10 shadow sessions** (about 12-04). The Primary part (L3) goes live in a Friday window | Live: 224 shorts, −78.8R; **+55.9R without 11-19**. **50 setup-accounts better (+99.3R), 24 worse (−20.6R, worst −2.65R)**; families 19 better, 4 worse. On 2-year data with a borrow proxy: +79.6R, 36 better / 20 worse, positive in both halves. Shadow day 1 (11-20): kept out 14 shorts worth −12.95R. G2 also passes | Hindsight-defined: the class was named after 11-19. SQQQ + SOXS are 71% of the removed R. The lab's early half is only +13.3R, and the lab disagrees on L3-fromopen (−5.4R). The "count as long-market exposure" add-on is **untested** and is split out | The owner's INV condition (11-19, "only if we can afford it"): blocking shorts *gains* R, so the condition is met. Inverse longs are kept because their evidence is undetermined (+20.5R, all from one day). PROT-05 already lists the inverse guard (strong), so this is consistent with it. PROT-06 (L3 layers): this is a universe filter, not a layer change. **Playing time (11-03 / 11-04):** three low-rep L3 WB copies lose most of their trades (T2 18/24, Live Lab 2/2, Testing F 3/3); they need rotation and must not be switched off. Backlog route (RULES 15-17); no change in market hours |
| **2** | **ST7-MOVE** (existing) | Move ST7-rsi50dn-long-pm-t1s1-FD from Primary to On Deck **unchanged**, at the next Friday window. Alternative: "probation", which means it moves automatically at −10R. Return bar: ≥ +15R on its non-overlap record plus C3-BAR2 | Primary: 43 trades, −0.149R, **−0.281R without its best day**, day t −1.16, 38% green days. It fails the random-entry null (p 0.10; Primary-only 0.33). 2-year lab: +0.045R, t 1.0. **FRESH 2023-24: −0.016R; FIT window: −0.132R**, so it is positive in only 1 of 3 periods. 64% of its live trades come from the RSI artifact bar, and the 13:35-15:00 window that earned its promotion was dropped in the FD copy. All three ST7 copies lost on 11-19 (about −22.9R) | Without 11-19, Primary is +1.35R on 34 trades (flat, not negative). Moving it before the −10R line is stricter than the automatic rules, which is a churn risk. The book loses its only long dip-buy, though NM-ETF remains | **Consistency over churn (11-20):** this is a deliberate exception, and the evidence must carry it; it does. PROT-07 covers only the trio, not ST7. **Promotion = move (10-20):** On Deck, not off; assignments.json is regenerated in the same commit. ST7-A (keep the shared RSI code) and ST7-B (no afternoon copy) were already answered 11-19 and are not reopened. Friday window, BASE1 note |
| **3** | **ETF-BURST** (existing; **study only**) | A pre-registered study of a **per-setup** limit on correlated ETF lots opened in the same bar or 5-minute bucket, reported for NM-ETF, its WB4 copy and ULT-22. NM-ETF itself stays unchanged | 11-20: 12 lots, −12.57R in Primary; WB4 copy (E) −15.8R; ULT-22 (C) −10.1R; all accounts 98 ETF longs, −75.0R. In NM-ETF's Primary record, lots opened 3+ in one bucket total 18 trades, **−13.04R**; the other 9 total +1.59R | **Against:** on 2 years of data its bursts of 8+ lots were its *best* trades (+0.48R on 66). The 11-17 three-lot bucket was +0.43R. The study may well end "no cap" | **Owner: "don't cap stacking by default."** This is a targeted, per-setup study and not a default cap. It goes live only with a per-setup better/worse report (remedies rule, 11-05). **PROT-23** (no burst caps beyond BRAKE-BURST) and **PROT-29** (NM-ETF unchanged, 15 more active days) both apply. BRAKE-BURST does not cover this pattern |
| 4 | **Close the "no-change" codes:** BE-NO yes · GT-KEEP yes · GB-BLPARK yes · LPB-1120 (LPB-UNBLOCK yes / LPB-WIDE no / LPB-WB5-OFF no) · INV-BUY no · WB2-NEXT-2 no · WB4-SPY-READ no (FYI) · G261019-04-GY no | Record the answers the tests already give, so these stop taking space on the card | BE: 18,144 configs, 0 pass. GEN trail: −0.049R, t −2.61, 4 better / 21 worse. LPB: unblocking frees 0 trades, and 0 of 53 looser variants clear the bar. G261019-04: BRAKE-BURST caps the burst behind its −99R day | None: each answer keeps things as they are | LPB-WB5-OFF must be "no" under the trimmed-setups rule (11-03: never just switch off). G261019-04-GY "no" follows the owner's 11-19 keep |
| 5 | **TAGS1-WHATIF**, **CORR1**, **TAGS1-HOLD** (existing; housekeeping), plus the LPB `blocked_pct` split | Fix the TAGS1 count of what-if rows as live. Correct W6's correlation labelling bug, so RW3+RW5 and the two L3 setups each count as about one bet. Keep FLAT25 / MFGAP frozen until their single 12-17 score | 1,664 what-if rows were counted as live on 11-19. The 0.74 / 0.76 figures were a column-label bug (re-run: 0.07 / 0.01). FLAT25 sits at the 4.8th percentile and MFGAP at the 44th (no better than random) | None (reporting only) | CORR1 is not a cap: STOP2 bars cross-setup entry caps. TAGS1-HOLD keeps the locked-score rule |
| 6 | **RW7-WATCH** (new code; research note) | Pre-register RW7-gapdn-bounce-early-short-FD (Testing F) as the BAR2 watch candidate, re-scored at the 11-27 / 11-30 window on its pooled non-overlap record, with a red-day column and the WW-CLUSTER figures | 872 trades / 28 days, +62.0R, +0.071R a trade, +0.025R without its best day, shrunk +0.046. Non-overlap with Primary: +58.0R. It fails only on 11-20 being 63-65% of its total | It moves with Primary (−25.9R on Primary's 18 red days, corr +0.23), so it may add little diversification | **Promotion hold (11-17)** must be lifted before any promotion. C3-BAR2 / PROT-14. One-big-day rule (10-25). Not a promotion lead today |
| 7 | **NMETF-SIZE** (existing) | **Lean no for now.** Let the frozen OUT-NMETF forward test run (25 Primary sessions, 11-23..12-31) and decide afterwards | Primary: 15 scored trades, +0.075R, t 1.18, `1 day` (66%). Since 11-19 it stands at 27 trades, −0.424R after the 11-20 burst. Chance of passing: about 80% if the true edge is the whole-record +0.21R, about 20% at Primary's own rate | Size-up on a thin record. 14 of 15 trades were slot-limited, so it doubles both caps | **C3-BAR2** (per-setup risk stays flat). **PROT-24** (no size-up while Primary R is negative). PROT-29. It needs an explicit exception if it is ever a yes |
| 8 | **WB2-Y1-SHADOW** (existing; optional) | Target at 1.25x on RW3 / RW5 as a journal-only paired shadow | +0.044R a trade, t 2.58, 6 of 6 weeks positive, 0 of 5 setups worse. Counted with its lineage (N 31) the bar is 2.62, which it **narrowly misses** | It relies on 42 trades held into the 15:55 flatten in a down tape | **WB2 hold (11-18):** "this may conflict with the WB2 hold; do you still want to proceed?" No exit change in market hours. PROT-27 (t1s1) |
| 9 | **LATCH-CLOSE** (existing, open since 11-12) | Recommend **keep the forward shadow and add no live rule** | 2-year VALID +1,684R, t 3.89. But the forward shadow's day 1 was −34.23R (16 better / 14 worse), and the brake study finds per-setup loss latches add nothing in Testing | An exit-family rule. The 2-year and live reads disagree | PROT-21 (latch rules). GB-NOEXIT evidence (section 4) |
| 10 | **DEC-CLEAN** (new code; housekeeping) | Close or supersede the 10 decisions open more than 3 nights (HN3, M1, M2, REGX, LATCH-CLOSE, LR6, CF-OD, MF4-OK, SIP-DEF, INACT), and park the optional research codes (UPDAY-PIT, PAPERS-FADE / YEAR, GT-BE, GB-BRAKE, CONS-PMX, W2-MTM, W3-GB5S, W3-BENCHSHADOW, EXIT-MF5, W2-ODOUT) in the backlog | 44 decisions are open, 34 of them raised 11-18..20. Several are probably moot (for example MF4-OK: MF4-FD went to the Graveyard on 11-19) and each must be re-verified before it is closed | Low. An item closed by mistake can be re-raised | Every closure is recorded as the owner's answer or marked "superseded" with a reason. Nothing is applied without a reply |

**Not ranked, already approved and starting 11-23** (no decision needed; watch only): BEG-ORB / BEG-GNG, the Remedy-Q 12:30 copies, BRAKE-BURST, the watchdog in act mode, WW-PROTECT / WW-CLUSTER, RETIRE-R3 (≥ 20 active sessions and ≥ 150 trades; never Primary), and the 11-20 Friday review moves.

## 4. What was PROVEN not to work (configurations counted)

| Area | What failed | Configs | Key numbers | Source |
|---|---|---|---|---|
| Exits and profit locks | Time cuts, breakeven moves, trails, partial profits, closer targets, clock exits, SPY-turn exits, day-level profit locks | **3,836** scored (lineage 5,272, bar t 4.14) | 0 pass. Taking profit early lost 950-1,600R on far-target setups. The +5R / 30% giveback lock saves 11-19 but costs 40.8R on 11-12 and 24.0R on 11-16 | giveback_1119 |
| Breakeven (stop to entry) | Every whole-position breakeven rule | **18,144** (9,072 independent) | 0 pass. All 216 whole-position rules lose book-wide | owner1120 (BE-NO) |
| GEN hold-setup exits | Trail, 1R target, chandelier | (GT study) | Check −0.049R, t −2.61; 4 better / 21 worse | owner1120 (GT-KEEP) |
| Exit classes on RW3/RW5 | Trail after +1R, target from the fill, SPY-since-entry | 9 (Wave 2) + 16 (W5) | Fail. Earlier exits hurt the gap-down shorts (14 of 15 pairs worse). Only Y1 at 1.25x is near the bar (item 8) | WAVE2 §5, WAVE1 W5 |
| Timing tweaks (2-year data) | 13:00 cut-off; L3 AM-only; ST7's 13:35-15:00 window; LPB 13:30 start; midday ban | 66 (Remedy-Q) + others | 13:00 cut: better live, but worse per trade on lab CHECK for all 3 setups. 12:30 cut: t 1.94 vs bar 2.89 (testing copies only). L3AM 2-year VALID t 0.36. ST7 window searched in-sample (120,500 configs, needs t 4.84, has 1.68). LPB 13:30: +0.064 on FIT → −0.017 on CHECK. Midday ban: coin flip (48/45 setups) | remedyq_1120, WAVE2, latepb_1120, outsider Q24 |
| Loosening | Wider lists, wider hours, lower ADV, looser triggers | 54 (LPB) + ULT-12/13/22/32-D | LPB 0 of 53 clear the bar. WB4 widened to 205 ETFs: check −0.005. Wider hours +0.004. Stock dip leg −0.078. Widening a real edge kills it | latepb_1120, ROUNDS.md |
| Per-setup condition rules / skips | Bespoke filters, FLAT25, MFGAP | **2,176** (W4) + 3 | 0 of 31 bespoke rules pass. Condition signs persist between halves only 56% of the time. FLAT25 4.8th percentile, MFGAP 44th (no better than random removal) | WAVE1 W4, WAVE2 §4 |
| Regime / market-state gates | Volatility, trend, VXX, breadth, dispersion, gap, weekday; Compass gate | **822** (round 6) | 0 of 24 pass. Closest (dispersion) keeps 13% of 2023-24 trades and 45% of its profit comes from one day. Compass removes trades no worse than the ones it keeps | round6/RESULTS.md, rootcause_1119 |
| "Ultimate" new setups | Patterns, learned rankers, ETF / mega-cap dips, sector lags, clock slots, cheap-cost universes, earnings / news | **~1,000** (rounds 1-4, 35 candidates) + 8 (FRESH) | 0 BEAT, 0 robust Tier A. 25 of 35 lose on check. FRESH 2023-24: 0 of 8 beat, and even ST7-FD is −0.016R. Random entries in the same names lose 0.02-0.05R before any trigger | ROUNDS.md, round5 |
| Earnings | EARN-GO | 1 (+ ULT-28..35) | −0.070R, t −2.44, both halves negative, worse than random and negative before costs | WAVE2 §2 (closed 11-19) |
| Shared RSI fix | Session-reset and gap-adjusted RSI | 4 | 40 of 46 setups worse (session reset), 31 of 45 worse (gap-adjusted), in both halves | WAVE2 R2 (ST7-A, kept) |
| Beginner textbook setups | ORB, gap-and-go, VWAP, etc., plus 8 session rules | **69** | 0 of 10 profitable on CHECK after costs (BEG-03 +0.006 rests on one day). A −3R daily stop and trade caps hurt Primary's winners. Only the S8 sanity filter helps, slightly. Two admitted anyway by the owner's admission rule | beginner_1120 |
| Generator / volume sources | More setups and more trades | Generator 64 setups, CWT 27, NS 11, ST 8, heat 4; top-5 tune loop 378 | 3 of 64, 1 of 27, 0 of 11, 0 of 8, 0 of 4 positive. 3 of 3 Generator graduates collapsed. Volume doubled while daily R fell from −76 to −145R a day. Tune loop 0 of 378. Selected tunes: fit +63.6R → check −45.3R | whatworks_1120, outsider Q01/Q21, WAVE1 W5 |
| Loss brakes beyond today's | Tighter halts, per-setup latches in Testing / Gen, stacking caps | 50 (retire) + brake replay | No reliable gain for Primary. Stacking caps cut L3 / RW3 / RW5 by 13-21R each. The cap of 30 bound once and cost about +97R (11-12) | brake/REPORT, rootcause_1119 §4 |
| Live-record selection | Promoting / demoting on live rank | — | Spearman −0.11; last-10 vs next-10 r −0.01. Promotions fail 75-80% of the time | outsider Q01/Q32, whatworks §3 |

**Counted this crunch:** Wave 1 2,287 + Wave 2 31 + ultimate_1119 about 1,887 + giveback 3,836 + breakeven 18,144 + Remedy-Q 66 + LPB 54 + beginner 69 + retire 50 = **about 26,400**. These lineages partly overlap. The program-wide N is about 2×10^7, which puts the honest t bar near 5.8 (outsider Q03).

**What does hold (protect, don't tinker):**
- **Stock-day selection.** 32 of 165 setups beat a random minute within ±30 minutes of their entry, but only NM-ETF beats a later random entry.
- **The spread/stop gate (PROT-01).** Blocked Primary trades: −0.41R, against −0.12R for trades taken.
- **The plumbing:** 28,115 orders submitted = booked, 0 overnight positions in Primary.
- **The gap-down trio (PROT-06/07/26).**
- **The INV guard.**
- **Leaders run by their stacking.** L3's days with 5+ lots: +92.8R.

## 5. Go-forward cadence for the daily consultant (recommendation)

1. **Daily, after the close (≤ 15 lines, `## Consultant` in the owner inbox; no lab runs):**
   - The fixed scorecard: day R (trade and account), 10-session median, 20-session green %, worst day, week with and without its best day, BASE1 paired difference.
   - The rule changes in effect inside the window.
   - One leak and one opportunity.
   - Open decisions older than 3 nights.
   - Raise a new decision only when a rule trigger fires (−10R, BAR2, FOOTRACE-EXIT, RETIRE-R3, a broken bug).
2. **Friday after the close:** TEAM-REVIEW, Epoch / BASE1 read, BAR2 re-scores (RW7-WATCH on 11-27 / 11-30), FOOTRACE-EXIT and RETIRE-R3, and every Primary change in one batch inside the window, each with its skeptic review and ledger entry. At most **5 owner decisions per brief**, with the rest carried.
3. **Scheduled reads, no ad-hoc re-scores in between:**
   - INV shadow at 10 sessions (about 12-04).
   - TAGS1 single score on 12-17.
   - OUT-NMETF frozen test ends 12-31.
   - Remedy-Q / BEG copies at 15 active days.
   - Compass gate1 / comp15 at 20 forward sessions.
4. **Research budget:**
   - Go only where a decision needs it, and point it at **entry and stock-day selection** (the null study's finding) and at a pre-registered book of narrow edges on a window nobody has seen.
   - **Do not re-open the families in section 4** (exits, breakeven, locks, timing cut-offs, loosening, regime gates, rankers, textbook setups, volume) without a stated mechanism change.
   - Every study reports its configuration count, per-setup better/worse counts, w/o best day / top-2 days and day-clustered t (WW-CLUSTER).
5. **Hygiene:** run DEC-CLEAN once, then keep open decisions at or below about 10. The scout's scale-back on low yield stays in force, and the no-change-in-market-hours rule is unchanged.

Educational only — not financial advice
