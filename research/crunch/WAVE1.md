Educational only — not financial advice.

# Crunch Wave 1 — lead consultant synthesis (2026-11-18, after the close)

Research only. No config, runtime, ledger or setup change was made in Wave 1. Every item below is a **proposal with a reply code**; no final decision without the owner (crunch brief 11-18 ~16:30 ET). Costs are in everywhere (LR8); the locked block 2024-11-01..2025-02-28 was not read by any workstream; L3-gap-slope-fromopen-FD was protected throughout.

Source write-ups (all on `claude/charming-mccarthy-i3rhhr`): `research/crunch/w1_redteam/` · `w2_promodemo/` · `w3_reps/` · `w4_conditions/` · `w5_workbench/` · `w6_external/` · `w7_primaryday/` · `w8_dataquality/`.

**Configurations tried in Wave 1: 2,287** (W1 24 · W2 7 · W3 3 · W4 2,176 · W5 16 · W6 35 · W7 26 · W8 0). Each workstream applied its own bar max(1.5, sqrt(2 ln N)) to its own pre-registered family; nothing in this file adds a new scored test.

**Rule changes inside the evidence windows (10-06..11-18, ledger):** 10-20 twin block; 10-22/23 testing latch off; 10-27 slots; 10-28 Primary ~$4k sizing (slots 160 → 77); 10-29 −2R latch + BAR90; 11-05 ROLL1; 11-11 TEAM-6; 11-12 LR1/LR3/LR7 + LR8 after-cost R + Testing D/E/F; 11-16 ROT1; 11-17 TSZ1 half size + 15 WB copies + promotion hold + shadow run 3; 11-18 GY-BENCH (+ guests), SRCV1. **From 11-19 (approved by the owner 11-18 evening, ledger):** C3 Epoch 1 — NS5 Primary → On Deck, C3-EXIT100 (20 setups → Graveyard), C3-ROT caps, C3-BAR2, C3-WB/WB5 (L3-rsi5hi-WB5 in Live Lab), C3-SCORE, C3-MECH, C3-EARN, BASE1; C3-LEAN was declined. The C3 build is PR #227 (skeptic review pending), so the 11-19 state depends on that merge.

---

## 1. What changed since the wave started (important for reading the proposals)

The owner approved most of C3 on 11-18 evening, *after* the Wave 1 workstreams had been briefed. Reconciling against the ledger:

| Wave 1 item | Status after the C3 approvals |
|---|---|
| W2-EXIT17 (17 EXIT100 setups → Graveyard on Friday) | **Superseded.** C3-EXIT100 already moves 20 setups from 11-19 (the 17 + MF2-FD, MF4-FD + **MF5**). Only the MF5 difference remains (EXIT-MF5). |
| W2-ODOUT (MF2-FD / MF4-FD out of On Deck) | **Superseded** for MF2/MF4 (both in the C3-EXIT100 list). Only the optional RW1-FD part remains. |
| RT-LEAN (C3-LEAN vs USAGE1 contradiction) | **Resolved by the owner:** C3-LEAN declined. USAGE1 stays open as filed. Dropped. |
| RT-WB5 (trim the WB queue) | **Mostly satisfied:** C3-WB5 deployed only #5; #2 and #4 (= W7-TUNE27-08) failed, #1 and #3 not deployed. What is left goes into WBQ1. |
| RT-NS5, RT-EARN, RT-EXIT, RT-UNCAL | Challenge **approved** decisions — flagged in §3. |
| W3-ROT-DRAG / W3-RARE-ON, WB2-PROTOCOL | Amend **approved** C3-ROT / C3-WB rules — flagged in §3. |

Housekeeping note: `docs/live/decisions.json` still lists the C3 codes, W1-BAR and W7-TUNE27-08 as open although the ledger records the owner's answers (C3 yes except C3-LEAN; W1-BAR replaced by C3-BAR2; W7-TUNE27-08 = C3-WB5 #4, failed). Not changed here; the nightly brief should close them.

---

## 2. Findings per workstream (one paragraph each)

**W1 red team (24 configs).** Headline numbers reproduce (P9 Primary −65.8R, 9/31 green; current six +89.8R; L3 +47.7R/133 tr; GEN −772R). Errors: R is not $ times a constant (system 11-12..11-18 −145R/session but +$21/session; Primary −65.8R ≈ −3.5 account R); 62% of pre-11-12 trades carry zero cost; EXIT100-flagged setups later averaged −0.099R vs the arena base rate −0.095R, so EXIT100 frees reps but does not by itself raise system R; NS5's numbers were misstated (green 8/16, not 29%); the "2 green days in 3" ceiling is in-sample (since TEAM-6 Primary is 2/6 green); C3-EARN's earlier half is only +0.045R; SRCV1 text vs `uncalibrated_weight` 0.2.

**W2 promotion/demotion (7 configs, t bar 3.28).** Nothing passes C3-BAR2 today; no Primary member is at −10R. The current six: +40.8R since 10-30 but +1.0R without 11-12. L3-fromopen +0.142 w/o best day (68% share). RW3/RW5 are one-day records. On Deck → Primary: none ready (L3-lowdist fails only the best-day check, 66%). Arena → On Deck: none. EXIT100 now: 18 + MF2/MF4-FD (MF5 held back on +0.258/31 tr in Testing A). No Graveyard resident graduates (closest RW6G1-FD).

**W3 reps (3 configs).** The testing accounts are short of **signals, not slots**: resource skips 0.2-2.4%, peak 10-29% of slots. Signals are lost to spread, the 0.15R cost filter and ETB. So rotation cannot add reps for low-rep setups; they are slow because they rarely fire (GEN-261027-08 ~9 more sessions to 30 tr/15 days; NM-RWN5 ~110). Shadow matches live 98.6% (R corr 0.958, bias −0.049R, pessimistic). WB copies share 64-100% of parent trades — paired tests, not new reps. 14 up-gated GEN setups silent 3 sessions (weak tape, not a bug).

**W4 conditions (2,176 configs, bar 3.94).** 0 of 31 per-setup bespoke rules pass. On later sessions the net +167R is mostly what random trade removal from losing setups gives (+135R): real excess +31.8R vs +550R promised; 8 rules made their setup worse (−58.2R, incl. L3 −18.2R). Condition effects keep their sign between halves only 56% of the time (shrink 0.23x). Time of day, gap and distance from open persist best.

**W5 Workbench (16 configs).** Tunes fail out of sample because selection picks noise (fit gain vs check gain Spearman −0.26; 17 chosen tunes fit +63.6R → check −45.3R). Unpaired copies need 1,000+ sessions to show +0.05R; paired exit overlays need 255-320 trades. WB2 protocol cuts false passes 15% → 3%. Demo: three earlier-exit classes hurt gap-down short fades (−0.025 to −0.030R/trade, 14 of 15 pairs worse); the old protocol would have shipped one. L3-rsi5hi-WB5 refire-off: +0.003R, t 0.11 on the full paired record.

**W6 external (35 configs, bar 2.67).** Vol-managed sizing, late-day SPY momentum, squeeze filter and gap-fade-by-liquidity all failed. PBO: ranking by avg R/trade overfits (0.74) vs by total R (0.24). 0 of 114 setups reach t 3.27 (best L3-fromopen 1.70). Post-hoc lead: MF-family shorts fading a ≥ 2% gap-up, 127 tr −0.558R, skip +70.9R, t 2.14 (below bar), 9 better / 1 worse. L3-fromopen vs RW3 daily R corr 0.74 pooled (conflicts with Part 3's 0-0.03). Outside pages could not be opened (network allowlist); citations rest on abstracts.

**W7 Primary day (26 configs, bar 2.55).** Red days are short squeezes on SPY-up days; −85.6R of the −145.7R red-day loss came from setups already removed (MF2/MF4 −75R). Red days never went green first (giveback is not the problem). RW3+RW5 −25.0R on 12 SPY-up days vs +19.4R on 7 down days. Every structural cap costs L3-fromopen (−2.8 to −31.6R). FLAT25 (+35.9R, green 42 → 58%) is in-sample and negative on the clean early sessions: FAIL.

**W8 data quality (0 configs).** Books are clean (0 mismatches in 32,972 trades; journal $ matches Alpaca within $1-5). What we *act on* is mislabelled: the daily review quotes raw what-if sums (B1; Primary raw +531.9R vs corrected +56.0R; 11 of 51 verdicts flip) and the approved `whatif_corrected` returns 0 (B1b); since-start R mixes cost bases (B2, −742R across accounts); dashboard since-start $ includes the MTUM glitch (B3); open marks and the Primary halt input use the signal price, not the fill (B4); R and $ disagree in sign on 3 of 32 Primary days (B5). Patches P1-P4 with tests pass (778 passed).

---

## 3. Red-team flags on approved decisions

| Approved | Flag | Lead's handling |
|---|---|---|
| **C3-NS5** (NS5 → On Deck, Epoch 1) | Numbers misstated; with 11-18 NS5 is +0.12R / +$252 in Primary. | W1 and W2 agree NS5 is ~0 (W2: −0.050 w/o best day, check half −0.086). The move neither helps nor hurts in expectation; reversing it now churns Epoch 1. **RT-NS5: recommend No (keep the move)**; BASE1 measures it; NS5 is reviewable in On Deck under C3-BAR2. |
| **C3-EARN** (EARN-GO in testing, blackout exception) | Fails the split (earlier half +0.045R); conflicts with BLKOUT (report-day BMO −0.064R, t −3.57). | **RT-EARN: recommend Yes** — hold the testing start until one pre-registered 2-year earnings-season test (Wave 2). |
| **C3-EXIT100** (20 → Graveyard) | Flagged setups later ran at the arena base rate, so the move frees reps but does not raise system R; R gain comes only from archiving. MF5, CWT13-z05-long and GEN-261021-06 had positive recent R. | Keep the rule as rep allocation; system R needs **GY-LIFE / GY-ARCHIVE-20** (still open; −66.5R/session). **EXIT-MF5: Optional** return of MF5. |
| **SRCV1** | `uncalibrated_weight` still 0.2. | **RT-UNCAL: Yes** (also answers the Guild's open UNCAL question). |
| **C3-ROT** | Caps are a drag control, not a playing-time fix (skips 0.2-2.4%). | **ROT2: Yes** — caps only where resource skips > 5%; never bench rare/day-gated setups. |
| **C3-WB** rules 3-4 | 40 paired trades give SE ~0.05R; the pass rule lets a null tune through ~50%. | **WB2: Yes** — WB2 protocol + power-based shadow horizon. |
| **C3-SCORE** corrected what-if | Approved function returns 0 on journal rows; review still quotes raw sums. | **DQ-P1: Yes** (fix to an approved item). |
| C3-BAR2 / C3-EPOCH ceiling | "2 green days in 3" is in-sample; post-selection Primary 2/6 green. | No change; expectations reset in UNIT1 and the Friday review. |

---

## 4. Conflicts between workstreams and how they were reconciled

1. **NS5:** W1 (noise, don't move) vs W2 (C3-NS5 stands). Both measure ≈ 0 → keep the approved move (RT-NS5 No).
2. **R vs $:** W1 RT-UNIT and W8 DQ-RDEF are the same proposal → merged into **UNIT1**.
3. **Cost basis:** W1 RT-COST and W8 DQ-P3 are the same fix → merged into **DQ-P3** (incl. a re-score of W5's exits; W5's demo is paired on the same trades, so its sign is unlikely to change).
4. **Reps:** W2-REPS (rotation priority) vs W3 (signals, not slots, are the limit) → **W2-REPS dropped**: C3-ROT already picks fewest-reps-first and slots are not binding.
5. **WB shadow:** W3-WBSHADOW and WB2-OVERLAY are one idea → merged into **WB2-OVERLAY**.
6. **MF gap-up skip vs no filters:** W6-MFGAP (t 2.14, below bar) vs W4-NOFILTER → consistent as a **shadow tag only** (TAGS1). Primary has no MF setup after C3-EXIT100, so its Primary effect is 0 today.
7. **L3/RW3 correlation:** W6 0.74 pooled vs Part 3 0-0.03 Primary-only → unresolved; Wave 2 item.
8. **Earlier vs later exits:** W5 shows earlier exits hurt the gap-down family; W7-UPDAY points at RW3/RW5 SPY-since-entry exits (also an earlier-exit class) → read the RW3/RW5-WB4 copies paired before any up-day work (C3-MECH).

**Dropped as weak or superseded:** W2-EXIT17, W2-ODOUT (MF2/MF4 part), W2-REPS, RT-LEAN, RT-WB5 (folded into WBQ1), W3-WBSHADOW (into WB2-OVERLAY), W7-UPDAY (into C3-MECH), W6-BREADTH and W6-HKS/SIP (Wave 2 studies, not decisions), W3-SHADOW-INFO / W3-REPCOL / W4-TAGS / W2-HOLDLIST / W2-PRIM / W6-DSR (folded into reporting items or FYI).

---

## 5. Ranked proposals (expected impact on positive R per day; Primary first, then pipeline/reps)

None of these claims an R gain that passed its bar. The top of the list ranks by how directly it changes what Primary does or how Primary's day is judged.

| # | Code | Proposal | Why (one number) | Expected effect | Rec |
|---|---|---|---|---|---|
| 1 | **UNIT1** | "Positive every day" measured in **account R** ($ after costs ÷ 0.25% equity) for the system and Primary; trade R stays for judging setups; days where they disagree are flagged | 11-18: −5.52 trade R but +1.42 account R; since start −71.3R vs ≈ −3.8 account R | Targets match the owner's meaning; small capped lots stop deciding the day's sign | Yes |
| 2 | **DQ-P4** | Open marks and the Primary −20R halt input use the entry fill (after hours, ledger entry) | 11-17: +1.69R (signal) vs +1.18R (fills) | Halt and latch read true risk | Yes |
| 3 | **DQ-P3** | One LR8 cost basis for every record spanning 11-12 (journal unchanged) | pre-11-12 trades flattered 0.035-0.040R each; 5 sign flips (NS5, RW7-FD) | Promotion/demotion on honest records | Yes |
| 4 | **TAGS1** | Journal-only would-skip tags (no order change): 12 point-in-time conditions + FLAT25, RW3/RW5 stacking (L3 exempt), MF gap-up ≥ 2%, W4 watch list; each scored once after 20 fresh sessions | FLAT25 +35.9R in-sample (t 1.76) but −36.7R early; MFGAP t 2.14 | The only clean route to a Primary entry rule; 0 R now | Yes |
| 5 | **W4-FRAME** | Standing framework for bespoke entry rules in Primary (shadow tag → excess over random removal → day-clustered t → keep ≥ 70% trades / 90% winners → one epoch) | 8 of 31 rules lost −58.2R on unseen sessions | Stops false rules | Yes |
| 6 | **STOP2** | Add to Stop-doing: cross-setup entry caps in Primary; live per-setup filters from short samples; earlier exits on gap-down short fades | caps cost L3-fromopen −2.8 to −31.6R | Saves research and avoids harm | Yes |
| 7 | **RT-NS5** | Reverse C3-NS5? | NS5 ≈ 0 in both reviews (−0.050 w/o best day) | Keep Epoch 1 clean | No |
| 8 | **W3-PSHADOW** | On Deck / testing candidates run as shadow setups inside Primary (no orders) | testing misses ~10% of Primary-rule trades; BAR2 needs overlap | Primary-rules record + overlap for promotion | Yes |
| 9 | **WB2** | WB2 evaluation protocol + power-based paired horizon (exits ≥ 120 paired / 15 sessions; gates ≥ 400; early harm stop) | false pass 15% → 3% | Fewer bad tunes reach On Deck | Yes |
| 10 | **WB2-OVERLAY** | Exit/refire variants as paired shadow overlays on the parent's signals, not arena copies (after hours) | +0.05R: 255-320 paired vs 5,000+ unpaired trades | Verdicts in 30-150 sessions; frees slots | Yes |
| 11 | **RT-EARN** | Hold EARN-GO's testing start until one 2-year earnings-season test | earlier half +0.045R | Avoids a split-failing exception | Yes |
| 12 | **ROT2** | C3-ROT caps only where resource skips > 5%; never bench rare/day-gated setups; verdict clock in eligible days (index-gated: per matching day) | skips 0.2-2.4% | Rare setups keep their few days | Yes |
| 13 | **WBQ1** | Queue clean-up: close W7-TUNE27-08 (failed as C3-WB5 #4); no tunes for MF1/MF3/NS3-FD; L3-rsi5hi-WB5 not counted without a paired read-out | WB5 refire-off t 0.11 | No false progress | Yes |
| 14 | **W3-NOGUEST** | No further testing setups sent to the Graveyard as guests (current ones home 11-25) | guests 3 signals on 11-18 | Guests not exposed to Graveyard halts | Yes |
| 15 | **DQ-P1** | Daily review + C3-SCORE use the corrected what-if (fix to approved item) | raw +531.9R vs corrected +56.0R | No false "loosen" findings | Yes |
| 16 | **RT-UNCAL** | `uncalibrated_weight` 0.2 → 0 (matches SRCV1; answers UNCAL) | config 0.2 vs text 0 | Consistency, no trading effect | Yes |
| 17 | **DQ-P2** | Dashboard since-start $ excludes the labelled MTUM glitch | −$11,505.57 shown vs ≈ +$134.66 trading | Honest dashboard | Yes |
| 18 | **W6-PBO** | Never rank by raw avg R; PBO line + try-count t column in the Friday review | PBO 0.74 vs 0.24 | Fewer lucky promotions | Yes |
| 19 | **W3-BENCHSHADOW** | Benched/archived setups keep running in shadow | ~570 GY trades/session not recorded | Records grow, no drag | Optional |
| 20 | **EXIT-MF5** | Return MF5 to Testing A (C3-EXIT100 moved it) | +0.258 on 31 trades in Testing A | One more live test | Optional |
| 21 | **W2-ODOUT** | RW1-FD On Deck → testing | −10.8R since 11-12; whole record −0.028 | Cleaner On Deck | Optional |
| 22 | **W2-HK-GEN09** | Diagnose GEN-261022-09's 144-entry burst and stop slippage (now in the Graveyard) | −134.6R on 11-17 | May expose a cap/slippage bug | Yes |
| 23 | **DQ-B4b** | Manage lots from the entry fill, same before/after the 14:15 handover (exit logic; backlog first) | one lot managed two ways per day | Consistent exits | Optional |
| 24 | **DQ-ODK** | Read-only P/L reconcile of 7 On Deck / Testing A $ gaps with those keys | On Deck 11-05 −$1,585 | Clean $ records | Optional |

Still open from before and directly relevant: **GY-LIFE / GY-ARCHIVE-20** (the largest system-R lever found: the 20 archive names were −66.5R/session), USAGE1, TIER-BIAS, U9-TGT (115 fills −65.3R), U9-ETB, ENG1.

---

## 6. Errors found and corrections

| # | Error | Correction |
|---|---|---|
| E1/B5 | R ≠ $ × constant; sign can flip (3 of 32 Primary days) | UNIT1 |
| E2/B2 | Mixed cost basis at 11-12 (−742R across accounts) | DQ-P3 |
| E3 | EXIT100 "+60-75R/session" — flagged setups ran at the base rate | §3; system R only via archiving |
| E4 | C3-NS5 numbers (29% green → 8/16) | RT-NS5 |
| E5/E6 | In-sample "2 of 3 green" ceiling; "43% since 10-29" is 4/14 = 29% | Expectations reset |
| E7-E10 | Open-code contradictions (C3-WB vs WB5/GY tunes; C3-ROT vs W7-TUNE27-08; C3-LEAN vs USAGE1; C3-EARN vs BLKOUT) | WBQ1; LEAN resolved by owner; RT-EARN |
| E11 | W1-BAR +19.3R flips sign across halves | W1-BAR superseded by C3-BAR2 |
| E12 | SRCV1 text vs `uncalibrated_weight` 0.2 | RT-UNCAL |
| E13-E16 | Replay-bias figures disagree; share denominators; U9 stop-part R inflated; TSZ1 listed twice | Noted in w1_redteam/RESULTS.md; U9-TGT's stop part to be restated before the owner answers |
| B1/B1b | Review quotes raw what-if; approved `whatif_corrected` returns 0 | DQ-P1 |
| B3 | Dashboard $ includes the MTUM glitch | DQ-P2 |
| B4/B4b | Marks and management use the signal price | DQ-P4, DQ-B4b |
| B6 | 7 unexplained On Deck / Testing A $ gaps | DQ-ODK |
| B7 | win rate / profit factor on raw $ next to after-cost avg R | label fix inside DQ-P3 |
| self | W3 first paired on UTC vs ET; W4 merged on id only; W7 latch re-applied on absolute R | each fixed and re-run before write-up |
| P2 vs W2 | EXIT100 count 31 (−1,251R) vs 18 (−760R) | W2 uses per-session snapshots for active days and GY-BENCH moves |

---

## 7. Wave 2 plan (Thursday 11-19 after the close → Friday 11-20 20:30 ET)

All pre-registered (PLAN.md committed before scoring), costs in, locked block excluded, configs counted.

1. **Friday review packet (W2 rerun, ≤ 7 configs):** all records on the LR8 basis (DQ-P3 helper), trade R and account R side by side, BAR2 + one-big-day + PBO/try-count columns, 11-19 and 11-20 added; Epoch 1 vs BASE1 first read (2 sessions — descriptive only).
2. **RT-EARN test (1 config):** EARN-GO on 2-year earnings seasons, outside the locked block.
3. **Fresh-session check of TAGS1 rules (0 new configs):** FLAT25, STACK1+L3x and MFGAP were frozen in Wave 1, so 11-19/11-20 are genuinely unseen; report, don't decide (2 sessions cannot pass).
4. **2-year single-config scores (3 configs):** FLAT25 on the current five, MFGAP on the MF family, W7 SPY-up-day RW3/RW5 profile — on the 2-year live-code replay, reported as a separate source (SRCV1 weight 0).
5. **WB2-NEXT (≤ 10 configs):** later/larger exits (target 1.25x; trail after +1R) on the gap-down family via the calibrated replay; plus the paired read-out of RW3-WB4/RW5-WB4 SPY-since-entry exits.
6. **Correlation recheck (0 new configs):** L3-fromopen vs RW3 and L3-rsi5hi vs NS1 on Primary-only and pooled series, in trade R and account R.
7. **Account-R decomposition of Primary's red days (UNIT1 basis):** which setups and lot sizes decide the sign; how many trade-R red days were account-R green.
8. **W6-HKS / W6-SIP (≤ 3 configs each)** if disk allows 1-minute packs; otherwise deferred.
9. **Builds ready for an owner yes (after hours, no merge):** TAGS1 journaling, W3-PSHADOW, WB2-OVERLAY specs; GEN-261022-09 burst diagnostic.
10. **Outside sources:** W6 could not open any page (network allowlist). If the owner wants full papers read, the session's allowed hosts must be widened in the environment settings; otherwise abstracts only.

Educational only — not financial advice.
