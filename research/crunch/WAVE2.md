Educational only — not financial advice.

# Crunch Wave 2 — lead consultant synthesis (2026-11-19, after the close)

**In plain English (5 lines)**
1. The 11-19 loss came from two rule defects, and tonight's tests point to two fixes: stop short setups from shorting inverse ETFs (INV: +78.8R live, 50 setups better and 24 worse, holds on the 2-year data with a borrow proxy) and leave the shared RSI code alone (fixing it would make 40 of 46 setups worse).
2. ST7-FD's only form that holds up is its original 13:35-15:00 window, and the evidence for that is thin (n 176, t 1.68). If it is used at all, it should run as a new testing copy, not replace ST7-FD in Primary.
3. One exit idea passes: on RW3 and RW5, moving the take-profit to 1.25x adds +0.044R a trade (t 2.58, 6 of 6 weeks positive, none of 5 setups worse). Because RW3 and RW5 are in Primary, the recommendation is a journal-only shadow first.
4. Several ideas fail and should be parked: EARN-GO (−0.070R a trade over 2 years), the FLAT25 and MFGAP skip rules (no better than removing trades at random), trail-after-+1R, and target-from-the-fill. W6's 0.74 "L3 vs RW3" correlation was a labelling bug. The real twins are RW3 with RW5 (0.76) and the two L3 setups (0.74).
5. Primary: no member is at −10R (ST7-FD is closest at −7.3R). Over 33 sessions it lost −133.4 trade R but only −10.0 account R, because the small lots carry most of the R loss. Nothing was decided or committed. 15 decisions are open for the owner, and **31 configurations** were counted in Wave 2.

> **Skeptic review (appended below, "## Skeptic"):** 11 proposals upheld, 4 downgraded (ST7-B, WB2-Y1-SHADOW, WB4-SPY-READ, WB2-NEXT-2). The corrected 5-line summary is there.

Research only. No config, setup, exit, order or ledger change was made by any Wave 2 research item. The housekeeping stop-rounding fix (b38a16981, ledger `2026-11-20-stop-rounding`, owner-approved housekeeping from root cause R3) is the only code change, and it was committed separately by the housekeeping agent. Costs are in everywhere (LR8 basis), and the locked block (2024-11-01..2025-02-28) was not read by any item. Each item pre-registered a PLAN.md before scoring (papers: before reading). Source write-ups: `research/crunch/wave2/{packet,earn,fresh_tags,exits,inverse_guard,st7_fix,papers}/`.

**Configurations counted in Wave 2: 31.** Packet 7, EARN 1, fresh_tags 3, exits 9, inverse guard 7, ST7 fix 4, papers 0. Not counted as new: the exits item also re-scored 2 configs that UPDAY had already counted, and looked at 6 more for description only (its N is 15, bar 2.33). Wave 1 counted 2,287, so the crunch total is **2,318**. Each item applied its own bar, max(1.5, sqrt(2 ln N)), to its own family.

**Rule changes inside the evidence windows (research/ledger.jsonl).** 10-20 twin block. 10-26 ST7-FD to Primary. 10-27 GX1 clock fix. 10-28 Primary sizing (~$4k, slots 160 → 77). 10-29 −2R latch and BAR90. 10-30 L3-rsi5hi to Primary. 11-05 ROLL1. 11-11 TEAM-6. 11-12 LR8 after-cost R. 11-17 TSZ1 half lots, 15 WB copies and the promotion hold.
- **11-19:** C3 Epoch 1 / BASE1 (NS5 out of Primary), C3-EXIT100, C3-ROT/ROT2, C3-BAR2, GY-LIFE, GY-ARCHIVE-20, DQ-P3/P4, UNIT1, U9-TGT, U9-ETB, TAGS1, REPS2-LANE, the conflict-check rule and the testing-admission rule.
- **11-20 (after every window here):** 9 ultimate_1119 admissions (Testing A-F), FOOTRACE-EXIT, GY-FOOTRACE and the stop-rounding fix. The 11-20 forward windows (Compass gate, INV shadow, Epoch 1) therefore start with these changes already in effect.

Any figure that spans 11-12 is re-costed to the LR8 basis. Figures that span 10-28 or 10-29 mix sizing and latch regimes.

---

## Per item

### 1. Friday review packet + item 7, Primary red days (packet; 7 configs)
- **Primary −10R check:** no member is at −10R. ST7-FD is closest at −7.3R since 10-28, and −8.7R of that came on 11-19. Its avg R without its best day is −0.307.
- **The current five:** +63.5 trade R and +18.7 account R (+$4,029) since admission.
- **L3-fromopen:** +0.240 avg R, but +0.066 without its best day, and 11-12 is 82% of its total (`1 day`). RW3 and RW5 are negative without 10-22.
- **C3-BAR2:** 0 setups ready. The L3 twins in On Deck fail only the best-day check (79% / 60%). No Graveyard setup graduates.
- **PBO** (136 setups, 70 splits): shrunk ranking 0.40, total R 0.51, raw avg R 0.61. No setup with ≥ 30 trades reaches the try-count bar (3.24).
- **FOOTRACE-EXIT (preliminary, through 11-19):** 8 arena setups are flagged (7 GEN plus intraday_momentum): 543 trades, −184.8R, −9.4 account R. 16 young WB copies are exempt.
- **Epoch 1 vs BASE1, session 1 (descriptive only):** BASE1 −25.34R / −9.13 account R vs the live book −16.15R / −4.18. The whole +9.19R gap is NS5 (18 shadow lots, 12 of them on the 10:50 bar).
- **Item 7, account R (33 sessions):**
  - Primary lost −133.4 trade R but only −10.0 account R (−23.7 without 11-12). The sign disagrees on 3 days (10-26 and 11-18 were account-green, 11-05 the reverse).
  - Lots under $25 carry 61% of the trade-R loss but only −5.8 account R; $75-150 lots made +9.0 account R.
  - One setup decides the sign on 78% of account-red days. Since 11-11, L3-fromopen has set the sign on 4 of 7 sessions.

### 2. RT-EARN (earn; 1 config) — FAIL
- EARN-GO on 446 sessions of earnings seasons: 1,110 trades, −0.070R, −77.7R in total, day-clustered t −2.44. Without the best day it is −0.079.
- Both halves are negative, and only 2 of 8 seasons are positive (each rests on one day). Longs −0.043, shorts −0.096.
- It is 0.125R worse than a random bar on the same names, and still −0.058 with costs removed.
- Caveats: ULT-28 had already scored a near neighbour, so this is a confirmation; the universe has survivorship bias; the cache ends 11-04.
- EARN-GO has never traded live: C3-EARN was approved on 11-18 and put on hold that same evening.

### 3. TAGS1 on the first unseen session, 11-19 (fresh_tags; 0 configs, reported, not decided)
- FLAT25 flagged 0 Primary trades.
- STACK1+L3x flagged 1 lot; skipping it would have saved +0.58R.
- MFGAP flagged 45 lots that made +13.6R (0 setups better, 5 worse), so the rule would have cost 13.6R. 43 of the 45 lots were Graveyard MF2/MF4-FD trades on one afternoon.
- Housekeeping bug: `tags1.decisions()` counts what-if runs as live (1,664 rows on 11-19), and no job calls the tagger.

### 4. Two-year single-config scores (fresh_tags; 3 configs, SRCV1 weight 0)
- FLAT25 on the current five is not supported: the gain is no better than removing trades at random (4.8th percentile).
- MFGAP on MF1-5 is not supported (44th percentile).
- The RW3/RW5 SPY-up-day profile holds: −0.211 on up days vs +0.078 on down days, Welch t 7.0, and it holds in both halves. It uses a hindsight day label, so it is a profile, not a rule.

### 5. WB2-NEXT exits (exits; 9 configs, bar 2.10)
Verdicts use RW3 + RW5: 383 paired trades over 27 sessions (10-12..11-17). L3-rsi5hi dropped out under the pre-registered rule (best day 102% of its total).

| class | Δ R/trade | t | result |
|---|---|---|---|
| Y1 target 1.25x | +0.044 | 2.58 | **PASS** — permutation p 0.002, 6 of 6 weeks positive, both halves positive; RW3 +11.7R (69 better / 13 worse), RW5 +5.7R (68 / 16); best day is 31% of the gain |
| Y2 trail after +1R | +0.005 | 0.42 | FAIL |
| Y3 target from the fill | +0.026 | 1.58 | FAIL, later half negative |
| SPY-since-entry (WB4 copies, re-scored) | +0.015 | 0.83 | FAIL — the RW5 gain is `1 day` (53%) |

- The descriptive looks at Y1 also all improve: L3-rsi5hi +10.5R, RW7 +11.4R, RW1 +3.3R. None of the five setups gets worse.
- None of these exits would have saved 11-19.

### 6. Correlation recheck (fresh_tags; 0 configs)
- L3-fromopen vs RW3 is 0.05-0.17, and L3-rsi5hi vs NS1 is −0.29 to +0.23.
- W6's 0.74 / 0.76 came from a labelling bug in its tests.py. The real high pairs are L3-fromopen vs L3-rsi5hi (0.74) and RW3 vs RW5 (0.76). This resolves the WAVE1 §4.7 conflict.

### 8. W6-HKS / W6-SIP — deferred
Not run (disk: no 1-minute packs). The papers item found that HKS's result supports the deferral: at lags under an hour, intraday reversal measured on trade prices is bid-ask bounce. Carried to Wave 3.

### 9. Builds (TAGS1 journaling, W3-PSHADOW, WB2-OVERLAY specs, GEN-261022-09 diagnostic) — not delivered tonight
No build report came back in Wave 2. Carried to Wave 3. TAGS1-WHATIF below covers the TAGS1 part.

### 10. Outside sources (papers; 0 configs)
- 10 sources were opened. SSRN and Alpha Architect return 403 even though they are on the allowlist, so of W6's ten sources only HKS was read in full.
- Vidovich-Zerjal: the end-of-day reversal was 6.62 bps in 2023 but 0.85-2.58 bps in 2024-26, so 2023 may have flattered the older record.
- The inverse-LETF sources (Zhao, Murray-Sammon, QuantPedia) support INV.
- Code check: `indicators.py::_rsi` is a 14-bar rolling sum, which is the cause of the 10:45 cliff.
- 3 backlog idea lines were appended to research/backlog.jsonl (configs_tried 0; uncommitted, and test_backlog passes).

### Root cause R1 — inverse guard (inverse_guard; 7 configs)
- **G1 live** (run 1, 10 accounts, 28,118 trades): it removes 224 shorts (−78.8R, −0.35R avg, red on 18 of 27 days).
  - 75 setup-accounts are affected: 50 better (+99.3R) and 24 worse (−20.6R), net **+78.8R** (+55.9R without 11-19). The largest worsening is −2.65R (heat_fade_short-FD, Graveyard). Families: 19 better, 4 worse (−3.1R in total).
  - L3-fromopen (Primary) gains +13.9R. Its avg R without the best day goes from −0.01 to +0.12, and its best-day share from 103% to 70%.
- **G1 on the 2-year data with a borrow proxy:** +79.6R, 36 better / 20 worse, positive in both halves. The lab disagrees on L3-fromopen (−5.4R); the live read is more relevant.
- **Variants:** G2 also passes (+73.6R). G3 fails (one setup worse by −3.12R). The mirror rule for longs is not a live leak and is not proposed.
- **Borrow list:** U9-ETB does not close the leak. Inverse shorts got through 10.4% of the time before 11-19 and 7.2% on 11-19.

### Root cause R2 — ST7 / RSI warm-up (st7_fix; 4 configs)
- **Shared RSI fix, 2-year data:**
  - A-SR (session reset): 46 setups affected, 6 better / 40 worse, −14,361R.
  - A-GA (gap-adjusted): 14 better / 31 worse, −3,395R.
  - Both are worse in both halves. NS5-FD alone loses −56.3R / −47.5R, which also answers PKT-RSI.
  - The live read is positive (+60.5R / +67.3R), but it can only count the trades the fix removes, not the trades it would add.
- **ST7-FD options:**

| config | n | avg R | t | w/o best day | best-day share |
|---|---|---|---|---|---|
| as live | 1,114 | +0.045 | 1.01 | +0.037 | 19% |
| B-WIN 13:35-15:00 | 176 | +0.133 | 1.68 | +0.076 | 46% |
| C-SKIP 10:45 | 466 | +0.034 | 0.74 | +0.014 | 61% (`1 day`) |

- B-WIN is positive in both halves, but the window came out of a 120,500-config search (t_required 4.84). Live, it would have kept 11 trades at −4.34R.
- With the artifact removed, ST7's 10:50-13:30 part is negative (−0.033R).

---

## Ranked proposals for the owner

The owner can reply to any of these with yes / no plus a comment or condition (decision-list rule 2026-11-19). **Friday-epoch** means the change touches Primary, so it can only go live in the Friday after-close window (C3-EPOCH), after an adversarial review (rule 27) and with a ledger entry.

| # | Code | What | Evidence | Per-setup effect | Rec. | Conflicts with standing owner rules | Friday-epoch? |
|---|---|---|---|---|---|---|---|
| 1 | **INV** | Short setups skip inverse ETFs and long-vol products (G1). Backlog item now, plus a journal-only shadow column `blocked_inverse_short` from 11-20. It goes live outside market hours only after at least 10 sessions that pass the pre-registered bar. Replies: "INV yes", "INV live-epoch" or "INV no". | Live +78.8R (+55.9R without 11-19). 2-year data with a borrow proxy +79.6R, positive in both halves. G2 also passes. | 75 setup-accounts: 50 better (+99.3R), 24 worse (−20.6R, worst −2.65R). Families 19 / 4. L3 family +30.4R (7 of 8 better). | **Yes** | It is a setup/filter change, so it goes through the backlog (RESEARCH_RULES 15-17) and never changes during market hours. Playing time / low-rep rotation (11-03 / 11-04): three low-rep L3 WB copies lose most of their trades (T2 WB4 18 of 24, Live Lab WB5 2 of 2, Testing F WB4 3 of 3). The Epoch-vs-BASE1 read must note the guard. The −2R latch is untouched. | Yes, for Primary (L3) when it goes live. The shadow itself is not. |
| 2 | **ST7-A** | Do not change the shared RSI. Log root cause R2-(i) (and PKT-RSI) as tested and failed. | A-SR −14,361R (6 better / 40 worse); A-GA −3,395R (14 / 31); worse in both halves. | Worst affected: NM-RWN4/RWR4, ST7Q, ST7-FD-WB1, ULT-HV2-K and NS5-FD (−56R). | **Yes** | None. Applying the fix would break the remedies rule (2026-11-05: targeted, not broad). | No (no change) |
| 3 | **ST7-B** | Run ST7 in its 13:35-15:00 source window as a **new testing copy**. ST7-FD stays where it is; any Primary review uses −10R / BAR2 as usual. | 2-year data: n 176, +0.133R, t 1.68, +0.076 without the best day (46% share), both halves positive. The window came from a 120,500-config search (t_required 4.84). Live it would have kept n 11 at −4.34R. | ST7 only. As-live ST7-FD is +0.045R on the 2-year data; with the artifact removed, its 10:50-13:30 part is −0.033R. | **Optional** (thin) | Owner policy of 10-09, "full-day versions first". 11-18, tweaked copies are new setups (it enters testing; it does not replace ST7-FD). Promotion hold (11-17). Testing admission (11-19): the parent ST7-FD is not "promising" live (−0.158R), so it would enter as "debatable". Check the C3-WB exception (no copies of a losing parent with 100+ live trades) against ST7-FD's live count across all accounts before admission (Primary alone: 58 trades). GUARDRAILS: no "automatic −FD copies"; this is the reverse, but it is still a variant. Backlog + ledger. | No (testing copy). Replacing ST7-FD in Primary would be. |
| 4 | **WB2-Y1-SHADOW** | Target at 1.25x as a journal-only paired overlay on RW3's and RW5's own signals. Confirm at ≥ 120 paired trades / ≥ 15 sessions, with an early stop for harm. | +0.044R/trade, t 2.58, permutation p 0.002, 6 of 6 weeks positive, both halves positive. Avg R without the best day goes from +0.051 to +0.087. | RW3 +11.7R (69 / 13), RW5 +5.7R (68 / 16). Descriptive looks: L3-rsi5hi +10.5R, RW7 +11.4R, RW1 +3.3R; 0 of 5 worse. | **Yes** | **Workbench hold (owner WB2, 11-18):** WB2-OVERLAY was put on hold, and this needs it lifted for one overlay. Ask: "this may conflict with the WB2 hold of 11-18; do you still want to proceed?" An exit change is never made during 09:30-16:00 (setup-freeze). Done as a copy, it would be a new setup (11-18) and could not be paired. | The shadow is not. A real exit change on RW3/RW5 is. |
| 5 | **EARN-CLOSE** | Do not start EARN-GO. Withdraw C3-EARN's blackout exception and park the idea in the backlog. | 1,110 trades, −0.070R, t −2.44, both halves negative, worse than random (−0.125R), negative before costs too. | None live (never traded). The blackout is unchanged for every setup. | **Yes** | It reverses part of the owner's **C3-EARN approval (2026-11-18)**, so it is asked, not acted on. It agrees with the earnings blackout (10-07) and RT-EARN (11-18). | No |
| 6 | **PKT-FX** | At the Friday review, run the approved FOOTRACE-EXIT on data that includes 11-20. The 8 flagged setups are the preliminary list. | 8 arena setups (7 GEN + intraday_momentum): 543 trades, −184.8R, −9.4 account R. 16 young WB copies are exempt. | Those 8 move to the Graveyard (moves, not switch-offs). The 11-20 admissions are untouched. | **Yes** | None. It applies an approved rule (FOOTRACE-EXIT, 11-19); these are exits, not low-activity trims (11-03). Moves regenerate assignments.json in the same commit (10-20). | No (arena only) |
| 7 | **TAGS1-WHATIF** | Housekeeping: `tags1.decisions()` counts only paper/live runs as live, and the nightly tagger runs, seeded with the 11-19 table. | 1,664 what-if rows were counted as live on 11-19. No caller and no tags/ folder. | No trading effect. It keeps the TAGS1 score honest. | **Yes** | None (it keeps the TAGS1 "score once" approval of 11-18 honest). | No |
| 8 | **CORR1** | Correct W6 X7 / W6-BREADTH, and count RW3+RW5 (0.76) and the two L3 setups (0.74) as roughly one bet each in reviews. | Re-running W6's own method gives 0.07 / 0.01, not 0.74 / 0.76; the high figures came from a column-labelling bug. | Reporting only. | **Yes** | None. Not a cap: STOP2 (11-18) bars cross-setup entry caps in Primary. | No |
| 9 | **TAGS1-HOLD** | Keep FLAT25 and MFGAP frozen and score them once on 12-17, noting the weight-0 lab result against them. | 2-year data: FLAT25 4.8th percentile, MFGAP 44th (no better than random). 11-19: MFGAP would have cost 13.6R. | None until 12-17. | **Yes** | Dropping either early would break TAGS1's pre-registration (11-18) and the locked-score rule, so that is not proposed. | No |
| 10 | **PKT-LOT** | Show "$ per trade R" per setup in the review (display only). | L3 lots carry about $78 of risk vs $25-31 for RW3/RW5. Lots under $25 carry 61% of Primary's trade-R loss but only −5.8 account R. | Display only. | **Optional** | It keeps UNIT1 (11-18: setups are judged by trade R). GUARDRAILS lists sizing tilts, so no sizing change is proposed. | No (display). Any sizing change would be. |
| 11 | **WB4-SPY-READ** | Keep the RW3-WB4 / RW5-WB4 SPY-exit copies running, but do not count them toward promotion until a paired read of ≥ 120 trades. | Paired SPY-exit Δ +0.015R, t 0.83. Over 3 live sessions the copies trail their parents (RW3 −1.04 vs +0.22R; RW5 +2.34 vs +4.70R). | RW3-WB4 and RW5-WB4 only. | **Optional** | **11-18, tweaked copies are new setups judged on their own record:** withholding promotion credit conflicts with that, so ask first. GUARDRAILS: no early-kill verdicts (fewer than 15 days / 30 trades). | No |
| 12 | **UPDAY-PIT** | Backlog only: a pre-registered point-in-time version of the RW3/RW5 SPY-up-day profile. | Hindsight profile: −0.211 on up days vs +0.078 on down days, Welch t 7.0, both halves. | RW3/RW5 family (a profile, not a rule yet). | **Optional** | **GUARDRAILS (11-18): "day-type switches" and "gates on proven setups"** (prior: W4 conditions, 0 of 31 bespoke rules pass, research/crunch/w4_conditions/). STOP2: no live per-setup filters from short samples. W4-FRAME applies. | Yes, if it ever reaches Primary |
| 13 | **WB2-NEXT-2** | One more pre-registered exit class: target at 1.5x on RW3/RW5 (on the 1-minute replay). | Y1: 124 of the 166 trades that hit the parent target went on to 1.25x; the other 42 were flattened at 15:55 (−13.0R). | RW3/RW5 (research). | **Optional** | GUARDRAILS: no replay "meets parent" as a pass; any pass would also need a forward shadow. | No (research) |
| 14 | **PAPERS-FADE** | Research: fade families measure the stretch from today's open, not the prior close (≤ 2 configs, 2-year data). | Miwa (overnight returns do not reverse); W6 MF gap-up fades −0.558R/trade. Not scored yet. | Fade families (research only). | **Optional** | None while it is research. GUARDRAILS: no new CWT12/CWT14 variants (not a CWT family). | No |
| 15 | **PAPERS-YEAR** | Add per-year R and the best year's share to fade-family reviews (reporting only). | 2023 supplies 56% of the 2023-26 end-of-day reversal estimate (Vidovich-Zerjal). | Reporting only. | **Optional** | None (it extends the one-big-day rule of 10-25). | No |

**Closed, superseded or FYI (no decision needed):**
- **PKT-RSI:** done. NS5-FD was in the ST7 shared-RSI test, and the fix makes it worse (−56.3R / −47.5R). See ST7-A.
- **PAPERS-RSI:** largely superseded by ST7-A, because the intraday-only and gap-adjusted RSI were both tested and failed. The only untested variant left (strict session reset that stays blank until 10:45, or Wilder) is optional config 5. It would not be built without a new reason, given the 40-of-46-worse result.
- **PKT-EPOCH:** FYI. Re-read on Friday with 11-20.
- **WB2-GDX-NOTE-2:** a backlog note for the gap-down family (trail and target-from-fill are null; a larger target is positive). This is housekeeping in the backlog.
- **PAPERS-HOSTS:** SSRN and Alpha Architect answer 403 through the proxy even though they are allowlisted. Reading the full papers needs a manual download.
- **"Six Defects" check:** daylight saving ended 11-01, and no hard-coded UTC open times were found in mcf/.

Owner decisions already answered and not re-asked: C3-EARN, RT-EARN, TAGS1, WB2 / WB2-OVERLAY (on hold; WB2-Y1-SHADOW asks to lift it for one overlay only).

---

## Skeptic

Adversarial review, 2026-11-19 after the close. I re-read every item's PLAN.md, RESULTS.md and saved tables, re-checked the headline numbers against them, and looked for hindsight, one-day, look-ahead and lineage problems, for remedies that are not targeted, and for conflicts with owner rules. **The Skeptic adds 0 configurations** (crunch total stays 2,318). No config, setup, exit, order or ledger line was changed. Costs are in, and the locked block was not read.

**Numbers check.** The headline figures in this file match the saved results: inverse_guard/RESULTS.md and live_G1.csv; st7_fix/RESULTS.md; exits/RESULTS.md and data/; earn/scores.json; fresh_tags/RESULTS.md; packet/RESULTS.md. The config count of 31 adds up (7+1+3+9+7+4+0). I found no arithmetic errors. The problems are in interpretation, set out below.

**Corrected 5-line summary (replaces the one at the top for the owner)**
1. **INV (Yes, backlog + journal-only shadow only):** short setups skip inverse ETFs / long-vol products. Live this is +55.9R without the discovery day (+78.8R with 11-19). 50 setup-accounts get better and 24 worse (worst −2.65R). The 2-year data with a borrow proxy gives +79.6R, but only +13.3R in its early half and −5.4R on L3-fromopen. SQQQ+SOXS are 71% of the removed R. Not live-epoch before the shadow reads.
2. **ST7-A (Yes):** keep the shared RSI code. The fairer gap-adjusted fix still makes 31 of 45 setups worse (session reset 40 of 46). The lab sizes (−3,395R / −14,361R) are inflated by no caps and no borrow list, but the direction holds in both halves. **ST7-B is downgraded to No (park):** its 13:35-15:00 window was searched on the same 2-year data, so t 1.68 is in-sample, and live it is 11 trades at −4.34R.
3. **WB2-Y1-SHADOW is downgraded to Optional:** the 1.25x target on RW3/RW5 (+0.044R a trade, t 2.58, none of 5 setups worse) was suggested by W5's look at the same 27 sessions. Counting that lineage (N 31) the bar is 2.62, which it misses narrowly. It leans on 42 trades held to the 15:55 flatten in a down tape. It is a cheap shadow only if the owner lifts the WB2 hold. WB2-NEXT-2 (1.5x) is downgraded to No on the same sessions.
4. **Park:** EARN-GO (EARN-CLOSE Yes: −0.070R a trade, t −2.44; caveat, the spec is a literal reconstruction), trail-after-+1R and target-from-the-fill. **Keep frozen until their single 12-17 score:** FLAT25 and MFGAP (TAGS1-HOLD). The 11-19 MFGAP −13.6R is one clustered afternoon and is not evidence. Correct W6's correlation labelling bug (CORR1), so RW3+RW5 and the two L3 setups each count as about one bet. Fix the TAGS1 what-if count (TAGS1-WHATIF). Apply the approved FOOTRACE-EXIT on Friday (PKT-FX, 8 setups; the flags are not caused by the inverse-ETF defect).
5. **Primary:** no member is at −10R (ST7-FD is closest at −7.3R, of which −8.7R came on 11-19). Over 33 sessions it lost −133.4 trade R but −10.0 account R, because the small lots carry most of the trade-R loss. **15 decisions are open: 11 upheld, 4 downgraded** (ST7-B, WB2-Y1-SHADOW, WB4-SPY-READ to FYI, WB2-NEXT-2). 31 configs were counted in Wave 2 and the Skeptic added 0. Rule changes inside the windows: 10-28 sizing, 10-29 latch, 11-12 LR8, 11-17 TSZ1 / WB copies / hold, the 11-19 C3 batch / U9-ETB. The 11-20 admissions, FOOTRACE-EXIT and stop rounding come after them.

**Per proposal**

| # | Code | Lead rec. | Skeptic | Why |
|---|---|---|---|---|
| 1 | INV | Yes | **Upheld, as backlog + shadow only** | It is targeted: one symbol class, every short setup, 50/24 better/worse with sizes, and no setup worse by more than 3R. It is hindsight-defined (the class was named after 11-19), but it still passes its bar without 11-19 (+55.9R, 45/23). Weak spots: (a) SQQQ+SOXS are 71% of the removed R; (b) the lab ETBp early half is only +13.3R, and the lab disagrees on L3-fromopen (−5.4R), the Primary setup the remedy is meant to help; (c) the live window is one regime. The INV-G1 wording also bundles an **untested** second change, "exposure checks count such a short as long-market". It was not scored, so it is split out and needs its own test. "INV live-epoch" is **not** recommended before the ≥ 10-session shadow, so the bar for that shadow must be frozen in a PLAN before 11-20's open. The playing-time conflict (3 low-rep L3 WB copies) stays with the owner. |
| 2 | ST7-A | Yes | **Upheld** | The direction is robust (both forms, both halves, most setups worse). The magnitudes are not: A-SR adds 56% more trades from a 3-13-change RSI, and the lab has no ETB or caps. Quote A-GA (31 of 45 worse, −3,395R) as the fair form, not −14,361R. The live removal-only read (+60.5 / +67.3R) cannot see the added trades, so it does not offset this. Backlog line papers-1119-rsi-session-boundary is annotated (only the Wilder form is untested). |
| 3 | ST7-B | Optional | **Downgraded → No (park in backlog)** | research/swarm1010/w2_neutral/NOTES.md: the ST windows "were searched on this same history, so they are in-sample". "Both halves positive" is therefore not independent. t 1.68 against a bar of 4.84, live 11 trades at −4.34R, and the 2023-24 round-5 read of FD at −0.016R. Admitting a variant of a live-losing Primary setup during the promotion hold adds a slot for no evidence. (C3-WB check: ST7-FD has 42+16 live trades plus WB1's 8, under 100, so the exception would not bar it. The reason is the evidence.) |
| 4 | WB2-Y1-SHADOW | Yes | **Downgraded → Optional** | Lineage: W5 (16 configs on the same 10-12..11-17 trades) found that earlier exits hurt and proposed "later/larger" exits as the next run. Y1 is the mirror image on the same data, not a fresh test. N = 16 + 15 looks = 31 gives a bar of 2.62 against t 2.58 (it passes at 9 or 25). RW5 alone is t 1.67. The gain comes from 124 extra target hits minus 42 trades flattened at 15:55, so it depends on fades drifting into the close. That holds in a choppy-to-down tape, and RW3/RW5 lose on SPY-up days (UPDAY profile). The method is fine (paired, per-setup, none worse, best day 31%), and a journal-only shadow costs nothing. It stays optional, conditional on the owner lifting the WB2 hold. |
| 5 | EARN-CLOSE | Yes | **Upheld** | Reliably negative, worse than a random bar, negative before costs, and consistent with ULT-28. Caveats: the spec is a literal reconstruction of an unwritten archive rule, and the cache ends 11-04, so it misses the archive's best days (11-05..11-18). Neither caveat makes −0.070R at t −2.44 a reason to start trading it. |
| 6 | PKT-FX | Yes | **Upheld** | It applies an approved rule. Cross-check with INV: of the 8 flagged setups, only GEN-261027-09 had inverse shorts in live_G1 (4 trades, −1.5R of its −20.2R), so the flags are not caused by the defect being remedied. GEN-261029-02 sits on the 15-active-day line, and 11-19 is −6.57R of its −22.3R, so the Friday run should show it with and without 11-19. |
| 7 | TAGS1-WHATIF | Yes | **Upheld** (housekeeping) | Also: item 3 in this file read TAGS1's first fresh session. Those figures are FYI only, and the single 12-17 score remains the only verdict (locked-score rule). |
| 8 | CORR1 | Yes | **Upheld** | Mechanism verified (alphabetical `corr()` columns relabelled in value_counts order). Breadth figures are unaffected. |
| 9 | TAGS1-HOLD | Yes | **Upheld, wording fixed** | The top summary's "should be parked" was inconsistent with "keep frozen until 12-17". Corrected above. Do not cite the 11-19 MFGAP −13.6R: 34 of 45 entries were Graveyard 13:xx lots on one afternoon, which is one clustered day. |
| 10 | PKT-LOT | Optional | **Upheld** | Display only. It keeps UNIT1. |
| 11 | WB4-SPY-READ | Optional | **Downgraded → No (FYI)** | It is moot while the 11-17 promotion hold stands (nothing can be promoted), and it conflicts with the 11-18 tweaked-copies rule. Re-raise only if the hold lifts before a 120-trade paired read exists. |
| 12 | UPDAY-PIT | Optional | **Upheld (Optional), caveat** | Welch t 7.03 is trade-level (11,507 trades, 422 sessions). Trades on the same day are correlated, so a day-clustered t would be much smaller. With the W4 prior (0 of 31 bespoke rules) and GUARDRAILS, it is backlog only, as proposed. |
| 13 | WB2-NEXT-2 | Optional | **Downgraded → No on the same 27 sessions** | It would add to the lineage count that already puts Y1 under its bar, and a 1.5x target raises the regime-dependent 15:55-flatten share. Allowed only on the 2-year replay as a weight-0 source, or after the Y1 shadow reads. |
| 14 | PAPERS-FADE | Optional | **Upheld** | Research, ≤ 2 configs, pre-registered. |
| 15 | PAPERS-YEAR | Optional | **Upheld** | Reporting. It extends the one-big-day rule. |

**Rule-change list gaps (for completeness, research/ledger.jsonl).** Effective 11-18 but missing from the list above: GY-BENCH, SRCV1 (weight 0), ODPREP and recorded quotes. Effective 11-19 but missing: C3-NS5, C3-WB, C3-MECH, C3-SCORE, GUARDRAILS, C3-WB5, LEARN1, RT-UNCAL, the process bundle (W4-FRAME / STOP2), the tweaked-copies rule and the outside-ideas scout. The testing-admission rule is effective **11-20**, not 11-19. None of these changes a number in this file, but GY-BENCH (11-18) and C3-EXIT100 / GY-ARCHIVE-20 (11-19) change which Graveyard setups traded on 11-19, which matters for the 11-19 MFGAP read.

**Files changed by the Skeptic:** this section and the pointer under the top summary; `docs/live/decisions.json` (recommend/why for ST7-B, WB2-Y1-SHADOW, WB4-SPY-READ and WB2-NEXT-2; still open); `research/owner_inbox/2026-11-19.md` (the 4 downgraded DECISION lines relabelled, plus one Skeptic FYI line); `research/backlog.jsonl` (a note on papers-1119-rsi-session-boundary).

Educational only — not financial advice.
