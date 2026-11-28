# Proposals from the 2026-11-27 exploration night, ranked by expected effect on weekly R

Educational only — not financial advice. Data, cost basis, configuration count (about 9,656 cumulative, including cycle 2) and the rule changes inside the 10-23..11-27 window are as stated at the top of [DECISIONS.md](DECISIONS.md). All weekly-R figures are for **Primary** unless marked arena. Each figure is an honest range, and most of each range is "trading less", not edge.

**One-paragraph verdict of the night.**
- Seven tracks and seven reviews found no positive edge after costs, long or short, in any condition. Friction is about 0.13R per lot, against a gross edge of about −0.02 to +0.03R.
- Losses are lumpy. Primary's worst 5 days are 64% of its losing-day R, and all 5 were short "baskets" (one setup with many same-side lots stopped together by a broad move). Costs are only 11% of those days.
- Every lever that helps works by cutting exposure on bad days. So the ranking below puts **tail insurance and exposure** first. The **search for a positive edge** comes next; it is the only thing that can produce green weeks, and it runs as frozen forward tests.

| Rank | Proposal | Primary R/wk (range) | Tail effect | Reviewer status | Starts Monday? |
|---|---|---|---|---|---|
| 1 | LATCH-OPEN (card) | +1 to +5 | 11-25: −40 → −8R; bench ≤ −20R days −75% | Reviewed earlier (inspector_1127); tonight: mechanism holds | Only with override (D1) |
| 2 | L3-OUT (card) | 0 to +4 (live +0.6, bench +1.8..+3.9) | Day sd −42%, worst-5 −108 → −69R (live roster) | Shorts reviewer: "restrict" reasonable | Only with override (D2) |
| 3 | PRIM-EXPOSURE: RW5 out (new, 12-04) | +1 to +4 | Day sd 9.1 → 5.5 | Not reviewed (decision support only) | No (12-04) |
| 4 | ARENA-LATCH-F (new) | 0 Primary; Testing F about 0 outside squeeze days | Testing F worst day −261 → −63R (replay) | Shorts reviewer: tail insurance only; needs a same-day random-cut control (added) | Yes, if approved by Sunday |
| 5 | B8-SHADOW (card) | 0 (log) | Option value on midday-flip days | Reviewed earlier; tonight's metrics P3 adds an exposure-cut test | Yes (log) |
| 6 | TAGS2 frozen would-skip set (new) | 0 now; at most +0 to +10 if a rule later passes | Depends on the rule | Each rule carries its reviewer-corrected control | Yes |
| 7 | PAIRED-CARD scoreboard (new) | 0 direct; +0 to +1.5 per real card, adopted 3-6 weeks sooner | — | Dev reviewer: sound; same-day net-R fix added | Yes |
| 8 | FROZEN-BLOCKS + GY-SHADOW/TWIN (structure) | 0 direct; 0 to +3 after 4-6 weeks | — | Dev reviewer: P3 speeds optimistic (corrected) | Blocks yes; twin 12-04 |
| 9 | LONG-SURVIVORS scoreboard (new) | 0 (arena about +1 to +2, 95% band −8..+10) | — | Long reviewer: sound; prior pass chance 10-15% per setup | Yes |
| 10 | Stage-1 scorecard + review rules (new) | 0 (stops variance-driven decisions) | — | Metrics/outside reviewers: hold | Yes |
| 11 | HS-SCALE shock-only (card) | 0 | Glitch failsafe | Reviewed earlier | 12-04 |

Not proposed (failed tonight, do not re-run): basket cap as a Primary rule (58th percentile vs random on the 11-30 roster, day t 0.30), RISK-BUDGET sizing, setup equity-curve governor, first-hour stop, Primary book budget, vol-regime switches, condition filters for shorts (0/8 on 71k bench lots), long cell filters (0 positive cells with ≥ 300 lots).

---

## 1. LATCH-OPEN: the −2R per-setup latch counts open R too (existing card)
- **Evidence:**
  - [neveragain_1125](../research/neveragain_1125/REPORT.md): 11-25 full-day replay −40.1R → −8.3R; bench days ≤ −20R 33 → 8 in 2.9 years; E = 1.00 on CHECK (insurance).
  - [loss_anatomy](findings/loss_anatomy.md) §1: 30 L3 lots were open before the first stop, so the closed latch could not act. Reviewer: "holds as a mechanism".
  - [regime_filters](findings/regime_filters.md) F2a: on Primary the per-setup latch already does what a book budget would.
- **Expected weekly R:** +1 to +5 on today's losing book. Bench CHECK goes from −3.03 to −2.05 R/day with L3 in the book, which is +4.9 R/wk, all from exposure. If the book earned +0.10R per lot it would cost about −1.7 R/wk.
- **Risk:**
  - It trims recovery days (11-12 L3 +31 → +1R).
  - rules_1122: a closed latch was −68R vs a random trim to 11-20, and the gap-down family is worse under a latch outside squeeze days.
  - A new live code path (tested, default-off today).
- **Experiment:**
  - Account: Primary.
  - Baseline: BASE1 twin shadow / journal counterfactual of the skipped lots (what-if rows, LIVE-L costed).
  - Duration: 20 sessions.
  - Success: no day below −20R caused by a setup that LATCH-OPEN latched; skipped lots average ≤ 0R after costs; R given up on recovery days reported per setup.
  - Paired read via PAIRED-CARD at 12-11.
- **Reviewer status:** card reviewed by inspector_1127 (#6, #14). Tonight: supported, no new counter-evidence beyond rules_1122.

## 2. L3-OUT: L3-gap-slope-fromopen-FD Primary → On Deck (existing card)
- **Evidence:**
  - [primshorts_1126](../research/primshorts_1126/REPORT.md): bench removal +0.77 / +0.36 R/session, t 3.4 / 3.7; L3 live w/o best day −0.204 vs RW3 −0.037 / RW5 −0.057.
  - [roster_options_out.txt](sandbox/decisions/roster_options_out.txt): on the live roster, L3 out leaves total R about unchanged (−30.1 → −27.0R) but day sd goes 15.8 → 9.1, worst day −42.3 → −25.7R, worst-5 −108.1 → −68.7R.
  - [shorts_autopsy](findings/shorts_autopsy.md) §4: "restrict".
- **Expected weekly R:** 0 to +4 (live +0.6; bench +1.8 to +3.9, size effect).
- **Risk:**
  - Loses L3's windfall days (11-12 +31R, 11-16 +16R).
  - Adds an 8th L3 copy to the arena, where On Deck has no per-setup stop (On Deck −391R on 11-25).
  - Skips the PRIME-RULES probation step, so it needs your override.
- **Experiment:** Primary without L3 vs the roster shadow, plus On Deck's L3 record.
  - 20 sessions.
  - Success: Primary day sd ≤ 10R and worst day ≥ −25R, with total R no worse than the live roster shadow by more than 5R.
  - L3's On Deck record is re-scored for C3-BAR2 at 20 sessions.
- **Reviewer status:** consistent with every review tonight. Both live records are `1 day`, so the bench drives the call.

## 3. PRIM-EXPOSURE: RW5 out as well (new; question for 12-04)
- **Evidence:**
  - Worst live Primary short (−2.3 R/wk) and worst on T2 (−0.182R per lot).
  - −21.4R on SPY gap-up days, but +21.1R on flat-open days ([shorts_autopsy](findings/shorts_autopsy.md)).
  - rwout: removal +0.91 / +0.80 R/day on the bench, a size effect.
  - Live roster table: L3 + RW5 out gives day sd 5.5, worst day −10.2R, but green weeks drop from 2/6 to 1/6.
- **Expected weekly R:** +1 to +4 (size).
- **Risk:** a thinner Primary means fewer lots to learn from, and RW5 has the best flat-day record of the three shorts.
- **Experiment:** decide at 12-04 from week 1 of LATCH-OPEN / L3-OUT data. If moved, same success bars as #2.
- **Reviewer status:** not reviewed tonight (built here as decision support from the live table).

## 4. ARENA-LATCH-F: closed −2R latch in Testing F for one frozen 2-week block (new)
- **Evidence:**
  - [shorts_autopsy](findings/shorts_autopsy.md) P2: live replay Testing F worst day −261 → −63R, +36 R/wk.
  - [loss_anatomy](findings/loss_anatomy.md): arena 11-25 −1,160R; arena latch +1,221R, 100th percentile vs random lots, but random lots in the same setup-days save more (1,599R).
  - Owner 11-22 approved a latch-for-every-setup study.
- **Expected:** Primary 0. Testing F: tail cut; R about 0 outside squeeze days (rules_1122: size trim, −68R vs random).
- **Risk:** fewer live reps for setups that start the day badly (the what-if run still records them, as a gross bar simulation). It is in-session throttling in a testing account, so it needs an explicit, time-boxed owner exception to the playing-time rule. One account only.
- **Experiment:**
  - Account: Testing F. Baseline: what-if add-back costed with LIVE-L.
  - Controls: same-account-day random cut of equal size, and a constant cut on fire days.
  - Duration: 11-30..12-11.
  - Success: worst-5 improves ≥ 40% and total R ≥ the same-day random cut; per-setup better/worse counts reported.
- **Reviewer status:** shorts reviewer "tail insurance only; add a same-day control". Added.

## 5. B8-SHADOW: net-beta cap as a journal tag (existing card)
- **Evidence:** [squeeze_1125](../research/squeeze_1125/REPORT.md): on top of LATCH-OPEN, worst-5 +47% on CHECK / +22% on T2; fires about 185 of 252 days; live today's trio −26.6R.
- **Expected:** 0 (log). **Risk:** code path only.
- **Experiment:**
  - Accounts: Primary, On Deck, Testing A. 20 Primary sessions.
  - Enforce only if it beats both a size-matched random block and a constant cut on CHECK and T2, plus the forward tags.
- **Reviewer status:** card reviewed (inspector_1127 #7, #8).

## 6. TAGS2: freeze 7 would-skip rules now, score once after 20 sessions (new)
- **Rules:**
  - BASKET5X ([loss_anatomy](findings/loss_anatomy.md) P1, re-scoped by its reviewer to excess over a day-block random cut).
  - GAPU_GD25 / GAPU_GD50 ([shorts_autopsy](findings/shorts_autopsy.md) P1, [loss_anatomy](findings/loss_anatomy.md) P2).
  - PLOCK25 ([outside](findings/outside.md) P1, with the reviewer's first-N path control).
  - SIDE20 / BS30 ([regime_filters](findings/regime_filters.md) P1, with TT dropped and same-day neutral).
  - LONGF1 ([long_edge](findings/long_edge.md) P2, tested against F5).
- **Expected:** 0 now. In-sample hints were +10 R/wk (GAPU on the current roster, `1 day`) down to about 0. Prior chance any rule passes: about 10-20%. Cycle 2: the GAPU switch failed a random day-skip control on the bench (0/5, [gapswitch](findings/gapswitch.md)), so GAPU's prior is lower.
- **Risk:** none (offline). The multiplicity count rises by 7.
- **Experiment:**
  - Accounts: all journals, read-only. Baseline: untagged lots plus each rule's control.
  - Duration: 11-30..12-29. Success: day-clustered t ≥ 2 and above the control's p95.
  - A pass only earns a pre-registered bench test.
- **Prepared:** [rules_draft.json](sandbox/decisions/TAGS2/rules_draft.json).

## 7. PAIRED-CARD scoreboard (new)
- **Evidence:** [dev_tactics](findings/dev_tactics.md) E5: paired tests need about 3x fewer sessions than split-account A/Bs; reviewer fix: skip rules scored same-day/same-side on net R.
- **Expected:** 0 direct; +0 to +1.5 R/wk per card that is real, adopted 3-6 weeks sooner.
- **Experiment:** cards LATCH-OPEN, RW 1.25x target (descriptive only: it failed the cycle-2 LIVE-L re-check, [rw_target](findings/rw_target.md)), L3 first-lot-only, SPREADFLOOR. 10 sessions, one report on 12-11.
  - Success: paired day t ≥ 2 in the bench direction, sign holds without the best day, ≥ 60% of affected setups improve, within 2 SE of the bench.
- **Prepared:** [PLAN.md](sandbox/decisions/PAIRED-CARD/PLAN.md).

## 8. FROZEN-BLOCKS and GY-SHADOW + TWIN (structure, new)
- **Evidence:** [dev_tactics](findings/dev_tactics.md) E2/E4/E9: 23 rule-change dates in 25 sessions; records 3-12% signal; promotions +0.190 → −0.197.
- **Expected:** 0 direct; 0 to +3 R/wk after 4-6 weeks through faster, cleaner verdicts.
- **Risk:** organisational (owner rules on copies and the Graveyard; FROZEN-BLOCKS amends the 11-20 "no freeze" rule and must exempt the playing-time session rotation); shadow bias −0.047R must be corrected; some execution-cost data lost if Graveyard orders stop (keep 1-2 live).
- **Experiment:** blocks from 11-30 (process only). Twin from 12-07: one candidate change per block. Success: at least one paired verdict per block at t ≥ 2 or a decisive null.
- **Prepared:** [RULE_DRAFT.md](sandbox/decisions/FROZEN-BLOCKS/RULE_DRAFT.md), [OUTLINE.md](sandbox/decisions/GY-SHADOW-TWIN/OUTLINE.md).

## 9. LONG-SURVIVORS scoreboard (new)
- **Evidence:** [long_edge](findings/long_edge.md) §3. Of 44 long setups with ≥ 50 lots, only GEN-261020-09 (+3.4R w/o best day, day t 0.96) and CWT14-orl-p10-long-WB5 (+2.7R, day t 1.15) stay positive without their best day.
- **Experiment:** 11-30..12-28 on their own lots, within-day random long control (2,000 draws).
  - Success: w/o-best-day > +0.05R per lot, best-day share < 35%, day t ≥ 2, above the random p95, ≥ 11 of 20 sessions traded.
- **Expected:** 0 on Primary. If one passes, it is the first long with a non-one-day record, and only then would a Primary card be written.

## 10. Stage-1 weekly scorecard and review rules (new)
- **Evidence:** [metrics](findings/metrics.md) §4 (green-day arithmetic, reproduced exactly), P1/P3; [outside](findings/outside.md) P2/P3.
- **What:** worst day ≥ −20R, 20-session floor ≥ −40R, median day > −2R, R per lot with day t. Red days and green weeks are reported but not judged while R per lot ≤ 0.
- **Review rules:** exposure-matched cut beside every red-day lever; no gating on a setup's own last 5-10 sessions; minimum size until day t ≥ 2 over 20 sessions.
- **Expected:** 0 R; prevents adopting disguised size cuts and promoting on noise.

## 11. HS-SCALE shock-only (existing card)
- SHOCK-V with 16R / 24R floors: no new entries plus an alert on a sharp 2-10 minute drop. It never flattens.
- On 118 account-days it caught Gen 11-17 and Live Lab 11-20, with 2 false fires.
- 0 R effect. Apply at 12-04; no override needed.

Educational only — not financial advice.
