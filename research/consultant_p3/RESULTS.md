Educational only — not financial advice

# Outside consultant — Part 3: full-operation review (2026-11-18)

Research only, run during market hours: no config, code, setup or branch changes. Data: live run (run_id 1) journals from all ten `mcf-data*` state branches, 10-06..11-17 (11-18 left out because it was still open), R = pnl_adj / initial risk, after costs. The locked block 2024-11-01..2025-02-28 was not read. Every workstream split its window into an earlier fit half and a later check half. Part 2 (research/consultant_p2/RESULTS.md) covered Primary overlays; Part 3 covers everything that moves daily and weekly R: the Primary book, day types, research yield, the Workbench, the testing arena, the Move Hunt, execution, sizing and process.

**Configurations tried: 153,401 in Part 3** (P1 153,190 — of which 153,102 are exhaustive 6-8 setup books; P2 17; P3 22; P4 73; P5 21; P6 5; P7 56; P8 13; P9 4 metric checks). Part 2 added 65. Both counts are reported in full under RESEARCH_RULES.

**Rule changes inside the windows (research/ledger.jsonl):** 10-20 twin-symbol block; 10-22/23 per-setup latch off in Testing 1/2; 10-27 slots 160 → 77; 10-28 Primary sizing (~$4k); 10-29 -2R per-setup latch and BAR90; 11-05 Explore 1 / Live Lab low-rep homes (ROLL1); 11-11 TEAM-6 lineup; 11-12 LR8 after-cost R, Testing D/E/F opened; 11-16 ROT1 rotation; 11-17 Testing half-size (TSZ1), 15 WB copies, promotion hold, shadow run 3; 11-18 GY-BENCH, SRCV1. R is per unit of risk, so sizing changes do not distort it; the latch and LR8 change which trades count and their net R.

## Where MCF stands (three views of Primary — they differ, and why)

| View | Sessions | Total R | Green days | Median day | Note |
|---|---|---|---|---|---|
| Primary journal as traded (all lineups) | 31 | -65.8R | 9 (29%) | -3.83R | Top 2 days +105.7R, other 29 -171.5R; worst -31.2R; 9 days ≤ -10R |
| Current six as traded in Primary | 31 | +89.8R | 14 (45%) | — | Daily SD 13.5R; gap-up opens -29.8R over 10 days |
| Current six pooled across accounts (book) | 26 | +158R | 62% | +2.30R | +113.6R w/o best day; 5 of 6 weeks green |

- Everything outside L3-fromopen, RW3 and RW5 made -153R in Primary (P3). Twelve live-record promotions: the three gap shorts +87R, the other nine -77R.
- Dashboard R overstates dollars 4-9x: the ~$4k position cap, not 0.25% risk, sets size. P6's +92.2R on the dashboard = +21.8R in account terms (P8).
- The honest ceiling with today's pool is about two green days in three (P1). There is no setup in the arena that turns Primary's losing days green (P2).

## Per-workstream findings

| WS | Verdict | Configs | Key number | Kept as |
|---|---|---|---|---|
| P1 portfolio | PARTIAL | 153,190 | Green-%-optimised books: fit 92% → check 31% green, -75.6R; only NS5 drop holds in both halves (+8 pts green, +4.1R) | C3-NS5, C3-BAR2 |
| P2 day type | FAIL (switches) / PARTIAL (leads) | 17 | Current six -29.8R on 10 SPY gap-up days, but the sign flips across halves; 0 of 67 setups positive on gap-up days in both halves | C3-SCORE (tag), C3-MECH (gap-up hunt), watch list (DN10) |
| P3 research yield | PARTIAL | 22 | 11 of 135 setups (8%) positive w/o best day; losers persist (100+ trades & ≤ -0.05R → -0.107R later, -585R in 8 sessions); gap mechanisms -0.008R/trade vs -0.140R | C3-EXIT100, C3-WB, C3-MECH, C3-BAR2 |
| P4 Workbench | PARTIAL | 73 | Tighten/gate helps losing parents (9/14, 5/6), hurts proven ones (4/4 total R down); -FD widening -294R over 14 pairs; 60/60 variants passed in-sample | C3-WB, C3-WB5 |
| P5 arena | PARTIAL | 21 | 30-trade record does not predict the next 30 (Spearman 0.03); early-kill backfired 10/10; CWT14 = 37% of arena trades | C3-ROT, C3-EXIT100 |
| P6 Move Hunt | PASS (one lead) | 5 | 58% of top moves are earnings blackout names; EARN-GO +0.346R/trade, n 121, t 3.6, +0.241 w/o best day (earlier half only +0.045) | C3-EARN, C3-MECH (09:35 harness), C3-SCORE (capture buckets) |
| P7 execution | FAIL (as lever) | 56 | Skipped signals would have lost -2,211R; spread skips -4,100R net of spread; latency adds ~0 | C3-SCORE (what-if fix), C3-MECH (ETB universe) |
| P8 sizing | FAIL | 13 | Tier weighting fit +13..+23R, check -33..-47R; daily caps cut R 50-100% | Stop list; watch list (L3 cap) |
| P9 process | PARTIAL | 4 | Median day stable (-3.83 / -4.35) while total swings (-12 / -54); 6.5 rule changes per session; Guild 0 passes in 78 ideas | C3-SCORE, C3-EPOCH, C3-LEAN |

## Conflicts resolved

1. **Promotion evidence: W1-BAR (30 trades) vs PROMO150 (150 trades) vs P5-DAYS (15 active days).** W1-BAR is the only one back-tested on past promotions (+19.3R, 18 improve / 7 worse). PROMO150 would have blocked it as a hard rule with no back-test of its own. Resolution (C3-BAR2): keep W1-BAR's thresholds, add 15 active days, score on the twin-symbol-adjusted (non-overlap) record, and show the shrunk estimate n/(n+150)·avg + 150/(n+150)·(-0.10) in every brief as a required column; a promotion needs it > 0. Demotion stays -10R since admission only.
2. **Kill rules: EXIT100 vs P5 "early kill backfired 10/10".** P5's failures were at 5-8 active days; EXIT100 acts at 100+ trades and 10+ sessions, where P3's split showed persistence (-0.107R later, 6/30 recovered). Both hold: no verdicts before 15 active days and 30 trades; EXIT100 only at 100+ trades, 15+ active days, avg ≤ -0.05R and w/o best day ≤ 0.
3. **Tunes on losing parents: TUNEGATE (no tunes below -0.03R) vs WB-PLAYBOOK (tightening rescues losing parents).** P4's rescues were on small parents (CWT09-g5 22-trade children, NS3 gated children); P3's zombies are large records (CWT14 9,539 trades). Resolution: a losing parent with 100+ trades goes to EXIT100, not the Workbench; a losing parent under 100 trades gets at most one threshold or gate tune (ODPREP). CWT12/CWT14 are closed to new variants, so P4's CWT14 tune is dropped from the top-5 queue and replaced by W7-TUNE27-08.
4. **Workbench pass evidence: WB-SPLIT (out-of-sample sessions) vs WBLIVE (live paired shadow A/B).** Sequential, not competing: split-validate before deployment (stops the 60/60 in-sample passes), then pass/fail on 40+ paired shadow trades in 5+ sessions.
5. **L3-lowdist promotion: P2 and W7 rank it first; P1 shows 46% of its trades (66% of its R) duplicate L3-fromopen.** Its non-overlap record (+9.8R, fit -5.6R, +0.5R w/o best day, best day 95%) fails today. It stays first in line, judged on the non-overlap record once the promotion hold lifts.
6. **Primary numbers.** P1 (+158R pooled, 62% green), P2 (+89.8R as traded) and P9 (-65.8R journal) use different series; all three are shown above and the scorecard uses Primary's own journal per epoch.

## Ranked plan (Primary first, then the pipeline)

Ranked by expected effect on Primary daily/weekly R, then by arena/research R and effort. All changes after hours (16:00 ET or later); Primary changes need the owner's yes; the 11-17 promotion hold stands (a demotion is not blocked by it).

| # | Code | Change | Evidence | Expected effect (honest) | Effort |
|---|---|---|---|---|---|
| 1 | C3-NS5 | Move Big Loser Flush Buy (NS5-sma50-flush-oversold-long) out of Primary into Testing 1 or 2; regenerate docs/live/assignments.json and add a ledger entry in the same commit; Primary runs 5 setups until a candidate clears C3-BAR2 | 41 trades -0.9R, green on 29% of its days, -4.0R w/o best day; the only drop/add of 59 that improved both halves | Book green days 62% → 69% (fit +8 pts, check +8 pts), +4.1R over 26 sessions; Primary journal median day -1.10 → -0.64R. Small but positive in every view. 0 setups worse | S |
| 2 | C3-BAR2 | Promotion standard = W1-BAR + 15 active days + non-overlap record + shrunk estimate > 0 + best-day share < 50%; demotion -10R since admission only; never choose books by green %; per-setup risk stays flat | W1-BAR back-test +19.3R (18/7); bad promotions cost -10 to -45R each (10-20 batch -58R); green-% book search lost 75.6R in check | Fewer churn losses; no candidate qualifies today; L3-lowdist first once the hold lifts if its non-overlap record is positive w/o best day | S |
| 3 | C3-EPOCH | Primary lineup/rule/sizing changes only in the Friday-after-close window; each opens a numbered epoch; approve BASE1 (journal-only baseline twin) and judge Primary changes by the same-day paired difference; promotion/demotion suggestions weekly | 200 ledger entries in 31 sessions; daily SD 19.2R means ~164 sessions to see +3R/day in totals | Verdicts in weeks, not months, if the paired SD is < ~8R; no direct R claimed | M |
| 4 | C3-EARN | EARN-GO (earnings reaction-day gap-and-go, pre-registered single config) in one Testing account at half size; narrow exception to the earnings blackout for this setup only | n 121, +0.346R/trade after costs, t 3.63, +0.241 w/o best day, best-day share 35%; earlier half only +0.045R | Planning number +0.1R × ~6 trades on earnings days ≈ +0.5R per session in Testing, ~0 outside earnings season. Takes no R from other setups. Not in Primary until it passes 20 sessions / 60 trades | M |
| 5 | C3-EXIT100 | Friday rule: Testing/Gen/On Deck setup with 100+ trades, 15+ active days, avg R ≤ -0.05 and w/o best day ≤ 0 is proposed for the Graveyard (not a low-activity trim); freed slots go to the lowest-rep setups. Covers W7-DRAIN | Flagged setups went on at -0.107R/trade (-585R in 8 sessions), 6 of 30 recovered; 31 assigned setups meet it now (-1,251R) | Arena paper R +60-75R per session; ~650 trades/session of exposure to low-rep setups. Primary not directly affected | S |
| 6 | C3-WB | Workbench reform: tune type by parent record (proven parents: exits/frequency only; small losing parents: one threshold or gate step); no tunes or copies for losing parents with 100+ trades; max 2 changed parts per copy; diagnose on early sessions, score on later sessions + 2-year; final pass by paired shadow A/B (40+ trades, 5+ sessions); no automatic -FD copies; refire only on setups with avg R > 0 | 60/60 in-sample passes; -FD copies -294R over 14 pairs; filters on proven parents lowered total R 4/4; CWT14 tune ran 7,953 trades of a -1,235R family | Pass rate ~40-60% instead of 100%; ~300R less arena drag over a comparable stretch; research time moves to parents that can turn positive | M |
| 7 | C3-WB5 | Next tune queue (one copy each, twin accounts apart): (1) CWT09-gapdn-vwaploss g10 → g15 + day-open filter; (2) NS3 failed-VWAP-reclaim short, 09:50-10:30 + SPY/QQQ up; (3) MF2-FD / MF4-FD with NM-MF3's 2-part gate; (4) GEN-261027-08 one exit change (= W7-TUNE27-08); (5) L3-rsi5hi-FD refire off | CWT09 g5→g10 -0.366 → +0.227; NM-MF3 -0.176 → +0.152; GEN-261027-08 +0.212, positive in both halves; L3-rsi5hi refires +0.219 → -0.220 late | 2 of 5 becoming steady positive testing setups in ~3 weeks at +2-5R/week each. Items 2 and 3 are one-day-carried (flagged) | M |
| 8 | C3-MECH | Research direction: every new setup card carries a mechanism tag (day-type condition + falsifiable reason); ~60% of new-setup work on day-type-conditioned candidates; GEN output 1-2/day inside those conditions; sibling variants ≤ 50% symbol-day overlap; first studies: Move Hunt on the 11 SPY gap-up sessions, a 09:35-09:45 decision-frame harness, an easy-to-borrow short universe in backtests/generator/promotion screens, an L3/RW family lane in one testing account | Gap mechanisms -0.008 vs -0.140R/trade, 7/20 vs 4/115 robust; GEN 89 setups -776R; 64% of tradable top moves decide by 09:45; L3 shorts 56-60% ETB-blocked live | Candidate base rate from ~8% robust to an estimated 15-25% (estimate, not validated); research records closer to what live can trade | M |
| 9 | C3-ROT | Arena reps: count reps in active days, no verdicts before 15 active days and 30 trades (bugs excepted); session rotation caps of 2 CWT14 variants and 6 GEN setups per session (benched, logged); shadow days as a separate rep column that orders the rotation; triage list every 2 sessions of zero-signal and 60%+ blocked setups (stay enabled, tagged) | 63% of arena trades on 19% of setup-days; CWT14 37% of arena trades; 107 setups < 30 trades, median ~56 sessions to get there; shadow vs live r = 0.98 | Frees 25-35% of opening slots/buying power; whole arena to 15 active days in ~3-4 weeks instead of months; no live-R claim | S |
| 10 | C3-SCORE | Scorecard line in the nightly brief and Friday review (see below), plus account R ($ ÷ 0.25% equity) next to dashboard R, a point-in-time SPY day-type tag, Move Hunt capture in three buckets, and the what-if accounting fix (first signal per name-day, spread and 0.05R haircut, no unfillable rejects; drop the latency/stop-entry hint) | Total R steered by 1-2 days (top 2 = +105.7R); what-if 'max positions/setup' +289R raw vs -22R deduplicated; capture 4.8% headline vs 11.5% on tradable moves | No R by itself; stops false "loosen this filter" calls and one-big-day decisions | S |
| 11 | C3-LEAN | Pause the Guild (5 roles, 60 runs/day) and Reddit scout; drop nightly Top-5 Part B; use the slot for HK-LATCH, HK-FLAT-1113, HK-GEN-BP, HK-HALT-RESTART, OPS-SCHED-0847, one per night; ROUTINE decisions take the stated recommendation after 2 silent nights (MONEY decisions still need a yes, max 3 a night); lean cadence (one start guard, one 30-min in-session check, one ≤150-word brief) | Guild 78 ideas / 174 configs / 0 passed; Reddit 26 / 0; Top-5 B 378 variants / 0 to Testing; 17 open decisions, 11 of them 6-11 days old | ~60 fewer agent runs a day, no measurable edge lost; HK fixes recover rejected entries (small, not quantified) | S |

**Weak or dropped:** P2-DN10 (RW3/RW5 1.5x when SPY down at 10:00; 6 sessions, RW3 '1 day' tag) and P8-CAP-WATCH (L3 cap 30 → 45; one day, 11-12) are kept only as pre-registered watch items with no live change. P5-SHADOW's "promotion uses live only" stays (SRCV1). P2-L3TWIN and P1-NONOV are folded into C3-BAR2. P4 CWT14 stacking is dropped (TUNEGATE). Nothing here touches the exit or latch rules.

## Part 2 decisions — where they land

| Part 2 code | Status in Part 3 |
|---|---|
| W1-BAR | Kept, extended as C3-BAR2 (a yes on C3-BAR2 answers W1-BAR) |
| W7-TUNE27-08 | Kept as item 4 of C3-WB5 |
| W7-DRAIN | Folded into C3-EXIT100 (all five drains meet it) |
| W2-MTM | Still optional; testing copies only. Lower priority than C3-WB5 |
| W3-GB5S | Still optional, shadow only |

## Protect

- **Gap-Down Recovery Fade (L3-gap-slope-fromopen-FD):** +47.7R in Primary 10-23..11-17 (+16.7R w/o best day; 11-12 = 65%), +90.8R over 379 live trades across accounts, +0.191R w/o best day, edge carried forward (+0.18 → +0.32R/trade). Its refire is ~+52R and positive in both halves. Dropping it from the book costs ~95R and 15 points of fit-half green days; it is the book's diversifier (corr 0-0.03 with RW3/ST7). No gates, windows, sizing tilts, caps or exit overlays on it; only testing copies.
- **RW3 / RW5 and NM-ETF / ST7 in Primary.** Dropping RW3 or RW5 cuts total R by 23-35R; NM-ETF and ST7 each add one check-half green day. RW3/RW5 are one-day records (89% / 104%) and negative after 11-06: watch, do not trim (Part 2 closed caps and shared latches).
- **Every execution filter and market entries.** Skips saved ~1,300R at engine costs; spread filters ~4,100R net of spread, ~140R in Primary.

## Stop doing

- Choosing Primary books by green-day % or smoothness (fit 92% → check 31% green, -75.6R), day-type switches and hedge promotions (no classifier keeps its sign; hedges swing ≤ 3.9R vs Primary's 13.5R), sizing tilts and daily trade caps (check -33 to -47R).
- New CWT12/CWT14 variants and top-5 execution tunes (18 setups, 10,807 trades, -1,418R; ~12.4M configs, 0 live winners); automatic -FD copies (-294R); stacking 3-5 changes in one copy; gates on proven setups.
- Treating replay / 2-year "meets parent" as a pass (rank corr ~0), early-kill verdicts on short records (backfired 10/10), and trade counts as reps.
- The Guild, Reddit scout and nightly Top-5 Part B (0 passes from ~480 ideas/variants); daily GEN output without a mechanism (-776R).
- Reading raw what-if sums as "rule cost us R", and latency / streaming / limit-entry projects (latency adds ~0; passive fills pick the -0.22R trades).

## Two-week implementation schedule (after hours only)

Thanksgiving: market closed Thu 11-26, half day Fri 11-27 (13:00 close).

| When (ET) | Work | Needs |
|---|---|---|
| Wed 11-18 after 16:00 | Owner answers C3 codes. Housekeeping that ships without a yes once tests pass: C3-SCORE scorecard line, account R column, day-type tag, what-if fix (reporting only) | — |
| Thu 11-19 | C3-LEAN: pause Guild + Reddit + Top-5 B; HK-LATCH first. C3-ROT active-day and shadow rep columns | C3-LEAN, C3-ROT yes |
| Fri 11-20 after close (window 1) | Epoch 1 opens. C3-NS5 move (assignments.json + ledger, ledger check). BASE1 twin on. C3-EXIT100 first list to owner. C3-ROT family rotation from Monday. Weekly check-in #1 | C3-NS5, C3-EPOCH, C3-EXIT100 yes |
| Mon 11-23 – Wed 11-25 | C3-WB rules into research/workbench/RULES.md and backlog gates; C3-WB5 copies, one per night, each split-validated, ≤ 2 parts; HK-FLAT-1113, HK-GEN-BP | C3-WB, C3-WB5 yes |
| Wed 11-25 | C3-EARN: EARN-GO setup in one Testing account at half size, backlog + ledger entry (configs_tried 5) | C3-EARN yes |
| Fri 11-27 after 13:00 (or Mon 11-30) | Window 2: C3-BAR2 written into RESEARCH_RULES; non-overlap re-score of L3-lowdist / L3-rsi5hi (no promotion while the hold stands); EXIT100 list #2. Weekly check-in #2 | C3-BAR2 yes |
| Mon 11-30 – Thu 12-03 | C3-MECH: mechanism tag in backlog.py, gap-up Move Hunt study, ETB universe in backtest/generator, 09:35-09:45 harness spec | C3-MECH yes |
| Fri 12-04 (window 3) | Score epoch 1 vs BASE1 twin (paired SD target < 8R); first WB copy read-outs (not verdicts before 15 active days) | — |

## Weekly check-in scorecard (Friday, Primary per epoch)

| # | Number | Now | Target |
|---|---|---|---|
| 1 | Primary median day R, last 10 sessions | -3.8R (journal); current-six book +2.3R | > 0 |
| 2 | Primary green-day %, last 20 sessions | 29% (journal); 43% since 10-29 | ≥ 50%, then ~2 in 3 |
| 3 | Worst day / days ≤ -10R, last 20 | -31.2R / 9 of 31 | no day below -15R |
| 4 | Week R w/o its best day, and that day's share (1-day tag ≥ 50%) | — (new) | > 0, share < 50% |
| 5 | Primary account R ($ ÷ 0.25% equity) next to dashboard R | +21.8R vs +92.2R (P6) | both > 0 |
| 6 | Arena: R per session of EXIT100-flagged setups still live; low-rep setups reaching 15 active days | -585R / 8 sessions; 107 under 30 trades | 0 flagged live; +15/week |
| 7 | Open owner decisions older than 3 nights | 11 | 0 |

Every check-in lists rule changes inside the week from research/ledger.jsonl.

## Caveats

Six weeks of live data (31 sessions; Testing D/E/F only 5); fit/check halves of 13-16 sessions, so one green day ≈ 8 points. Pooled series average across accounts; P1 applied the -2R latch to every account although testing ran without it from 10-22/23. EARN-GO's result sits in the later half during peak earnings season (without 11-05 and 11-09: +0.145R). EXIT100's -585R avoided is from 8 later sessions. MECH60's 15-25% yield is an estimate. The shadow-vs-live match covers two sessions. The 'raised' field P9 asks for in decisions.json needs a schema-test change (tests/test_decisions_json.py fixes the key set), so it is part of C3-SCORE's housekeeping, not done here. Scratch directories of all workstreams were deleted.
