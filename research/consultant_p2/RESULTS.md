Educational only — not financial advice

# Outside consultant — Part 2 results (2026-11-18)

Research only, run during market hours: no config, code or branch changes. Data: live run (run_id 1) journals from the `mcf-data*` state branches, R = pnl_adj / initial risk (after costs). The locked block 2024-11-01..2025-02-28 was not read. Each workstream split its window into an earlier fit half and a later check half where possible. Scope: Primary plus the successful and up-and-coming setups in On Deck and Testing A-F (owner request).

**Configurations tried: 65 in total** (W1 9, W2 9, W3 13, W4 12, W5 7, W6 6, W7 9). Two configurations in W1 (V5, V6) were added after the first results were seen and are marked as not pre-declared.

**Rule changes inside the windows (research/ledger.jsonl):** 10-20 twin-symbol block; 10-22/23 per-setup latch off in Testing 1/2; 10-28 Primary sizing (~$4k); 10-29 -2R per-setup latch and BAR90, On Deck stop-cost filter 0.15R; 11-05 Explore 1 / Live Lab became low-rep homes; 11-11 TEAM-6 lineup; 11-12 LR3/LR8 after-cost R, split-tape gate off in On Deck (ODX-1), Testing D/E/F opened, Gen sizing; 11-16 ROT1 rotation; 11-17 Testing half-size (TSZ1), 15 WB copies, promotion hold; 11-18 GY-BENCH guests. MF2/MF4 were taken out of Primary inside the window. R is per unit of risk, so the sizing changes do not distort it; the latch and LR8 change which trades count and their net R.

**L3 reconciliation.** Gap-Down Recovery Fade (L3-gap-slope-fromopen-FD) in Primary is +47.7R over 133 trades for 10-23..11-17 (avg R w/o best day +0.206; best day 11-12 = 65%) and +40.6R over 156 trades for 10-06/10-21..11-17. The difference is its losing first stint on 10-21/22 (-7.0R). Both figures are after costs. Its record is a one-big-day record by the owner's tag in the longer window (11-12 = 76%).

## Verdicts at a glance

| Workstream | Verdict | Configs | Proposed change | Risk to L3 |
|---|---|---|---|---|
| W1 admission/demotion bar | PARTIAL | 9 | W1-BAR (admission bar + -10R-only demotion) | High under the bar as first proposed; none under W1-BAR |
| W2 correlation (RW3/RW5) | FAIL | 9 | none (next: W2-MTM test on WB copies) | None |
| W3 daily risk shape | FAIL | 13 | none (optional W3-GB5S shadow flag) | Every giveback lock costs L3 (-3.3 to -15.9R) |
| W4 long/short balance | PARTIAL | 12 | none; no long promotion | High if a short-share cap is adopted (-44 to -49R) |
| W5 exit overlays | FAIL | 7 | none | High: every rule hurts L3 (-1.4 to -18.5R) |
| W6 equity-curve gating | FAIL | 6 | none; log as rejected | High: cuts L3's best days (-4.5 to -29.3R) |
| W7 pipeline / contenders | PARTIAL | 9 | W7-TUNE27-08, W7-DRAIN | None today; medium if L3 twins are promoted |

## W1 — admission and demotion bar (PARTIAL, 9 configs)

Back-test on Primary 10-06..11-17 (1,316 trades, -65.9R). Delta = R under the bar minus actual Primary R.

| Variant | Direct adds (15) | Tested promos (12) | Improve/Worse/Same (27) | L3 | RW3 | RW5 | Fit half | Check half |
|---|---|---|---|---|---|---|---|---|
| V0 as proposed (n30, awo>0, green>=50%; demote -10R or n40 & awo<0) | +76.2 | -17.4 | 18/8/1 | -36.8 | -24.7 | -10.0 | -15.2 | -2.2 |
| V1 n20, no green rule | +70.8 | +8.5 | 17/8/2 | -36.8 | -25.4 | -10.9 | +21.4 | -12.9 |
| V2 n50, awo>0.05, green>=55%, -8R | +76.2 | +31.4 | 20/6/1 | +6.2 | -14.5 | -9.8 | -52.4 | +83.8 |
| **V3 V0 admission, demote -10R only** | +76.2 | **+19.3** | 18/7/2 | **+7.1** | -1.7 | -2.4 | -11.1 | +30.4 |
| V4 -10R or n60 & awo<-0.05 | +76.2 | +2.0 | 18/7/2 | +7.1 | -8.2 | -13.3 | -11.1 | +13.1 |
| V5* -10R or n40 & plain avg<0 | +76.2 | +55.9 | - | +7.1 | -1.7 | -2.4 | -11.1 | +67.0 |
| V6* -10R or 15R drawdown from peak | +76.2 | ~+2.5 | - | +7.1 | -7.7 | -13.3 | - | - |

\* not pre-declared.

- V3 per setup: improve CWT13 +4.4, L3-fromopen +7.1, MF3-FD +1.8, MF4-FD +27.0, NS3-FD +12.0; worse MF2-FD -24.2, RW3 -1.7, RW5 -2.4, ST7 -2.8, NM-ETF -1.9; unchanged CWT14, L3-rsi5hi. 18 improve / 7 worse / 2 unchanged across all 27.
- The "avg R w/o best day < 0 after 40 trades" demotion test would have pulled L3 on 11-10, missing +31.0R (11-12) and +16.4R (11-16). Dropped.
- Testing records do not carry over: 12 promoted setups averaged +0.23 R/trade in testing and -0.08 in Primary (Spearman plain avg 0.50, p 0.10; w/o best day 0.21).
- Half-risk sizing by edge (RW5): -3.1R or -16.9R. Rejected.
- Honest caveat: the tested-promotion effect is negative in the fit half for every variant (the delays miss 10-22) and positive only in the check half; most of the total gain is the 15 untested direct adds of 10-06..10-09, which the process no longer allows anyway.
- On Deck setups that pass now: L3-lowdist-FD (108 tr / 18 sessions, +26.5R, awo .109, best day 69%) and L3-rsi5hi-FD (130 / 15, +24.8R, awo .127, best day 53%). Both are L3 sisters (see W7). Promotion hold of 11-17 stands.

## W2 — correlation (FAIL, 9 configs)

Only RW3/RW5 are strongly linked: daily R correlation 0.78 in Primary, 41 same-symbol-same-side-same-day lots (39 open together). Baseline 6 setups 10-09..11-17: 547 trades, +89.8R.

| Config | Change | Fit | Check | Per setup |
|---|---|---|---|---|
| a1 drop later sister lot | -7.0 | -7.0 | 0.0 | RW3 +2.3, RW5 -9.3 |
| a2 only if earlier lot open | -7.2 | -8.1 | +0.9 | RW3 +2.3, RW5 -9.5 |
| a3 any pair of the 6 | -7.0 | -7.9 | +0.9 | RW3 +2.3, RW5 -9.3, NS5 +0.2, NM-ETF -0.2 |
| b1 shared -2R latch | -8.8 | -3.1 | -5.7 | RW3 -0.2, RW5 -8.6 |
| b2 shared -3R latch | -2.4 | 0 | -2.4 | RW3 +0.8, RW5 -3.2 |
| b3 shared latch NM-ETF+RW3 | -1.8 | 0 | -1.8 | NM-ETF -0.7, RW3 -1.0 |
| b4 a1+b1 | -13.9 | -9.5 | -4.4 | RW3 +2.1, RW5 -16.0 |
| cap 8 open RW3+RW5 | -20.7 | -34.2 | +13.6 | RW3 -11.2, RW5 -9.5 |
| cap 12 | -13.1 | -30.0 | +16.9 | RW3 -4.7, RW5 -8.4 |

Root cause: RW3/RW5 enter in bursts (46 lots open on 10-22, 32 on 11-10, 31 on 11-11); the realized-R latch cannot stop a burst. Any burst trim trades the +44R day of 10-22 against the 11-10/11 losses. L3 has 0 overlaps with the other Primary setups and is unchanged in every config. RW5 w/o best day -0.005 (10-22 = 104%); RW3 +0.025 (89%). Both one-day records — flag for the Friday review.

## W3 — daily risk shape (FAIL, 13 configs)

Primary 10-23..11-17, 724 trades, -47.2R; realized R only (no open marks in the journal).

| Config | Total R | Fit / check | L3 | Fired |
|---|---|---|---|---|
| Base | -47.2 | -12.9 / -34.3 | 47.7 | 0 |
| GB5 (+5R peak giveback; 33/50/66% identical) | -7.3 | -11.4 / +4.1 | 42.7 | 7 |
| GB8 (3 thresholds identical) | -28.3 | -12.9 / -15.4 | 47.4 | 3 |
| GB3_50 | +3.9 | -4.8 / +8.7 | 31.8 | 10 |
| H12 halt | -63.5 | -12.9 / -50.6 | 48.2 | 4 |
| H15 halt | -48.0 | - | - | 2 |
| FH3 / FH5 first-hour brake | = base | - | - | 0 |
| GB5+H15 | -7.8 | - | - | 8 |

GB5's gain is 11-06 and 11-10, and 31.5R of it is MF2/MF4 (already removed). On today's lineup: +11.3R, of which 11-10 is +16.6R; without 11-10 it loses -5.3R. Per setup on today's lineup: 6 improve (L3-rsi5hi +7.5, RW5 +4.0, NS4 +1.2, ST7 +1.1, RW3 +0.8, CWT14 +0.7), 2 worsen (L3-fromopen -3.3, NM-ETF -0.8). GB3_50 costs L3 -15.9R. H12 costs RW3 -17.2R. Keep the -20R halt and -2R latch.

## W4 — long/short balance (PARTIAL, 12 configs)

Primary 10-23..11-17: shorts 80% (-45.9R), longs -1.3R. Today's lineup (427 trades, +48.5R): RW3/RW5 carry the down-day dependence (+23.7 down / -14.4 up / -12.2 quiet). L3 is not a direction bet (+28.8R on up days).

| Cap | Today's lineup R (base +48.5) | L3 | Per setup |
|---|---|---|---|
| 60% of 77 slots | +47.7 | 0 | RW5 -0.9 |
| 70% of 77 slots | +48.5 | 0 | never binds |
| 60% of open lots | +3.0 | -46.8 | RW5 +3.7, RW3 -2.4 |
| 70% of open lots | +5.8 | -44.4 | RW5 +6.0, RW3 -4.4 |

Long screen: 62 long setups with >= 20 trades; 8 positive, none positive without its best day. Best low-correlation long: GEN-261020-09 Midday Stretched Dip Buy (+67.1R, but -0.06 w/o best day; 11-13 = 108%; corr -0.24) — keep testing. NM-ETF (+0.26 w/o best day, 92% green) and ST7 are the only longs that hold up, and both are already in Primary.

## W5 — exit overlays (FAIL, 7 configs)

4,626 live trades replayed on 1-min SIP bars with LR8 costs on every new exit; ambiguous bars resolved against the new rule.

| Group | Trades | Base | BE0.5 | BE0.7 | BE1.0 | TS30 | TS60 | PT0.5 | PT0.5+BE |
|---|---|---|---|---|---|---|---|---|---|
| Primary | 724 | -47.2 | -8.4 | -5.4 | +4.1 | +5.4 | +1.4 | 0.0 | -4.2 |
| P: L3-fromopen | 133 | +47.7 | -9.7 | -5.2 | -1.4 | -18.5 | -16.2 | -7.3 | -11.5 |
| Top 10 testing | 3231 | -342.1 | -33.9 | -7.4 | -3.8 | +29.2 | +39.6 | +0.1 | -17.9 |
| Up-and-coming (11) | 671 | +114.4 | -12.9 | -2.8 | +1.3 | -91.7 | -42.7 | -17.8 | -21.7 |
| ALL | 4626 | -274.9 | -55.2 | -15.6 | +1.7 | -57.1 | -1.7 | -17.6 | -43.7 |

Per setup (29 setups >= 20 trades), improve/worse: BE0.5 9/18; BE0.7 8/15; BE1.0 8/8; TS30 14/16; TS60 17/13; PT0.5 12/17; PT0.5+BE 13/16. Time stops move R from winners (RW7 -25.5, NM-RWN4 -20.0, exhaustion_short -18.0, NM-RWR4 -14.4, GEN-261029-06 -13.7, L3-rsi5hi -12.6) to losers (RW3S +28.8, R2A-long +18.7, CWT12 +12.1). No rule improves in both halves. Confirms Part 1: 21.4% of stopped Primary trades first reached +0.5R — but taking that money costs more than it saves. Park: "exit overlays: null (W5, 7 configs)".

## W6 — equity-curve gating (FAIL, 6 configs)

161 setup/account pairs, 23.8k trades. Gains are exposure cuts only: versus a same-exposure random shadow, -44R (MA10), -62R (MA20), -538R (S5) per-account; pooled +21 / -52 / -576. Core-account winners (20 setups, +306R): MA10 -83.5R (7 better / 11 worse), MA20 -94.6R (5/9), S5 -82.2R (2/11). Primary L3 +40.6R falls to +14.0R (MA10) / +11.3R (MA20); On Deck L3's +33.6R day of 10-20 is skipped under S5. Log as rejected.

## W7 — pipeline and contenders (PARTIAL, 9 configs)

116 enabled On Deck / Testing / Gen setups with >= 10 trades, pooled: -1,135R. 32 positive, 8 positive without best day. Early-half rank does not predict later half (Spearman -0.12; of 12 above +0.10 early, 10 turned negative).

**Contenders**

| Setup | Acct | Trades | Avg R | w/o best (share) | Fit -> check | Corr Primary | Note |
|---|---|---|---|---|---|---|---|
| L3-gap-slope-rsi5hi-FD | On Deck | 130 | +0.191 | +0.127 (53%) | +0.17 -> +0.22 | 0.88 with L3 | lost -10R in Primary 10-30..11-10 |
| L3-gap-slope-lowdist-FD | On Deck | 108 | +0.245 | +0.109 (69%) | +0.07 -> +0.60 | 0.86 with L3 | best day 11-12 (rule-change day) |
| GEN-261027-08 Lunch Failed-Breakdown Short | Test B | 64 | +0.212 | +0.143 (50%) | +0.20 -> +0.23 | +0.81 | only contender positive in both halves and not an L3 twin; correlated with Primary |
| CWT09-gapdn-vwaploss-g10 | On Deck | 22 | +0.227 | +0.139 (53%) | +0.33 -> +0.01 | -0.02 | fading; wait for 30 trades |
| NS-short-while-index-up family (NM-RWN3/4/5, NM-RWR3/4) | Test B-F | 106 | ~+0.25 | positive | - | +0.54 | green on Primary's red days 11-02, 11-06, 11-10 |

Watch: RW7 (Test F, 715 trades, w/o best +0.005; shares 56 symbol-days with RW3/RW5).

**Low-rep, high potential**: GEN-261027-01 Late Pullback Buy (16 tr, +0.187, w/o best +0.139, 83% green, corr -0.06, a long; starved by 21 'halted' skips in Gen); NM-RWR3 (11 tr, +0.410); GEN-261026-03 Lunch New-Low Short (21 tr, +0.379, w/o best +0.129); NM-RWN5 (8 tr, +0.543); NM1-cwt09-g10-vwaploss (8 tr, +0.441).

**Drains**: GEN-261022-09 (Gen, 211 tr, -181.8R; -134.6R on 11-17), CWT14-failbrk-pdl-p10-long (Test A, 809 tr, -93.9R; -45.3R last 5 sessions), GEN-261026-05 (Test E, -61.9R), GEN-261029-08 (Gen, -61.7R), GEN-261019-05 (Test D, -57.2R). Also MF2-open-rsimidhi-flowsell-FD (On Deck, -0.65 in the later half).

## Risk to L3 (Gap-Down Recovery Fade) — summary

Nothing recommended here touches it. Every book-wide overlay tested would hurt it: exit rules -1.4 to -18.5R, giveback locks -3.3 to -15.9R, equity-curve gates up to -29.3R, short-share caps -44 to -49R, the w/o-best-day demotion -36.8R. Its sisters (L3-rsi5hi, L3-lowdist) correlate 0.86-0.88 with it and share 16-19 symbol-days (21/43 overlaps vs the Primary book); promoting one would concentrate Primary on one pattern and could take symbol-days from L3 under one-position-per-symbol.

## Ranked ACTION LIST

Apply after hours (16:00 ET or later) only, and only with the owner's yes where marked.

1. **W1-BAR (owner yes needed; process rule, no setup change today).** Admission: >= 30 testing trades after costs, >= 8 traded sessions, avg R w/o best day > 0, >= 50% green days. Demotion: -10R cumulative since admission only. No half-risk sizing. Back-test +19.3R on tested promotions (18 improve / 7 worse), L3 +7.1R. Caveat: fit half -11.1R, check half +30.4R.
2. **W7-TUNE27-08 (owner yes needed; testing copy only).** One ODPREP Workbench tune of GEN-261027-08 as a copy in Testing A or C, pre-registering one exit change (1R target or breakeven after +0.5R). Note W5 found breakeven book-wide is negative, so this is a single-setup hypothesis tied to its flatten-heavy exit profile (53 of 64 trades exit at 15:55).
3. **W7-DRAIN (owner yes needed; testing/Gen only).** Send GEN-261022-09 first, then CWT14-failbrk-pdl-p10-long, GEN-261026-05, GEN-261029-08 and GEN-261019-05, to the next arena / Graveyard review (trimmed-for-low-activity rule does not apply: these are drains, not low-rep).
4. **W2-MTM (optional; testing copies only).** Pre-register a burst-aware control that counts open (mark-to-market) R per setup/family, tested on the RW WB copies in Testing C/D. Primary untouched.
5. **W3-GB5S (optional; shadow only).** Log the +5R peak giveback lock as a shadow flag on open + realized marks; re-check after 15+ sessions. No live effect.
6. **Friday review flags (no decision now):** RW5 (w/o best day -0.005, 10-22 = 104%) and RW3 (+0.025, 89%) are one-day records; L3-rsi5hi / L3-lowdist overlap with L3 before any promotion; keep GEN-261020-09 and GEN-261027-01 (longs) in testing for exposure.

**Drop / do not apply:** avg-R-w/o-best-day demotion; half-risk sizing by edge; sister-lot drop, shared RW3/RW5 latch, combined open-lot caps; GB3/GB8 giveback locks; -12R or -15R halt; first-hour brake on realized R; short-share caps; breakeven, time-stop and partial exit overlays book-wide; equity-curve gating (MA10/MA20/S5). Do not promote any long or either L3 sister now.

## Part 3 next steps

- After hours: apply whichever of W1-BAR / W7-TUNE27-08 / W7-DRAIN / W2-MTM / W3-GB5S the owner approves, via testing copies or a ledger entry, and re-check with `python -m mcf.research.ledger check`.
- Weekly consultant check-in until Primary is positive R day after day: Primary total and avg R w/o best day, per-setup one-day tags, contender table refresh (On Deck / Testing), drains, and the rule changes inside the week.
